"""
Teste da protecao contra IDOR (acesso a recurso de outro usuario trocando o ID).

Cenario (dados sinteticos, criados por: python manage.py preparar_teste_seguranca):
    - o usuario B tem a placa TESTE-B e uma viagem em andamento com leituras;
    - o usuario A, logado com a conta DELE, tenta ler, alterar e comandar
      a placa e a viagem do B, so trocando o ID na URL.

Resultado esperado:
    ANTES do controle -> as tentativas do A passam (VULNERAVEL);
    DEPOIS            -> todas recebem 403/404 (PROTEGIDO) e o B continua usando.

Contorno testado: o ID do outro no CORPO da requisicao (nao na URL) e a
enumeracao de IDs (comparar a resposta de "existe mas nao e seu" com "nao existe").

Uso (PowerShell, na raiz do projeto):
    $env:TESTE_SENHA = "..."; $env:MISSAO = "XXXXXX"
    $env:TESTE_TOTP_SEGREDO = "..."   (depois do 2FA: o login dos usuarios de teste pede o codigo)
    python manage.py preparar_teste_seguranca
    python seguranca/testes/teste_idor.py
"""

from comum import (
    USUARIO_A, USUARIO_B, cabecalho, chamar, exigir_senha, resultado, token_de,
)


def recursos_de(token, letra):
    """O usuario procura a PROPRIA viagem de teste (lote TESTE-IDOR-<letra>): viagem, placa, veiculo e fazenda."""
    eu = chamar('GET', '/auth/me', token).json()['data']
    resposta = chamar('GET', '/shipments', token, params={'page_size': 200})
    for viagem in resposta.json()['data']:
        lotes = [item.get('lot') for item in viagem.get('items', [])]
        if viagem.get('created_by') == eu['id'] and f'TESTE-IDOR-{letra}' in lotes:
            return viagem['id'], viagem['device'], viagem['vehicle'], viagem['origin']
    raise SystemExit(f'Viagem de teste do {letra} nao encontrada. Rode: python manage.py preparar_teste_seguranca')


def main():
    exigir_senha()
    cabecalho('Teste IDOR - usuario A tentando usar a placa e a viagem do usuario B')

    token_a = token_de(USUARIO_A)
    token_b = token_de(USUARIO_B)
    viagem_b, placa_b, veiculo_b, fazenda_b = recursos_de(token_b, 'B')
    viagem_a = recursos_de(token_a, 'A')[0]
    print(f'Recursos do B: viagem id={viagem_b}, placa id={placa_b}, veiculo id={veiculo_b}, fazenda id={fazenda_b}\n')

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
        resultado(f'ler o veiculo do B       GET  /vehicles/{veiculo_b}',
                  chamar('GET', f'/vehicles/{veiculo_b}', token_a)),
        resultado(f'alterar a fazenda do B   PATCH /locations/{fazenda_b}',
                  chamar('PATCH', f'/locations/{fazenda_b}', token_a, json={'name': 'invadida'})),
        resultado(f'alterar a viagem do B    PATCH /shipments/{viagem_b}',
                  chamar('PATCH', f'/shipments/{viagem_b}', token_a, json={})),
        # Comando por ultimo: encerra a viagem do B (por isso o preparar a reabre).
        resultado(f'comandar (encerrar) B    POST /shipments/{viagem_b}/finish',
                  chamar('POST', f'/shipments/{viagem_b}/finish', token_a, data={'condition': 'good'})),
    ]

    print('\nTentativas de contorno:')
    # 1) O ID do outro vai no CORPO, nao na URL: A troca a placa da PROPRIA viagem pela do B.
    contornos = [
        resultado(f'placa do B no corpo      PATCH /shipments/{viagem_a} {{"device": {placa_b}}}',
                  chamar('PATCH', f'/shipments/{viagem_a}', token_a, json={'device': placa_b})),
        resultado(f'veiculo do B no corpo    PATCH /shipments/{viagem_a} {{"vehicle": {veiculo_b}}}',
                  chamar('PATCH', f'/shipments/{viagem_a}', token_a, json={'vehicle': veiculo_b})),
    ]
    # 2) Enumeracao: se "existe mas nao e seu" desse resposta diferente de "nao existe",
    #    o atacante descobriria quais IDs existem. As duas respostas precisam ser iguais.
    alheia = chamar('GET', f'/shipments/{viagem_b}', token_a)
    inexistente = chamar('GET', '/shipments/999999999', token_a)
    iguais = (alheia.status_code, alheia.text) == (inexistente.status_code, inexistente.text)
    print(f'{alheia.status_code:>4}  {"PROTEGIDO" if iguais else "VULNERAVEL":<26} '
          f'enumeracao: viagem do B e viagem inexistente dao a MESMA resposta')
    contornos.append('PROTEGIDO' if iguais else 'VULNERAVEL')

    print('\nO dono (usuario B) continua usando normalmente:')
    resultado(f'B le a propria viagem    GET  /shipments/{viagem_b}',
              chamar('GET', f'/shipments/{viagem_b}', token_b), esperado_protegido=False)

    situacoes += contornos
    vulneraveis = situacoes.count('VULNERAVEL')
    print('\n' + '-' * 72)
    if vulneraveis:
        print(f'RESULTADO: VULNERAVEL - {vulneraveis} de {len(situacoes)} tentativas do A passaram.')
    else:
        print(f'RESULTADO: PROTEGIDO - as {len(situacoes)} tentativas do A foram recusadas.')
    print('Para repetir: python manage.py preparar_teste_seguranca (reabre a viagem do B).')


if __name__ == '__main__':
    main()
