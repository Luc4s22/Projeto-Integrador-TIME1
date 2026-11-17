"""
Funcoes usadas pelos dois testes de seguranca (IDOR e OTP).

Tudo vem de variaveis de ambiente, nada de senha no codigo:

    API_URL             endereco da API (padrao: a API publicada no Render)
    TESTE_SENHA         senha dos usuarios de teste (a mesma do preparar_teste_seguranca)
    TESTE_TOTP_SEGREDO  segredo do autenticador dos usuarios de teste (depois do 2FA)
    MISSAO              codigo de missao da equipe (aparece no cabecalho da saida)
"""

import os
import sys
import time
from datetime import datetime

import requests

API_URL = os.environ.get('API_URL', 'https://projeto-integrador-time1.onrender.com/api/v1').rstrip('/')
SENHA = os.environ.get('TESTE_SENHA', '')
SEGREDO_TOTP = os.environ.get('TESTE_TOTP_SEGREDO', '').strip().upper()
MISSAO = os.environ.get('MISSAO', 'SEM-CODIGO')

USUARIO_A = 'vendedor-a@teste.local'
USUARIO_B = 'vendedor-b@teste.local'

TEMPO_LIMITE = 90  # o Render gratuito pode levar ~1 min para acordar
PASSO_S = 30       # cada codigo TOTP vale 30 s

_ultimo_passo_usado = {}  # por usuario: o servidor recusa codigo do mesmo intervalo


def cabecalho(titulo):
    print('=' * 72)
    print(f'[{MISSAO}] {titulo}')
    print(f'API: {API_URL}')
    print(f'Data: {datetime.now():%d/%m/%Y %H:%M:%S}')
    print('=' * 72)


def exigir_senha():
    if not SENHA:
        sys.exit('Defina a variavel TESTE_SENHA antes de rodar o teste.')


def chamar(metodo, rota, token=None, **opcoes):
    """Faz a requisicao e devolve a resposta (sem levantar erro em 4xx/5xx)."""
    cabecalhos = opcoes.pop('headers', {})
    if token:
        cabecalhos['Authorization'] = f'Bearer {token}'
    return requests.request(metodo, API_URL + rota, headers=cabecalhos, timeout=TEMPO_LIMITE, **opcoes)


def dados(resposta):
    try:
        return resposta.json().get('data', resposta.json())
    except ValueError:
        return {}


def login_so_com_senha(email):
    """POST /auth/login. Devolve a resposta inteira (o teste de OTP olha o que veio nela)."""
    return chamar('POST', '/auth/login', json={'email': email, 'password': SENHA})


def codigo_novo(email):
    """
    Codigo TOTP de um intervalo de 30 s que este usuario ainda NAO usou.
    Se o atual ja foi usado, espera o proximo (o servidor recusa reuso).
    """
    import pyotp

    if not SEGREDO_TOTP:
        sys.exit('O login pede o codigo do 2FA: defina TESTE_TOTP_SEGREDO (o mesmo do preparar_teste_seguranca).')
    passo = int(time.time()) // PASSO_S
    if _ultimo_passo_usado.get(email, -1) >= passo:
        espera = PASSO_S - int(time.time()) % PASSO_S + 1
        print(f'(aguardando {espera} s pelo proximo codigo do autenticador)')
        time.sleep(espera)
        passo = int(time.time()) // PASSO_S
    _ultimo_passo_usado[email] = passo
    return pyotp.TOTP(SEGREDO_TOTP).at(passo * PASSO_S)


def aguardar_proximo_codigo(email):
    """Marca o intervalo atual como usado e espera o proximo."""
    _ultimo_passo_usado[email] = int(time.time()) // PASSO_S


def verificar_codigo(email, mfa_token):
    """
    POST /auth/2fa/verify com um codigo novo. Se o servidor disser que o codigo
    deste intervalo ja foi usado (por outro teste rodado logo antes), espera o
    proximo intervalo e tenta uma vez mais. Devolve (codigo usado, resposta).
    """
    codigo = codigo_novo(email)
    resposta = chamar('POST', '/auth/2fa/verify', json={'mfa_token': mfa_token, 'code': codigo})
    if resposta.status_code == 400 and 'utilizado' in resposta.text:
        aguardar_proximo_codigo(email)
        codigo = codigo_novo(email)
        resposta = chamar('POST', '/auth/2fa/verify', json={'mfa_token': mfa_token, 'code': codigo})
    return codigo, resposta


def token_de(email):
    """
    Entra e devolve o token de acesso.

    Antes do 2FA: o login com senha ja devolve o token.
    Depois do 2FA: login devolve so o mfa_token; o token vem do /auth/2fa/verify.
    """
    resposta = login_so_com_senha(email)
    if resposta.status_code != 200:
        sys.exit(f'Login de {email} falhou: {resposta.status_code} {resposta.text[:200]}')
    corpo = dados(resposta)
    if 'access' in corpo:
        return corpo['access']
    _, verificado = verificar_codigo(email, corpo['mfa_token'])
    if verificado.status_code != 200:
        sys.exit(f'2FA de {email} falhou: {verificado.status_code} {verificado.text[:200]}')
    return dados(verificado)['access']


def resultado(descricao, resposta, esperado_protegido=True):
    """
    Imprime uma linha do relatorio.

    VULNERAVEL = o servidor deixou (2xx) quando nao deveria.
    PROTEGIDO  = o servidor recusou (403 ou 404).
    """
    codigo = resposta.status_code
    if 200 <= codigo < 300:
        situacao = 'VULNERAVEL' if esperado_protegido else 'OK (dono usa normalmente)'
    elif codigo in (403, 404):
        situacao = 'PROTEGIDO' if esperado_protegido else 'ERRO: o dono foi bloqueado'
    else:
        situacao = 'OUTRO'
    print(f'{codigo:>4}  {situacao:<26} {descricao}')
    return situacao
