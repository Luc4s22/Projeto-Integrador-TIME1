"""
PROTECAO CONTRA IDOR (Insecure Direct Object Reference).

O problema: as rotas recebem o ID do recurso na URL (/shipments/13). Se o servidor
so confere "o usuario esta logado e tem o papel certo?", qualquer usuario troca o
13 por outro numero e mexe no que e de outra pessoa.

A regra deste arquivo: TODA consulta de viagem, placa, leitura, alerta e item
passa por um filtro de DONO, feito no servidor com o usuario do token -- nunca
com um ID que o cliente manda. Quem nao e dono recebe 404, como se o recurso nao
existisse (403 confirmaria que o ID existe).

Quem e dono:
    - viagem: o vendedor que criou (created_by), o comprador (buyer), o motorista
      (driver) e o dono da placa usada nela (device.owner);
    - placa: so o dono (owner);
    - local e veiculo: quem cadastrou (owner); os SEM dono sao cadastros
      compartilhados da plataforma (todos veem e usam, so a plataforma altera);
      e tambem os que aparecem nas viagens que o usuario ja ve (ex.: o comprador
      ve a fazenda de origem da compra dele, mas nao altera);
    - leituras, impactos, alertas e itens: seguem a viagem a que pertencem;
    - plataforma (superusuario ou grupo Administrador): ve tudo.
"""

import logging

from django.conf import settings
from django.db.models import Q
from django.http import Http404

logger = logging.getLogger('seguranca')


def eh_plataforma(usuario):
    """Superusuario ou grupo Administrador: a equipe que mantem o sistema."""
    return bool(
        usuario.is_authenticated
        and (usuario.is_superuser or usuario.groups.filter(name='Administrador').exists())
    )


def filtro_viagens(usuario, prefixo=''):
    """
    Condicao (Q) "a viagem e deste usuario".

    `prefixo` permite usar a mesma regra a partir de outro model:
    leituras e alertas usam prefixo='shipment__' (viagem da leitura/alerta).
    """
    return (
        Q(**{f'{prefixo}created_by': usuario})
        | Q(**{f'{prefixo}buyer': usuario})
        | Q(**{f'{prefixo}driver': usuario})
        | Q(**{f'{prefixo}device__owner': usuario})
    )


def viagens_visiveis(usuario, queryset):
    if eh_plataforma(usuario):
        return queryset
    return queryset.filter(filtro_viagens(usuario)).distinct()


def placas_visiveis(usuario, queryset):
    if eh_plataforma(usuario):
        return queryset
    return queryset.filter(owner=usuario)


def locais_visiveis(usuario, queryset):
    """Locais (fazendas, CDs): os proprios, os compartilhados e os das viagens que ele ve."""
    if eh_plataforma(usuario):
        return queryset
    return queryset.filter(
        Q(owner=usuario) | Q(owner__isnull=True)
        | filtro_viagens(usuario, prefixo='shipments_from__')
        | filtro_viagens(usuario, prefixo='shipments_to__')
    ).distinct()


def veiculos_visiveis(usuario, queryset):
    """Veiculos: os proprios, os compartilhados e os das viagens que ele ve."""
    if eh_plataforma(usuario):
        return queryset
    return queryset.filter(
        Q(owner=usuario) | Q(owner__isnull=True) | filtro_viagens(usuario, prefixo='shipments__')
    ).distinct()


def pode_alterar_cadastro(usuario, objeto):
    """
    Ver nao e poder alterar: so o dono (ou a plataforma) altera um local ou veiculo.
    Cadastro compartilhado (sem dono) so a plataforma altera.
    """
    return eh_plataforma(usuario) or (objeto.owner_id is not None and objeto.owner_id == usuario.id)


def pela_viagem_visivel(usuario, queryset):
    """Para models ligados a uma viagem (leitura, impacto, alerta, item)."""
    if eh_plataforma(usuario):
        return queryset
    return queryset.filter(filtro_viagens(usuario, prefixo='shipment__')).distinct()


def registrar_bloqueio(request, recurso, identificador, motivo='nao e dono'):
    """
    Log de seguranca com o CODIGO DE MISSAO da equipe (exigencia do trabalho).
    Aparece nos logs do Render: quem tentou, o que, de onde.
    """
    logger.warning(
        '[%s] IDOR bloqueado: usuario=%s recurso=%s id=%s rota=%s %s ip=%s motivo=%s',
        settings.SECURITY_MISSION_CODE,
        getattr(request.user, 'email', '') or getattr(request.user, 'username', '?'),
        recurso, identificador, request.method, request.path,
        request.META.get('REMOTE_ADDR', '?'), motivo,
    )


class ProtecaoDonoMixin:
    """
    Mixin para os ViewSets: aplica o filtro de dono e registra as tentativas.

    Como funciona no DRF: TODA rota de detalhe e TODA acao (@action detail=True)
    chama self.get_object(), que procura o ID dentro de self.get_queryset().
    Filtrando o get_queryset pelo dono, o ID de outro usuario simplesmente
    "nao existe" para quem pede -> Http404. Um lugar so protege todas as rotas.

    Cada ViewSet diz como filtrar em `filtrar_por_dono`.
    """

    def filtrar_por_dono(self, usuario, queryset):  # sobrescrito em cada ViewSet
        raise NotImplementedError

    def get_queryset(self):
        return self.filtrar_por_dono(self.request.user, super().get_queryset())

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            # O 404 pode ser "nao existe" ou "existe, mas nao e seu".
            # So o segundo caso e tentativa de IDOR: esse vai para o log.
            chave = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)
            modelo = self.queryset.model
            if str(chave).isdigit() and modelo.objects.filter(pk=chave).exists():
                registrar_bloqueio(self.request, modelo._meta.model_name, chave)
            raise
