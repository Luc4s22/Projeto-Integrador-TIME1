"""
Teste da autenticacao em dois fatores (OTP) no login.

ANTES do controle: o login so com e-mail e senha ja entrega o token de acesso.

DEPOIS do controle, o teste prova os 5 itens do trabalho:
    1. senha certa e sem codigo   -> nao recebe token
    2. codigo errado              -> recusado
    3. codigo valido              -> aceito (recebe token)
    4. o mesmo codigo de novo     -> recusado
    5. codigo de recuperacao      -> funciona uma vez so
    (+ tentativa de contorno: recadastrar o autenticador so com a senha)

Uso (PowerShell, na raiz do projeto):
    $env:TESTE_SENHA = "..."; $env:TESTE_TOTP_SEGREDO = "..."; $env:MISSAO = "XXXXXX"
    python manage.py preparar_teste_seguranca
    python seguranca/testes/teste_otp.py
"""

from comum import (
    USUARIO_A, cabecalho, chamar, codigo_novo, dados, exigir_senha, login_so_com_senha, verificar_codigo,
)


def linha(numero, descricao, resposta, esperado):
    ok = resposta.status_code == esperado
    print(f'{numero}. {descricao:<44} -> {resposta.status_code} {"OK" if ok else "FALHOU (esperado " + str(esperado) + ")"}')
    return ok


def main():
    exigir_senha()
    cabecalho('Teste OTP - autenticacao em dois fatores no login')

    resposta = login_so_com_senha(USUARIO_A)
    corpo = dados(resposta)
    print(f'POST /auth/login (so senha) -> {resposta.status_code}')

    if 'access' in corpo:
        me = chamar('GET', '/auth/me', corpo['access'])
        print('O servidor devolveu o token de acesso sem pedir codigo do autenticador.')
        print(f'GET /auth/me com esse token -> {me.status_code} (usuario: {dados(me).get("email")})')
        print('\n' + '-' * 72)
        print('RESULTADO: VULNERAVEL - senha correta basta para entrar na conta.')
        return

    resultados = []
    print('1. Senha certa e sem codigo: o login NAO devolveu token de acesso -> OK')
    resultados.append('access' not in corpo)
    token = corpo['mfa_token']

    def verificar(**campos):
        return chamar('POST', '/auth/2fa/verify', json={'mfa_token': token, **campos})

    resultados.append(linha(2, 'codigo errado (000000)', verificar(code='000000'), 400))

    codigo, valido = verificar_codigo(USUARIO_A, token)
    resultados.append(linha(3, f'codigo valido ({codigo})', valido, 200))
    resultados.append(linha(4, f'o mesmo codigo de novo ({codigo})', verificar(code=codigo), 400))

    # Codigos de recuperacao novos (pede um codigo atual do autenticador).
    acesso = dados(valido).get('access')
    gerados = chamar('POST', '/auth/2fa/recovery-codes', acesso, json={'code': codigo_novo(USUARIO_A)})
    recuperacao = dados(gerados).get('recovery_codes', ['SEM-CODIGO'])[0]
    resultados.append(linha('5a', f'codigo de recuperacao ({recuperacao})', verificar(recovery_code=recuperacao), 200))
    resultados.append(linha('5b', 'o mesmo codigo de recuperacao de novo', verificar(recovery_code=recuperacao), 400))

    contorno = chamar('POST', '/auth/2fa/setup', json={'mfa_token': token})
    resultados.append(linha('C', 'contorno: recadastrar autenticador so c/ senha', contorno, 400))

    print('\n' + '-' * 72)
    if all(resultados):
        print('RESULTADO: PROTEGIDO - a senha sozinha nao entra; codigos errados, reusados e')
        print('           de recuperacao ja usados sao recusados.')
    else:
        print('RESULTADO: FALHOU - algum item acima nao se comportou como esperado.')


if __name__ == '__main__':
    main()
