"""
Link de "definir senha" e envio de e-mail (Resend).

Usado em dois lugares:
- recuperacao de senha (o proprio usuario pede: /auth/password-reset);
- convite de usuario novo (a plataforma cria a conta: POST /auth/users).

No convite, NINGUEM escolhe a senha da pessoa: ela recebe um link de uso
unico (token do Django, vale PASSWORD_RESET_TIMEOUT, padrao 3 dias) e define
a propria senha na mesma tela da recuperacao de senha do front.
"""

import json
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)


def link_definir_senha(usuario):
    """Link do front com uid e token de uso unico. None se PASSWORD_RESET_URL nao estiver configurada."""
    base_url = settings.PASSWORD_RESET_URL
    if not base_url:
        return None
    parametros = urlencode({
        'uid': urlsafe_base64_encode(force_bytes(usuario.pk)),
        'token': default_token_generator.make_token(usuario),
    })
    return f'{base_url}{"&" if "?" in base_url else "?"}{parametros}'


def enviar_email(destino, assunto, texto):
    """Envia pelo Resend. Devolve True se enviou; False se nao esta configurado ou falhou."""
    if not (settings.RESEND_API_KEY and settings.RESEND_FROM_EMAIL):
        logger.error('Envio de e-mail nao configurado (RESEND_API_KEY / RESEND_FROM_EMAIL).')
        return False
    requisicao = Request(
        'https://api.resend.com/emails',
        data=json.dumps({
            'from': settings.RESEND_FROM_EMAIL, 'to': [destino], 'subject': assunto, 'text': texto,
        }).encode('utf-8'),
        headers={'Authorization': f'Bearer {settings.RESEND_API_KEY}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(requisicao, timeout=10):
            return True
    except Exception:
        logger.exception('Falha no envio de e-mail.')
        return False


def enviar_recuperacao(usuario):
    link = link_definir_senha(usuario)
    if link is None:
        logger.error('Recuperacao de senha nao configurada (PASSWORD_RESET_URL).')
        return False
    return enviar_email(
        usuario.email, 'Recuperação de senha',
        'Recebemos uma solicitação para redefinir sua senha.\n\n'
        f'Acesse: {link}\n\nSe não foi você, ignore esta mensagem.',
    )


def enviar_convite(usuario):
    """
    Manda o convite. Devolve (enviado, link):
    - enviado=True: o e-mail saiu; o link NAO volta na resposta da API;
    - enviado=False: o e-mail nao esta configurado ou falhou; o link volta para
      a plataforma entregar a pessoa por outro canal (ou None, sem PASSWORD_RESET_URL).
    """
    link = link_definir_senha(usuario)
    if link is None:
        return False, None
    enviado = enviar_email(
        usuario.email, 'Seu acesso ao Caminho do Vale',
        f'Olá, {usuario.get_full_name() or usuario.email}!\n\n'
        'Uma conta foi criada para você no Caminho do Vale.\n'
        f'Defina sua senha por este link (uso único): {link}\n\n'
        'No primeiro acesso, você também vai configurar o aplicativo autenticador (2FA).',
    )
    return enviado, (None if enviado else link)
