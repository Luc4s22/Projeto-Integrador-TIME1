"""
Teste da autenticacao em dois fatores (OTP) no login.

ANTES do controle: o login so com e-mail e senha ja entrega o token de acesso,
e com ele a pessoa usa a API inteira. Quem descobrir a senha (vazamento,
senha repetida em outro site, phishing) entra na conta.

DEPOIS do controle (este arquivo ganha os outros casos quando o 2FA existir):
    - senha certa e sem codigo   -> recusado
    - codigo errado ou vencido   -> recusado
    - codigo valido              -> aceito
    - codigo ja usado            -> recusado
    - codigo de recuperacao      -> funciona uma vez so

Uso (PowerShell, na raiz do projeto):
    $env:TESTE_SENHA = "..."; $env:MISSAO = "XXXXXX"
    python seguranca/testes/teste_otp.py
"""

from comum import USUARIO_A, cabecalho, chamar, exigir_senha, login_so_com_senha


def main():
    exigir_senha()
    cabecalho('Teste OTP - login so com e-mail e senha, sem segundo fator')

    resposta = login_so_com_senha(USUARIO_A)
    dados = resposta.json().get('data', {}) if resposta.headers.get('content-type', '').startswith('application/json') else {}
    print(f'POST /auth/login (so senha) -> {resposta.status_code}')

    if resposta.status_code == 200 and 'access' in dados:
        print('O servidor devolveu o token de acesso sem pedir codigo do autenticador.')
        me = chamar('GET', '/auth/me', dados['access'])
        print(f'GET /auth/me com esse token -> {me.status_code} (usuario: {me.json()["data"].get("email")})')
        print('\n' + '-' * 72)
        print('RESULTADO: VULNERAVEL - senha correta basta para entrar na conta.')
    else:
        print('O servidor NAO entregou o token so com a senha.')
        print('\n' + '-' * 72)
        print('RESULTADO: login pede segundo fator (use a versao "depois" deste teste).')


if __name__ == '__main__':
    main()
