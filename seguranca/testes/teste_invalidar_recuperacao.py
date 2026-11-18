"""
Alteracao ao vivo: "invalide os codigos de recuperacao de um usuario".

1. O usuario A gera codigos de recuperacao novos (mostrados na tela).
2. O script PAUSA: no outro terminal, rode o comando de invalidar.
3. O script tenta entrar com um dos codigos: deve ser RECUSADO.

Uso (PowerShell, na raiz do projeto, com as mesmas variaveis dos outros testes):
    python seguranca/testes/teste_invalidar_recuperacao.py
    (quando pausar, em outro terminal:)
    python manage.py invalidar_codigos_recuperacao vendedor-a@teste.local
"""

from comum import (
    USUARIO_A, cabecalho, chamar, codigo_novo, dados, exigir_senha, login_so_com_senha, token_de,
)


def main():
    exigir_senha()
    cabecalho('Teste OTP - invalidar os codigos de recuperacao do usuario A')

    acesso = token_de(USUARIO_A)
    gerados = chamar('POST', '/auth/2fa/recovery-codes', acesso, json={'code': codigo_novo(USUARIO_A)})
    codigos = dados(gerados).get('recovery_codes')
    if not codigos:
        raise SystemExit(f'Nao gerou codigos: {gerados.status_code} {gerados.text[:200]}')
    print(f'Codigos de recuperacao novos do A: {", ".join(codigos[:3])} ... ({len(codigos)} no total)')

    input('\nAgora, em OUTRO terminal, rode:\n'
          f'    python manage.py invalidar_codigos_recuperacao {USUARIO_A}\n'
          'e depois aperte Enter aqui... ')

    token = dados(login_so_com_senha(USUARIO_A))['mfa_token']
    resposta = chamar('POST', '/auth/2fa/verify', json={'mfa_token': token, 'recovery_code': codigos[0]})
    print(f'\nEntrar com o codigo {codigos[0]} -> {resposta.status_code} {resposta.json().get("detail", "")}')
    print('-' * 72)
    if resposta.status_code == 400:
        print('RESULTADO: PROTEGIDO - os codigos invalidados nao entram mais.')
    else:
        print('RESULTADO: FALHOU - o codigo ainda funcionou (o comando foi rodado no MESMO banco da API?).')


if __name__ == '__main__':
    main()
