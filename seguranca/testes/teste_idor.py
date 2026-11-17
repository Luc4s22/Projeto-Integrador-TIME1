"""
Teste da protecao contra IDOR (acesso a recurso de outro usuario trocando o ID).

Cenario (dados sinteticos, criados por: python manage.py preparar_teste_seguranca):
    - o usuario B tem a placa TESTE-B e uma viagem em andamento com leituras;
    - o usuario A, logado com a conta DELE, tenta ler, alterar e comandar
      a placa e a viagem do B, so trocando o ID na URL.

Resultado esperado:
    ANTES do controle -> as tentativas do A passam (VULNERAVEL);
    DEPOIS            -> todas recebem 403/404 (PROTEGIDO) e o B continua usando.

Uso (PowerShell, na raiz do projeto):
    $env:TESTE_SENHA = "..."; $env:MISSAO = "XXXXXX"
    $env:TESTE_TOTP_SEGREDO = "..."   (depois do 2FA: o login dos usuarios de teste pede o codigo)
    python manage.py preparar_teste_seguranca
    python seguranca/testes/teste_idor.py
"""

from comum import (
    USUARIO_A, USUARIO_B, cabecalho, chamar, exigir_senha, resultado, token_de,
)


def recursos_do_b(token_b):
    """O B procura a PROPRIA viagem de teste (lote TESTE-IDOR-B) e a placa dela."""
    eu = chamar('GET', '/auth/me', token_b).json()['data']
    resposta = chamar('GET', '/shipments', token_b, params={'page_size': 200})
    for viagem in resposta.json()['data']:
        lotes = [item.get('lot') for item in viagem.get('items', [])]
        if viagem.get('created_by') == eu['id'] and 'TESTE-IDOR-B' in lotes:
            return viagem['id'], viagem['device']
    raise SystemExit('Viagem de teste do B nao encontrada. Rode: python manage.py preparar_teste_seguranca')


def main():
    exigir_senha()
    cabecalho('Teste IDOR - usuario A tentando usar a placa e a viagem do usuario B')

    token_a = token_de(USUARIO_A)
    token_b = token_de(USUARIO_B)
    viagem_b, placa_b = recursos_do_b(token_b)
    print(f'Recursos do B: viagem id={viagem_b}, placa id={placa_b}\n')

    print('Tentativas do usuario A (deveriam ser recusadas):')
    situacoes = [
        resultado(f'ler a viagem do B        GET  /shipments/{viagem_b}',
                  chamar('GET', f'/shipments/{viagem_b}', token_a)),
        resultado(f'ler o resumo do B        GET  /shipments/{viagem_b}/summary',
                  chamar('GET', f'/shipments/{viagem_b}/summary', token_a)),
        resultado(f'ler as leituras do B     GET  /shipments/{viagem_b}/readings',
                  chamar('GET', f'/shipments/{viagem_b}/readings', token_a)),
        resultado(f'ler a placa do B         GET  /devices/{placa_b}',
                  chamar('GET', f'/devices/{placa_b}', token_a)),
        resultado(f'alterar a viagem do B    PATCH /shipments/{viagem_b}',
                  chamar('PATCH', f'/shipments/{viagem_b}', token_a, json={})),
        # Comando por ultimo: encerra a viagem do B (por isso o preparar a reabre).
        resultado(f'comandar (encerrar) B    POST /shipments/{viagem_b}/finish',
                  chamar('POST', f'/shipments/{viagem_b}/finish', token_a, data={'condition': 'good'})),
    ]

    print('\nO dono (usuario B) continua usando normalmente:')
    resultado(f'B le a propria viagem    GET  /shipments/{viagem_b}',
              chamar('GET', f'/shipments/{viagem_b}', token_b), esperado_protegido=False)

    vulneraveis = situacoes.count('VULNERAVEL')
    print('\n' + '-' * 72)
    if vulneraveis:
        print(f'RESULTADO: VULNERAVEL - {vulneraveis} de {len(situacoes)} tentativas do A passaram.')
    else:
        print(f'RESULTADO: PROTEGIDO - as {len(situacoes)} tentativas do A foram recusadas.')
    print('Para repetir: python manage.py preparar_teste_seguranca (reabre a viagem do B).')


if __name__ == '__main__':
    main()
