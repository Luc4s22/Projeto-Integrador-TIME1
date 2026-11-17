
from django.urls import re_path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    MeView,
    LogoutView,
    PasswordResetView,
    PasswordResetConfirmView,
    SetupView,
    ActivateView,
    VerifyView,
    RecoveryCodesView,
)

# As rotas aceitam com ou sem barra no final.

urlpatterns = [

    # LOGIN
    # Recebe email e senha.
    # Devolve access, refresh e user.
    re_path(
        r'^login/?$',
        LoginView.as_view(),
        name='auth-login'
    ),

    # SEGUNDO FATOR (2FA com TOTP)
    # setup: primeiro acesso, devolve o QR Code.
    # activate: confirma o cadastro, devolve tokens + codigos de recuperacao.
    # verify: acessos seguintes, codigo do app (ou de recuperacao) -> tokens.
    re_path(r'^2fa/setup/?$', SetupView.as_view(), name='auth-2fa-setup'),
    re_path(r'^2fa/activate/?$', ActivateView.as_view(), name='auth-2fa-activate'),
    re_path(r'^2fa/verify/?$', VerifyView.as_view(), name='auth-2fa-verify'),
    re_path(r'^2fa/recovery-codes/?$', RecoveryCodesView.as_view(), name='auth-2fa-recovery-codes'),

    # RENOVAR TOKEN
    # Recebe refresh e devolve novo access.
    re_path(
        r'^refresh/?$',
        TokenRefreshView.as_view(),
        name='auth-refresh'
    ),

    # DADOS DO USUÁRIO AUTENTICADO
    re_path(
        r'^me/?$',
        MeView.as_view(),
        name='auth-me'
    ),

    # LOGOUT
    # Invalida o refresh token.
    re_path(
        r'^logout/?$',
        LogoutView.as_view(),
        name='auth-logout'
    ),

    # SOLICITAR RECUPERAÇÃO DE SENHA
    # Recebe o e-mail do usuário.
    re_path(
        r'^password-reset/?$',
        PasswordResetView.as_view(),
        name='auth-password-reset'
    ),

    # CONFIRMAR NOVA SENHA
    # Recebe uid, token e nova senha.
    re_path(
        r'^password-reset/confirm/?$',
        PasswordResetConfirmView.as_view(),
        name='auth-password-reset-confirm'
    ),
]
