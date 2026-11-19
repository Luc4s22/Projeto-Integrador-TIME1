# Segurança — Caminho do Vale

## 1. Objetivo e escopo

Este diretório documenta dois controles implementados na API Django: **autenticação em dois fatores (2FA/TOTP)** e **autorização por recurso para mitigar IDOR**. O objetivo é permitir que outra pessoa identifique os controles, prepare dados sintéticos e reproduza os testes sem acessar dados reais. O modelo de ameaças está em [`modelo-ameacas.md`](modelo-ameacas.md) e o registro de IA em [`uso-de-ia.md`](uso-de-ia.md).

**Status desta documentação:** implementação identificada por inspeção do projeto enviado em 19/11/2026; os resultados de execução *depois* das correções devem ser anexados e validados pela equipe. Não confundir inspeção de código com teste efetivamente executado ou confirmação de deploy.

## 2. Controles implementados e localização

| Controle | Local do código | Funcionamento |
| --- | --- | --- |
| TOTP, cadastro de autenticador e QR Code | `usuarios/dois_fatores.py` | Cria o segredo e URI `otpauth://`, gera QR Code em SVG e valida o código no servidor. |
| 2FA no login | `usuarios/views.py`, `usuarios/urls.py` | O login usa uma etapa intermediária `mfa_token`; `POST /auth/2fa/setup` inicia o cadastro, `POST /auth/2fa/activate` ativa o fator e `POST /auth/2fa/verify` valida o segundo fator antes de emitir tokens de acesso. |
| Recuperação de acesso | `usuarios/dois_fatores.py`, `usuarios/views.py`, `usuarios/models.py` | Gera códigos de recuperação com hash persistido; cada código só pode ser usado uma vez. A rota `POST /auth/2fa/recovery-codes` substitui os códigos antigos após conferir TOTP. |
| Limites de tentativas | `usuarios/views.py`, `piADS04/settings.py` | O escopo `mfa` usa `ScopedRateThrottle`; `THROTTLE_MFA` tem padrão `10/min`. O escopo `login` também tem padrão `10/min`. Configurações de ambiente podem alterar esses valores. |
| Regra central de visibilidade e log IDOR | `usuarios/acesso.py` | `ProtecaoDonoMixin` filtra o queryset segundo `request.user`; recursos existentes mas não visíveis recebem 404, com tentativa registrada em log. |
| Viagens e itens de viagem | `transporte/views.py` | ViewSets aplicam filtro de autorização por viagem e seu relacionamento com o usuário. |
| Placas e leituras | `iot/views.py` | Filtragem de dispositivos por proprietário e de leituras por viagem permitida. |
| Alertas | `alertas/views.py` | Filtragem pelo acesso à viagem vinculada ao alerta. |
| Veículos e locais | `dominio/views.py` | Consulta permite itens próprios, compartilhados ou vinculados a viagens autorizadas; alteração/remoção exigem dono ou administrador da plataforma. |

A política **não** se resume a comparar `created_by`: viagens podem ser visíveis a quem criou, comprador, motorista e dono do dispositivo associado; superusuário ou grupo `Administrador` têm acesso de plataforma. Cadastros compartilhados sem dono são visíveis, mas só a plataforma os altera. As regras exatas estão em `usuarios/acesso.py`.

Os endpoints e contratos adicionais estão em `docs/API.md`.

## 3. Requisitos para reproduzir

1. Use Python, as dependências de `requirements.txt`, a configuração Django e um banco de dados **de teste**, conforme `.env.example` e o README principal. Nunca publique senhas, segredos, tokens ou conteúdo do `.env` no Git.
2. Execute os comandos a partir da **raiz** do projeto, onde fica `manage.py`.
3. Configure a API e as variáveis de teste no PowerShell, **substituindo os exemplos por valores privados**:

```powershell
$env:TESTE_SENHA = '<senha-privada-de-teste-com-10-ou-mais-caracteres>'
$env:TESTE_TOTP_SEGREDO = python -c "import pyotp; print(pyotp.random_base32())"
$env:MISSAO = '<codigo-da-equipe>'
$env:API_URL = 'http://127.0.0.1:8000/api/v1'
```

- `TESTE_SENHA`: senha dos usuários sintéticos; o comando exige pelo menos 10 caracteres.
- `TESTE_TOTP_SEGREDO`: mesmo segredo base32 para os usuários sintéticos com 2FA habilitado; é dado sensível, não registrar seu valor nos documentos nem nas evidências.
- `MISSAO`: identificador da missão usado no cabeçalho dos resultados e nos logs do servidor (via configuração própria).
- `API_URL`: endereço-base da API **a ser testada**. O script `seguranca/testes/comum.py` possui um padrão apontando para Render, portanto **defina explicitamente a URL local/de homologação** para evitar alterar dados de produção.

**Preparação do banco de teste:**

```powershell
python manage.py migrate
python manage.py criar_grupos
python manage.py carregar_limites_iniciais
python manage.py preparar_teste_seguranca --terceiro
```

O último comando cria/reaproveita os vendedores sintéticos A, B e C; A e B recebem seus próprios dispositivos, veículos, locais e viagens, e C não recebe placa nem viagem. Os registros podem ser atualizados/reabertos em novas execuções. **Não execute esta preparação em uma base com dados reais**: o comando reutiliza identificadores de teste e redefine credenciais/estado das viagens sintéticas. Caso o servidor seja iniciado localmente, mantenha-o em outro terminal com `python manage.py runserver`.

## 4. Execução dos testes

**Primeiro os testes automáticos do Django:**

```powershell
python manage.py test
```

**Depois, com o ambiente de teste preparado e a API respondendo em `API_URL`:**

```powershell
python seguranca/testes/teste_otp.py
python seguranca/testes/teste_idor.py
python seguranca/testes/teste_terceiro_usuario.py
python seguranca/testes/teste_janela_otp.py
```

- `teste_otp.py`: valida ausência de token final só com senha, código inválido, código válido, prevenção de reutilização e recuperação de uso único.
- `teste_idor.py`: o usuário A tenta acessar recursos de B por ID e exercita cenários de contorno. **Pode fazer PATCH ou encerrar a viagem de teste de B**; execute exclusivamente sobre dados sintéticos autorizados. Em caso de repetição, rode novamente `preparar_teste_seguranca --terceiro`.
- `teste_terceiro_usuario.py`: verifica se o usuário C, sem placas e viagens, consegue ver registros alheios.
- `teste_janela_otp.py`: compara a aceitação de código do intervalo anterior; para demonstrar janela estrita, altere `OTP_VALID_WINDOW=0` na configuração **local** do servidor, reinicie-o e repita. O padrão do código é `1`.

**Teste interativo de revogação de códigos de recuperação:**

```powershell
python seguranca/testes/teste_invalidar_recuperacao.py
```

O script orienta uma ação entre duas etapas. Em outro terminal do **mesmo ambiente e banco** da API de teste, execute o comando informado pelo script, por exemplo:

```powershell
python manage.py invalidar_codigos_recuperacao vendedor-a@teste.local
```

Depois retorne ao primeiro terminal para comprovar que o código revogado é rejeitado. Execute apenas com usuários de teste. Alguns scripts imprimem valores de OTP ou recuperação no terminal: **remova ou oculte esses dados antes de compartilhar qualquer captura ou log**.

### 4.1 Postman

Importe `seguranca/testes/caminho-do-vale.postman_collection.json`. Configure `base_url` para o servidor autorizado de teste e preencha as variáveis de coleção necessárias. A coleção contém o fluxo em duas etapas e cenários de acesso. Nunca exporte a coleção com `senha`, `codigo`, `mfa_token`, `access` ou `refresh` preenchidos.

### 4.2 Critérios para interpretar

- **2FA:** a autenticação apenas por senha não deve fornecer o token JWT final quando o segundo fator estiver ativo; OTP inválido ou reutilizado deve ser recusado; recuperação deve funcionar uma única vez.
- **IDOR:** tentativa de acessar um objeto privado de outra conta por ID deve ser negada (normalmente 404; algumas alterações podem retornar 403), sem impedir que o usuário legítimo continue acessando seu próprio objeto.
- **Limites de requisição:** verificar o escopo `mfa` com testes próprios em ambiente de teste, respeitando que a taxa real depende da configuração e do cache da execução.

Nenhum resultado de execução posterior à correção é afirmado aqui sem arquivo de evidência correspondente.

## 5. Evidências

| Controle | Antes (já localizado no ZIP) | Depois (a anexar pelo responsável) |
| --- | --- | --- |
| Login sem segundo fator | `seguranca/evidencias/otp-antes.txt` — em 17/11/2026 a senha, sozinha, gerou acesso | **Pendente:** nome/caminho do log ou captura do teste 2FA após a correção |
| IDOR | `seguranca/evidencias/idor-antes.txt` — em 17/11/2026 foram registradas 6/6 tentativas indevidas aceitas | **Pendente:** nome/caminho do log ou captura após a correção, incluindo veículos e locais |
| Limite OTP e alterações ao vivo | Não há arquivo específico de antes identificado | **Pendente:** evidência de janela OTP, revogação de código e bloqueio por taxa, se exigida |
| Testes automatizados e vídeo | Não há registro de execução final anexado nesta cópia | **Pendente:** saída dos testes e links/nomes dos vídeos preparados pela equipe |

**Responsabilidade pelas evidências e vídeos de depois: Wendell**, segundo o documento de tarefas de 19/11/2026. Os nomes pendentes devem ser substituídos pelos arquivos efetivamente produzidos, sem simular resultados.

## 6. Limitações e riscos residuais

- O 2FA reduz o risco de uso indevido de **senha isoladamente vazada**, mas não elimina phishing em tempo real, roubo de sessão/JWT, comprometimento do dispositivo autenticador ou indisponibilidade do serviço.
- A proteção IDOR se aplica às rotas que realmente usam os filtros de acesso; novas rotas ou consultas criadas sem verificação apropriada podem reintroduzir a falha. Administradores possuem acesso mais amplo por regra de negócio.
- A credencial `X-Device-Key` protege a ingestão por dispositivo, mas o acesso físico à placa pode expor a chave; essa mitigação é parcial.
- MQTT em broker público, sem autenticação/TLS conforme o modelo atual, continua com risco de leitura/publicação indevida; a API mantém o histórico oficial separadamente.
- O padrão `10/min` do escopo MFA e do login é mitigação parcial contra tentativas em massa, não proteção completa contra ataques distribuídos e negação de serviço; a configuração pode variar conforme ambiente.

**Pendente de conciliação:** confrontar esta seção com a seção **5.4 de `guia-apresentacao.md`**, material citado no documento de tarefas, mas não incluído no ZIP analisado. Não considerar esta lista reprodução literal daquele guia.

## 7. Participação da equipe e origem das informações

- **Lucas:** responsável pelos arquivos `seguranca/README.md`, `seguranca/uso-de-ia.md` e atualização de `seguranca/modelo-ameacas.md`, conforme divisão de tarefas de 19/11/2026.
- **Wendell:** identificado no documento de tarefas como responsável pelos testes posteriores, arquivos de evidência e vídeos; também é citado como responsável pelo material de apoio `guia-apresentacao.md` e `aula-seguranca-codigo.md` (não versionar esses materiais se forem enviados fora do Git).
- **Autoria de cada controle de código e dos demais integrantes:** confirmar com histórico Git/PRs e equipe antes de atribuir nominalmente. A presença de código na main, por si só, não prova autoria individual.

## 8. Revisão antes da entrega

- [ ] Confirmar correspondência com `guia-apresentacao.md` (especialmente seção 5.4).
- [ ] Preencher nomes reais de evidências de depois e vídeos quando enviados por Wendell.
- [ ] Revisar `uso-de-ia.md` com histórico dos commits de 02/10 e prompts efetivamente usados.
- [ ] Conferir execução em ambiente isolado e remover segredos das capturas.
- [ ] Criar PR da branch `docs/seguranca` com os arquivos da pasta `seguranca/`.
