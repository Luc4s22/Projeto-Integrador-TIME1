"""
Alteracao ao vivo: "mude a janela de validade do codigo OTP".

Envia, para o usuario A, o codigo do intervalo de 30 s ANTERIOR (um codigo que
acabou de vencer) e mostra se o servidor aceita:
    OTP_VALID_WINDOW=1 (padrao) -> ACEITO   (tolera ate 30 s de atraso do relogio)
    OTP_VALID_WINDOW=0          -> RECUSADO (so vale o codigo do intervalo atual)

A janela e lida pelo SERVIDOR (piADS04/settings.py). Para a demonstracao,
rode a API local e mude o .env:
    1. no .env:  OTP_VALID_WINDOW=0      2. reinicie o runserver
    3. $env:API_URL = "http://127.0.0.1:8000/api/v1"
    4. python seguranca/testes/teste_janela_otp.py
"""

import time

import pyotp

from comum import (
    PASSO_S, SEGREDO_TOTP, USUARIO_A, cabecalho, chamar, dados, exigir_senha, login_so_com_senha,
)


def enviar_codigo_anterior():
    corpo = dados(login_so_com_senha(USUARIO_A))
    if 'mfa_token' not in corpo:
        raise SystemExit(f'Login do A falhou: {corpo}')
    passo_anterior = int(time.time()) // PASSO_S - 1
    codigo = pyotp.TOTP(SEGREDO_TOTP).at(passo_anterior * PASSO_S)
    return codigo, chamar('POST', '/auth/2fa/verify', json={'mfa_token': corpo['mfa_token'], 'code': codigo})


def main():
    exigir_senha()
    if not SEGREDO_TOTP:
        raise SystemExit('Defina TESTE_TOTP_SEGREDO (o mesmo do preparar_teste_seguranca).')
    cabecalho('Teste OTP - codigo do intervalo anterior (janela de validade)')

    codigo, resposta = enviar_codigo_anterior()
    for _ in range(2):
        if not (resposta.status_code == 400 and 'utilizado' in resposta.text):
            break
        # Outro teste acabou de usar um codigo deste usuario: espera o proximo intervalo.
        espera = PASSO_S - int(time.time()) % PASSO_S + 1
        print(f'(codigo recente ja usado por outro teste; aguardando {espera} s)')
        time.sleep(espera)
        codigo, resposta = enviar_codigo_anterior()

    print(f'Codigo de 30 s atras ({codigo}) -> {resposta.status_code}')
    print('\n' + '-' * 72)
    if resposta.status_code == 200:
        print('RESULTADO: ACEITO - o servidor tolera 1 intervalo de atraso (OTP_VALID_WINDOW >= 1).')
    else:
        print(f'RESULTADO: RECUSADO - so vale o codigo do intervalo atual (OTP_VALID_WINDOW = 0). '
              f'Mensagem: {resposta.json().get("detail")}')


if __name__ == '__main__':
    main()
