"""
Alteracao ao vivo: "crie um terceiro usuario e mostre que ele nao enxerga os
dispositivos dos outros".

O usuario C e novo: nao tem placa nem viagem. Ele lista placas e viagens (deve
vir vazio) e tenta abrir, pelo ID, a placa e a viagem do A e do B (deve dar 404).

Uso (PowerShell, na raiz do projeto, com as mesmas variaveis dos outros testes):
    python manage.py preparar_teste_seguranca --terceiro
    python seguranca/testes/teste_terceiro_usuario.py
"""

from comum import USUARIO_A, USUARIO_B, USUARIO_C, cabecalho, chamar, dados, exigir_senha, resultado, token_de


def itens(resposta):
    corpo = dados(resposta)
    return corpo if isinstance(corpo, list) else []


def main():
    exigir_senha()
    cabecalho('Teste IDOR - usuario novo (C) tentando ver placas e viagens dos outros')

    token_c = token_de(USUARIO_C)
    alvos = []
    for email in (USUARIO_A, USUARIO_B):
        token = token_de(email)
        for placa in itens(chamar('GET', '/devices', token)):
            alvos.append((email, 'placa', f'/devices/{placa["id"]}'))
        for viagem in itens(chamar('GET', '/shipments', token, params={'page_size': 5})):
            alvos.append((email, 'viagem', f'/shipments/{viagem["id"]}'))

    placas_c = itens(chamar('GET', '/devices', token_c))
    viagens_c = itens(chamar('GET', '/shipments', token_c))
    print(f'GET /devices   do C -> {len(placas_c)} placa(s)   (esperado: 0)')
    print(f'GET /shipments do C -> {len(viagens_c)} viagem(ns) (esperado: 0)\n')

    print('O C tenta abrir pelo ID o que e do A e do B:')
    situacoes = [
        resultado(f'{tipo} de {email.split("@")[0]:<11} GET {rota}', chamar('GET', rota, token_c))
        for email, tipo, rota in alvos
    ]

    print('\n' + '-' * 72)
    if not placas_c and not viagens_c and 'VULNERAVEL' not in situacoes:
        print(f'RESULTADO: PROTEGIDO - o C nao ve nada dos outros ({len(situacoes)} tentativas recusadas).')
    else:
        print('RESULTADO: VULNERAVEL - o C conseguiu ver algo que nao e dele.')


if __name__ == '__main__':
    main()
