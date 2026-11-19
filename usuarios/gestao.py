"""
GESTAO DE USUARIOS PELA PLATAFORMA (tela "Usuarios" do front, sem o /admin).

Rotas (todas so para a plataforma: superusuario ou grupo Administrador):
    GET   /auth/users                    lista completa (sem ?role=)
    POST  /auth/users                    cria e manda o convite
    PATCH /auth/users/{id}               muda nome, papel ou ativo
    POST  /auth/users/{id}/invite        manda o convite de novo
    POST  /auth/users/{id}/reset-2fa     apaga o 2FA (celular perdido)

Decisoes de seguranca:
- ninguem define a senha de outra pessoa: a conta nasce SEM senha utilizavel e a
  pessoa recebe um link de uso unico para definir a dela;
- o papel vira o grupo certo (Vendedor, Comprador, Motorista, Administrador);
- a plataforma nao desativa nem rebaixa a si mesma (para nao ficar sem acesso),
  e so um superusuario mexe em outro superusuario;
- toda acao vai para o log de seguranca com o codigo de missao.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .acesso import eh_plataforma
from .convite import enviar_convite
from .models import CodigoRecuperacao, SegundoFator
from .serializers import role_do_usuario

logger = logging.getLogger('seguranca')
User = get_user_model()

# Papel que a tela envia -> grupo do Django.
GRUPO_POR_PAPEL = {
    'seller': 'Vendedor',
    'buyer': 'Comprador',
    'driver': 'Motorista',
    'admin': 'Administrador',
}


class SoPlataforma(BasePermission):
    message = 'Apenas a administração da plataforma pode gerenciar usuários.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and eh_plataforma(request.user))


def registrar(request, acao, alvo):
    logger.warning(
        '[%s] Gestao de usuarios: %s por=%s alvo=%s ip=%s',
        settings.SECURITY_MISSION_CODE, acao,
        getattr(request.user, 'email', '') or request.user.username,
        alvo.email or alvo.username, request.META.get('REMOTE_ADDR', '?'),
    )


def separar_nome(nome):
    partes = nome.strip().split(maxsplit=1)
    return (partes[0] if partes else ''), (partes[1] if len(partes) > 1 else '')


def definir_papel(usuario, papel):
    usuario.groups.set([Group.objects.get(name=GRUPO_POR_PAPEL[papel])])


# --- Serializers --------------------------------------------------------------

class UsuarioGestaoSerializer(serializers.Serializer):
    """O que a tela de usuarios mostra (so a plataforma ve)."""

    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    role = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()
    has_password = serializers.SerializerMethodField()
    has_2fa = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField()
    date_joined = serializers.DateTimeField()

    def get_name(self, usuario) -> str:
        return usuario.get_full_name() or usuario.username

    def get_role(self, usuario) -> str | None:
        return role_do_usuario(usuario)

    def get_has_password(self, usuario) -> bool:
        """False = convite ainda nao aceito (a pessoa nao definiu a senha)."""
        return usuario.has_usable_password()

    def get_has_2fa(self, usuario) -> bool:
        return SegundoFator.objects.filter(usuario=usuario, ativo=True).exists()


class CriarUsuarioSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=list(GRUPO_POR_PAPEL))

    def validate_email(self, email):
        email = email.strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise serializers.ValidationError('Já existe um usuário com este e-mail.')
        return email


class AlterarUsuarioSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    role = serializers.ChoiceField(choices=list(GRUPO_POR_PAPEL), required=False)
    is_active = serializers.BooleanField(required=False)


# --- Acoes ----------------------------------------------------------------------

def listar_usuarios():
    return User.objects.prefetch_related('groups').order_by('first_name', 'last_name', 'username')


def criar_usuario(request):
    """POST /auth/users: cria a conta sem senha e manda o convite."""
    entrada = CriarUsuarioSerializer(data=request.data)
    entrada.is_valid(raise_exception=True)
    dados = entrada.validated_data
    if dados['role'] == 'admin' and not request.user.is_superuser:
        raise PermissionDenied('Só um superusuário cria outro administrador.')

    with transaction.atomic():
        primeiro, ultimo = separar_nome(dados['name'])
        usuario = User(username=dados['email'], email=dados['email'], first_name=primeiro, last_name=ultimo)
        usuario.set_unusable_password()  # a senha quem define e a propria pessoa, pelo link
        usuario.save()
        definir_papel(usuario, dados['role'])

    enviado, link = enviar_convite(usuario)
    registrar(request, f'criou ({dados["role"]})', usuario)
    resposta = {
        'user': UsuarioGestaoSerializer(usuario).data,
        'invite_sent': enviado,
        # So aparece quando o e-mail NAO saiu: a plataforma entrega o link por outro canal.
        'password_setup_link': link,
    }
    return Response(resposta, status=status.HTTP_201_CREATED)


def alvo_ou_erro(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.is_superuser and not request.user.is_superuser:
        raise PermissionDenied('Só um superusuário altera outro superusuário.')
    return usuario


class UsuarioDetalheView(APIView):
    """PATCH /auth/users/{id}: nome, papel e ativo."""

    permission_classes = [SoPlataforma]

    @extend_schema(request=AlterarUsuarioSerializer, responses=UsuarioGestaoSerializer)
    def patch(self, request, pk):
        usuario = alvo_ou_erro(request, pk)
        entrada = AlterarUsuarioSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data

        if usuario.pk == request.user.pk and (dados.get('is_active') is False or 'role' in dados):
            return Response(
                {'detail': 'Você não pode desativar nem trocar o papel da sua própria conta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if dados.get('role') == 'admin' and not request.user.is_superuser:
            raise PermissionDenied('Só um superusuário promove alguém a administrador.')

        with transaction.atomic():
            if 'name' in dados:
                usuario.first_name, usuario.last_name = separar_nome(dados['name'])
            if 'is_active' in dados:
                usuario.is_active = dados['is_active']
            usuario.save()
            if 'role' in dados:
                definir_papel(usuario, dados['role'])

        if dados.get('is_active') is False:
            # Desativar tambem derruba as sessoes abertas (refresh tokens).
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
            for token in OutstandingToken.objects.filter(user=usuario):
                BlacklistedToken.objects.get_or_create(token=token)

        registrar(request, f'alterou {sorted(dados)}', usuario)
        return Response(UsuarioGestaoSerializer(usuario).data)


class ReenviarConviteView(APIView):
    """POST /auth/users/{id}/invite: convite vencido (3 dias) ou e-mail perdido."""

    permission_classes = [SoPlataforma]

    @extend_schema(request=None)
    def post(self, request, pk):
        usuario = alvo_ou_erro(request, pk)
        if not usuario.is_active:
            return Response({'detail': 'Usuário desativado.'}, status=status.HTTP_400_BAD_REQUEST)
        enviado, link = enviar_convite(usuario)
        registrar(request, 'reenviou convite', usuario)
        return Response({'invite_sent': enviado, 'password_setup_link': link})


class Resetar2FAView(APIView):
    """POST /auth/users/{id}/reset-2fa: no proximo login a pessoa cadastra o autenticador de novo."""

    permission_classes = [SoPlataforma]

    @extend_schema(request=None)
    def post(self, request, pk):
        usuario = alvo_ou_erro(request, pk)
        SegundoFator.objects.filter(usuario=usuario).delete()
        CodigoRecuperacao.objects.filter(usuario=usuario).delete()
        registrar(request, 'resetou o 2FA', usuario)
        return Response({'detail': '2FA removido. No próximo login a pessoa configura o autenticador de novo.'})
