"""
Cria (ou atualiza) os grupos do sistema e as permissoes de cada um.

Uso:  python manage.py criar_grupos

Pode rodar quantas vezes quiser: o comando e idempotente (sempre deixa os
grupos exatamente como definido aqui). Usa so User/Group/Permission nativos.
"""

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

APPS_DO_PROJETO = ['dominio', 'iot', 'transporte', 'alertas']


def permissoes_do_projeto():
    """
    Permissoes dos models que EXISTEM hoje nos apps do projeto.

    O Django nao apaga as permissoes de um model removido ou renomeado (elas ficam
    "orfas" no banco). Filtrar pelos models atuais evita dar permissao a um model
    que nao existe mais.
    """
    tipos = [
        ContentType.objects.get_for_model(modelo)
        for modelo in apps.get_models()
        if modelo._meta.app_label in APPS_DO_PROJETO
    ]
    return Permission.objects.filter(content_type__in=tipos)

# Operador: cadastra/edita o que e do dia a dia; nao mexe em frutas, limites nem dispositivos.
# Os nomes sao os do model em minusculas (shipment, shipmentitem...): e assim que o
# Django batiza as permissoes (add_shipment, change_alert...).
OPERADOR_PODE_ADICIONAR_E_EDITAR = [
    'location', 'vehicle', 'shipment', 'shipmentitem',
]
OPERADOR_PODE_EDITAR = ['alert']  # reconhecer e resolver alertas


def permissoes_do_administrador():
    """Administrador: todas as permissoes de todos os models do projeto."""
    return permissoes_do_projeto()


def permissoes_do_operador():
    permissoes = permissoes_do_projeto()
    codenames = {p.codename for p in permissoes if p.codename.startswith('view_')}
    for modelo in OPERADOR_PODE_ADICIONAR_E_EDITAR:
        codenames |= {f'add_{modelo}', f'change_{modelo}'}
    for modelo in OPERADOR_PODE_EDITAR:
        codenames.add(f'change_{modelo}')
    return permissoes.filter(codename__in=codenames)


def _ver_tudo_mais(adicionar_e_editar=(), editar=(), adicionar=()):
    """Monta um grupo: ver (view_) tudo + as acoes listadas."""
    permissoes = permissoes_do_projeto()
    codenames = {p.codename for p in permissoes if p.codename.startswith('view_')}
    for modelo in adicionar_e_editar:
        codenames |= {f'add_{modelo}', f'change_{modelo}'}
    codenames |= {f'change_{modelo}' for modelo in editar}
    codenames |= {f'add_{modelo}' for modelo in adicionar}
    return permissoes.filter(codename__in=codenames)


# "Ver tudo" aqui e so a permissao de TIPO (pode ver viagens). QUAIS viagens cada um
# ve e decidido pela protecao contra IDOR (dono da viagem/placa), nas views.

def permissoes_do_vendedor():
    """Vendedor: monta a carga e a viagem; cadastra fazendas e veiculos; cuida da placa dele."""
    return _ver_tudo_mais(
        adicionar_e_editar=['shipment', 'shipmentitem', 'location', 'vehicle'],
        editar=['alert', 'device'],
    )


def permissoes_do_comprador():
    """Comprador: acompanha a compra e confirma o recebimento (avaliacao com fotos)."""
    return _ver_tudo_mais(
        adicionar_e_editar=['location'],
        editar=['alert'],
        adicionar=['finalinspection', 'inspectionphoto'],
    )


def permissoes_do_motorista():
    """Motorista: so ve e, para iniciar/finalizar, precisa de change_shipment."""
    return _ver_tudo_mais(editar=['shipment'])


def permissoes_do_visualizador():
    """Visualizador: so consulta (view_) tudo."""
    return permissoes_do_projeto().filter(codename__startswith='view_')


GRUPOS = {
    'Administrador': permissoes_do_administrador,
    'Vendedor': permissoes_do_vendedor,
    'Comprador': permissoes_do_comprador,
    'Motorista': permissoes_do_motorista,
    'Operador': permissoes_do_operador,
    'Visualizador': permissoes_do_visualizador,
}


class Command(BaseCommand):
    help = 'Cria os grupos (Administrador, Vendedor, Comprador, Motorista, Operador, Visualizador).'

    def handle(self, *args, **options):
        for nome, obter_permissoes in GRUPOS.items():
            grupo, criado = Group.objects.get_or_create(name=nome)
            permissoes = list(obter_permissoes())
            grupo.permissions.set(permissoes)  # "set" substitui: mantem o grupo sempre igual a este arquivo
            situacao = 'criado' if criado else 'atualizado'
            if options['verbosity'] > 0:
                self.stdout.write(self.style.SUCCESS(f'Grupo {nome} {situacao} com {len(permissoes)} permissoes.'))
