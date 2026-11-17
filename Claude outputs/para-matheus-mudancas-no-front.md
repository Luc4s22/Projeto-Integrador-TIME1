# Mudanças na API para o front (segurança: 2FA, IDOR e chat)

Matheus, este é o resumo do que mudou no backend e do que o front precisa ajustar.
Branch: `seguranca/fases234`. **Enquanto o merge não acontece, a API publicada continua igual.**
Assim que o merge for feito, o login atual do front para de funcionar. Por isso o primeiro item (login) é o mais urgente.

Lembrete do formato que já usávamos:

- **Sucesso** vem dentro de `data`: `{"data": {...}}`.
- **Listas paginadas** vêm assim: `{"data": [...], "pagination": {...}}`.
- **Erros** vêm sem `data`: `{"detail": "mensagem em português"}`, às vezes com um `code`.

---

## 1. Login em duas etapas (obrigatório para todos)

O `POST /auth/login` **não devolve mais** `access` e `refresh`. Agora a senha só libera a etapa do código do aplicativo autenticador (Google Authenticator, Microsoft Authenticator, Authy etc.).

### Fluxo

```
Tela de login (e-mail + senha)
        │  POST /api/v1/auth/login
        ▼
{ mfa_required: true, mfa_setup_required, mfa_token, expires_in: 300 }
        │
        ├── mfa_setup_required = true  → Tela "Configurar autenticador" (primeiro acesso)
        │        POST /auth/2fa/setup     → mostra QR Code
        │        POST /auth/2fa/activate  → recebe tokens + códigos de recuperação
        │
        └── mfa_setup_required = false → Tela "Digite o código"
                 POST /auth/2fa/verify    → recebe tokens
```

Guarde o `mfa_token` só em memória (estado do React), **não** no localStorage. Ele vale 5 minutos (`expires_in`, em segundos).

### 1.1 `POST /api/v1/auth/login`

Corpo: `{ "email": "...", "password": "..." }`

Resposta 200:

```json
{ "data": {
    "mfa_required": true,
    "mfa_setup_required": false,
    "mfa_token": "eyJ1Ijo...",
    "expires_in": 300
} }
```

Erros: 400 para e-mail ou senha errados (igual a antes); 429 para tentativas demais.

### 1.2 Primeiro acesso: `POST /api/v1/auth/2fa/setup`

Corpo: `{ "mfa_token": "..." }`

Resposta 200:

```json
{ "data": {
    "qr_code": "data:image/svg+xml;base64,PHN2Zy...",
    "secret": "JBSWY3DPEHPK3PXP...",
    "otpauth_uri": "otpauth://totp/Caminho%20do%20Vale:..."
} }
```

- **`qr_code`**: vai direto no `<img src={qr_code} />`.
- **`secret`**: mostre embaixo do QR, como alternativa para digitar à mão ("Não consegue ler o QR? Digite este código no app").
- **`otpauth_uri`**: no celular (PWA), pode virar um link `<a href={otpauth_uri}>Abrir no app autenticador</a>`.
- **Erro 400 `O autenticador já está configurado nesta conta.`**: mande o usuário para a tela "Digite o código".

### 1.3 Confirmar o cadastro: `POST /api/v1/auth/2fa/activate`

Corpo: `{ "mfa_token": "...", "code": "123456" }`

Resposta 200:

```json
{ "data": {
    "access": "...", "refresh": "...",
    "user": { "id": 1, "name": "...", "email": "...", "role": "seller" },
    "recovery_codes": ["ABCD-EFGH", "JKLM-NPQR", "... (10 códigos)"]
} }
```

**Importante:** os `recovery_codes` aparecem **uma única vez**. Mostre uma tela "Guarde estes códigos" com:

- botão copiar e/ou baixar `.txt`;
- uma caixa de seleção "Guardei os códigos" antes de seguir para o sistema.

Cada código serve para entrar **uma vez** se a pessoa perder o celular.

Erro 400 `Código inválido.`: deixe a pessoa tentar de novo.

### 1.4 Acessos seguintes: `POST /api/v1/auth/2fa/verify`

Corpo, uma das duas opções:

- `{ "mfa_token": "...", "code": "123456" }`
- `{ "mfa_token": "...", "recovery_code": "ABCD-EFGH" }` (link "Perdi meu celular / usar código de recuperação")

Resposta 200: `{ "data": { "access", "refresh", "user" } }`. A partir daqui, tudo segue como era antes.

Erros:

| Status | `detail` | O que fazer no front |
|---|---|---|
| 400 | `Código inválido ou vencido.` | Limpar o campo e pedir de novo |
| 400 | `Este código já foi utilizado. Aguarde o próximo.` | Avisar para esperar o app mostrar outro código |
| 400 | `Código de recuperação inválido ou já utilizado.` | Mostrar a mensagem |
| 401 | `Sessão de login expirada...` | O `mfa_token` venceu (5 min): voltar para a tela de e-mail e senha |
| 429 | (muitas tentativas) | Mostrar o `detail` e esperar |

Dicas para o campo do código: `inputMode="numeric"`, `autoComplete="one-time-code"`, `maxLength={6}`. Envie quando completar 6 dígitos.

### 1.5 Gerar códigos de recuperação novos (tela de perfil)

`POST /api/v1/auth/2fa/recovery-codes`, **com** `Authorization: Bearer <access>`.

Corpo: `{ "code": "123456" }` (código atual do app)

Resposta 200: `{ "data": { "recovery_codes": [...] } }`. Os códigos antigos param de valer.

### 1.6 Depois do deploy

Todos os refresh tokens antigos foram invalidados. Quem estava logado vai receber 401 no refresh e deve voltar para a tela de login. O fluxo atual de "401 → tela de login" já resolve isso.

---

## 2. Papéis (`role` em `/auth/me` e no `user` do login)

Valores possíveis: `admin`, `seller` (vendedor), `buyer` (comprador), `driver` (motorista), `operator`, `viewer`.

| Papel | O que vê | O que faz |
|---|---|---|
| `admin` | tudo | tudo (pelo `/admin` do Django) |
| `seller` | viagens que criou ou que usam placa dele; só as placas dele | cria viagem e carga, escolhe comprador, motorista e placa, edita, inicia e finaliza |
| `driver` | só as viagens em que é o motorista | inicia e finaliza a viagem dele |
| `buyer` | só as viagens em que é o comprador | acompanha e **confirma o recebimento** |

Use o `role` para decidir o menu e os botões. **Mesmo assim, o backend bloqueia sozinho**: esconder o botão é só para a experiência do usuário.

---

## 3. Viagens (`/api/v1/shipments`)

### 3.1 Campos novos

- `buyer`: id do usuário comprador (precisa estar no grupo Comprador).
- `driver`: id do usuário motorista (precisa estar no grupo Motorista).
- Filtros novos: `GET /shipments?buyer=5`, `GET /shipments?driver=7`.

> Ainda **não existe** uma rota que liste os compradores e motoristas para preencher o select. O Wendell vai criar. Até lá, deixe o campo pronto e use um id fixo de teste.

### 3.2 Status novo: `delivered`

```
planned ──/start──► active ──/finish──► delivered ──/confirm──► completed
(Planejada)        (Em andamento)       (Entregue, aguardando     (Concluída)
                                          confirmação)
```

**Mudança de comportamento:** o botão "Finalizar viagem" agora deixa a viagem em `delivered`, não mais em `completed`. Quem conclui é o comprador. Precisa de um badge ou cor para `delivered`.

### 3.3 Ações

| Rota | Quem pode | Corpo | Observação |
|---|---|---|---|
| `POST /shipments/{id}/start` | motorista da viagem ou vendedor | (vazio) | Igual a antes |
| `POST /shipments/{id}/finish` | motorista da viagem ou vendedor | (vazio) | `active` → `delivered` |
| `POST /shipments/{id}/confirm` | **só o comprador** (ou admin) | `multipart/form-data` (ver abaixo) | `delivered` → `completed` |

Corpo do `/confirm`:

- `condition`: `good`, `damaged` ou `critical` (obrigatório);
- `notes`: texto opcional, até 10.000 caracteres;
- `photos`: arquivos JPEG ou PNG (campo repetido, até 10). **Obrigatório quando `condition` não é `good`.**

Erros do `/confirm` (400): `Com avaria, envie ao menos uma fotografia como prova.`, `Informe uma condição válida...`, `Só é possível confirmar uma viagem entregue pelo motorista.`

### 3.4 Tela do motorista: `GET /api/v1/shipments/current`

Devolve as viagens do motorista logado com status `planned`, `active` ou `delivered`, ordenadas pelo início previsto. É a base da tela "Minha viagem" do PWA:

- `planned` → botão **Iniciar viagem**;
- `active` → leituras ao vivo e botão **Finalizar viagem**;
- `delivered` → "Aguardando confirmação do comprador".

Resposta: `{ "data": [ {viagem}, ... ] }` (lista **sem** paginação).

---

## 4. "Não encontrado" e "Sem permissão" (proteção IDOR)

Agora cada usuário só enxerga o que é dele. Isso vale para viagens, placas, leituras, alertas e itens.

- **404** `Não encontrado.`: o recurso não existe **ou é de outra pessoa**. O front não consegue saber qual dos dois, e é de propósito. Mostre "Viagem não encontrada" e um botão para voltar à lista.
- **403** `Você não tem permissão para esta ação nesta viagem.`: a pessoa vê a viagem, mas o papel dela não permite a ação. Exemplos: comprador tentando iniciar; motorista tentando editar.
- **403** `Esta placa não é sua.`: o vendedor tentou criar ou editar uma viagem com a placa de outro vendedor.
- As listas (`GET /shipments`, `/devices`, `/alerts`...) já vêm filtradas. Não precisa filtrar no front.

---

## 5. Chat com o assistente (Gemini)

### `POST /api/v1/chat` (com JWT)

Corpo:

```json
{
  "message": "Como está a temperatura da minha carga?",
  "shipment_id": 13,
  "history": [
    { "role": "user",  "text": "pergunta anterior" },
    { "role": "model", "text": "resposta anterior" }
  ]
}
```

- `message`: obrigatório, até 1000 caracteres.
- `shipment_id`: opcional. Quando a pessoa abre o chat de dentro da tela de uma viagem, mande o id dela. Sem ele, o assistente usa as viagens mais relevantes do usuário (até 5).
- `history`: opcional. Mande as últimas trocas, e o backend usa só as 6 últimas. `role` é `user` (o que a pessoa escreveu) ou `model` (o que o assistente respondeu).

Resposta 200: `{ "data": { "answer": "texto da resposta", "shipments": [13] } }`

Erros (sempre com `detail` pronto para mostrar):

| Status | `code` | Significado | Sugestão de UI |
|---|---|---|---|
| 400 | `invalid_message` | mensagem vazia ou maior que 1000 caracteres | validar antes de enviar |
| 404 | (nenhum) | `shipment_id` não existe ou não é do usuário | "Viagem não encontrada" |
| 429 | (nenhum) | o usuário mandou mais de 5 mensagens por minuto | mostrar `detail`; o cabeçalho `Retry-After` diz quantos segundos esperar |
| 429 | `assistant_quota_exceeded` | acabou a cota gratuita do Gemini | "Assistente indisponível por hoje"; desabilitar o envio por um tempo |
| 503 | `assistant_unavailable` | Gemini fora do ar, demorou ou chave não configurada | "Tente de novo em instantes" |

Diferencie os dois 429 pelo campo `code`.

Sugestões:

- mostrar "digitando..." enquanto espera (a resposta pode levar alguns segundos);
- bolha da mensagem com erro e botão "tentar de novo";
- contador de caracteres (máximo 1000).

---

## 6. Checklist do front

- [ ] Tela de login → guardar `mfa_token` em memória.
- [ ] Tela "Configurar autenticador" (QR + segredo + campo do código).
- [ ] Tela "Guarde seus códigos de recuperação" (copiar/baixar + confirmação).
- [ ] Tela "Digite o código" + link "usar código de recuperação".
- [ ] Tratar 401 do `mfa_token` vencido (voltar ao login).
- [ ] Perfil: botão "Gerar novos códigos de recuperação".
- [ ] Menu e botões por `role` (`seller`, `buyer`, `driver`).
- [ ] Formulário de viagem com `buyer` e `driver`.
- [ ] Badge para o status `delivered`; "Finalizar" agora leva a `delivered`.
- [ ] Tela de confirmação do comprador (condição, observações, fotos obrigatórias com avaria).
- [ ] Tela "Minha viagem" do motorista (`/shipments/current`).
- [ ] Tratar 404 e 403 com mensagens amigáveis.
- [ ] Componente de chat com os erros da tabela da seção 5.

Dúvidas: o Swagger em `/api/docs` já mostra as rotas novas.
