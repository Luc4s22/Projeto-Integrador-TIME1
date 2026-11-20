from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# Nome do grupo no Django -> "role" que o front recebe (JSON 1 do plano).
# Cada usuario tem UM papel (a gestao de usuarios grava um grupo so). Se alguem
# ficar em mais de um grupo (pelo /admin), vale o primeiro desta ordem: o de mais poder.
ROLES = {
    'Administrador': 'admin',
    'Vendedor': 'seller',
    'Comprador': 'buyer',
    'Motorista': 'driver',
    'Operador': 'operator',
    'Visualizador': 'viewer',
}


def role_do_usuario(usuario):
    if usuario.is_superuser:
        return 'admin'
    grupos = set(usuario.groups.values_list('name', flat=True))
    return next((papel for grupo, papel in ROLES.items() if grupo in grupos), None)


def dados_basicos(usuario):
    return {
        'id': usuario.id,
        'name': usuario.get_full_name() or usuario.username,
        'email': usuario.email,
        'role': role_do_usuario(usuario),
    }


class LoginSerializer(serializers.Serializer):
    """Login por e-mail e senha. Devolve os tokens e o usuario (JSON 1 do plano)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, dados):
        erro = serializers.ValidationError('E-mail ou senha inválidos.', code='authorization')
        encontrados = list(User.objects.filter(email__iexact=dados['email'])[:2])
        if len(encontrados) != 1:
            raise erro  # nao existe, ou o e-mail esta repetido (nao da para saber qual conta)
        usuario = authenticate(username=encontrados[0].username, password=dados['password'])
        if usuario is None or not usuario.is_active:
            raise erro

        # Senha certa NAO entrega mais o token: so identifica o usuario.
        # Quem decide o que vem depois (cadastro ou codigo do 2FA) e a LoginView.
        return {'usuario': usuario}


def emitir_tokens(usuario):
    """Tokens JWT + dados do usuario. So e chamado DEPOIS do segundo fator."""
    # Grava o ultimo login: alem de mostrar na gestao de usuarios, isso invalida
    # o mfa_token usado nesta entrada (ele carrega o last_login de quando foi criado).
    update_last_login(None, usuario)
    refresh = RefreshToken.for_user(usuario)
    return {'access': str(refresh.access_token), 'refresh': str(refresh), 'user': dados_basicos(usuario)}


class MeSerializer(serializers.ModelSerializer):
    """Dados do usuario logado, para o front saber quem e e o que pode fazer."""

    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'username', 'role', 'is_superuser', 'groups', 'permissions']
        read_only_fields = fields

    def get_name(self, usuario) -> str:
        return usuario.get_full_name() or usuario.username

    def get_role(self, usuario) -> str | None:
        return role_do_usuario(usuario)

    def get_groups(self, usuario) -> list[str]:
        return sorted(usuario.groups.values_list('name', flat=True))

    def get_permissions(self, usuario) -> list[str]:
        # Ex.: ["iot.view_reading", "transporte.add_shipment"]
        return sorted(usuario.get_all_permissions())
