# API — guia rápido para o front e para a placa

Base: `https://projeto-integrador-time1.onrender.com/api/v1` · Swagger: `/api/docs/`
(em produção: faça login em `/admin/` com um usuário **staff**, que também pede o código do 2FA, e volte para `/api/docs/`).

- Sucesso vem em `{"data": ...}`. Listas: `{"data": [...], "pagination": {"next", "previous", "count"}}`.
- Erro vem como `{"detail": "..."}` ou `{"campo": ["..."]}`. Alguns erros trazem também um `code` (ver o chat).
- Rotas aceitam com ou sem barra no final.
- Pessoas: `Authorization: Bearer <access>`. Placa: `X-Device-Key: <chave>`.

## Autenticação (login em duas etapas: senha + código do app autenticador)

| Método | Rota | Corpo | Resposta (`data`) |
|---|---|---|---|
| POST | `/auth/login` | `{"email", "password"}` | `{"mfa_required": true, "mfa_setup_required", "mfa_token", "expires_in": 300}` (**sem** access) |
| POST | `/auth/2fa/setup` | `{"mfa_token"}` | primeiro acesso: `{"qr_code" (SVG em data URI), "secret", "otpauth_uri"}` |
| POST | `/auth/2fa/activate` | `{"mfa_token", "code"}` | primeiro acesso: `{"access", "refresh", "user", "recovery_codes": [10 códigos]}` |
| POST | `/auth/2fa/verify` | `{"mfa_token", "code"}` ou `{"mfa_token", "recovery_code"}` | `{"access", "refresh", "user": {"id", "name", "email", "role"}}` |
| POST | `/auth/2fa/recovery-codes` | `{"code"}` (com JWT) | `{"recovery_codes": [...]}`: gera novos; os antigos deixam de valer |
| POST | `/auth/refresh` | `{"refresh"}` | `{"access"}` |
| GET | `/auth/me` | — | usuário, `role`, grupos e permissões |
| POST | `/auth/logout` | `{"refresh"}` | invalida o refresh |
| POST | `/auth/password-reset` · `/auth/password-reset/confirm` | `{"email"}` · `{"uid", "token", "password"}` | recuperação de senha por e-mail |

- `mfa_setup_required: true` → telas de cadastro (setup → activate). `false` → tela do código (verify).
- O `mfa_token` vale 5 min; vencido → 401 (voltar para e-mail e senha).
- Código errado, vencido ou já usado → 400 com `detail`. Muitas tentativas → 429 (10 por minuto).
- `role`: `admin`, `seller` (vendedor), `buyer` (comprador), `driver` (motorista), `operator` ou `viewer`.
- O access vale 30 min; o refresh, 1 dia.

## Gestão de usuários (só a plataforma: tela "Usuários")

| Método | Rota | Corpo | Resposta (`data`) |
|---|---|---|---|
| GET | `/auth/users` (sem `role`) | — | `[{"id", "name", "email", "role", "is_active", "has_password", "has_2fa", "last_login", "date_joined"}]` |
| POST | `/auth/users` | `{"email", "name", "role": "seller\|buyer\|driver\|admin"}` | 201 `{"user", "invite_sent", "password_setup_link"}` |
| PATCH | `/auth/users/{id}` | `{"name"?, "role"?, "is_active"?}` | o usuário atualizado |
| POST | `/auth/users/{id}/invite` | — | `{"invite_sent", "password_setup_link"}` |
| POST | `/auth/users/{id}/reset-2fa` | — | apaga o 2FA (celular perdido); no próximo login a pessoa cadastra de novo |

- A conta nasce **sem senha**: a pessoa recebe por e-mail um link de uso único (vale 3 dias) e define a senha
  na mesma tela da recuperação de senha (`/auth/password-reset/confirm` com `uid` e `token` do link).
- `password_setup_link` só vem preenchido quando o e-mail **não** saiu (Resend não configurado): aí a plataforma
  copia o link e manda à pessoa por outro canal. Quando o e-mail sai, vem `null`.
- `has_password: false` = convite ainda não aceito. Convite vencido: "reenviar convite" ou "Esqueci minha senha".
- Só superusuário cria ou promove `admin` e altera outro superusuário. Ninguém desativa nem troca o papel da própria conta (400).
- Desativar (`is_active: false`) bloqueia o login e derruba as sessões abertas.
- Quem não é plataforma recebe 403 (ou 400 no `GET` sem `role`). Toda ação vai para o log de segurança.

## Quem vê o quê (proteção contra IDOR)

Cada usuário só enxerga o que é dele; a plataforma (superusuário ou grupo Administrador) vê tudo.

- **Viagem:** quem criou (vendedor), o comprador, o motorista e o dono da placa. Leituras, impactos, alertas e itens seguem a viagem.
- **Placa:** só o dono (`owner`, definido pela plataforma no `/admin`).
- **Local e veículo:** os próprios, os compartilhados (`owner: null`, cadastrados pela plataforma) e os das viagens de que o usuário participa.
- Recurso de outro usuário → **404** (igual a "não existe"). Vê o recurso mas o papel não permite a ação → **403**.
- IDs no corpo também são conferidos: usar placa, veículo ou local de outro vendedor numa viagem → 403.

## Cadastros e viagens

| Método | Rota | O que faz |
|---|---|---|
| GET/POST | `/fruits` | Frutas com os limites ativos em `limits` |
| GET/POST | `/fruit-parameters` | Limites por fruta (só a plataforma altera) |
| GET/POST/PATCH | `/locations`, `/vehicles` | Cadastros com dono (`owner` vem do token; só o dono altera) |
| GET/PATCH | `/devices` | Placas do usuário (`owner` só leitura) |
| GET | `/auth/users?role=buyer\|driver&search=` | Compradores ou motoristas para o formulário de viagem: `[{"id", "name"}]` (só vendedor e plataforma) |
| GET/POST | `/shipments` | Viagens (filtros: `status`, `device`, `origin`, `destination`, `buyer`, `driver`) |
| GET | `/shipments/current` | Viagens do motorista logado (`planned`, `active`, `delivered`), sem paginação |
| POST | `/shipment-items` | Fruta e lote numa viagem (só o vendedor da viagem) |
| POST | `/shipments/{id}/start` | `planned` → `active` (motorista ou vendedor) |
| POST | `/shipments/{id}/finish` | `active` → `delivered` (motorista ou vendedor) |
| POST | `/shipments/{id}/confirm` | `delivered` → `completed` (só o comprador). Ver abaixo |
| GET | `/shipments/{id}/summary` | Card do dashboard |
| GET | `/shipments/{id}/readings` | Histórico (`?start=`, `?end=`, `?since=`) |
| GET | `/shipments/{id}/shocks` | Impactos |
| GET | `/shipments/{id}/alerts` | Alertas |
| GET | `/alerts` | Alertas visíveis (filtros: `shipment`, `type`, `severity`, `status`) |
| POST | `/alerts/{id}/ack` · `/alerts/{id}/resolve` | Reconhecer · encerrar |

Viagem: campos `origin`, `destination`, `vehicle`, `device`, `buyer`, `driver` (ids), `started_at`, `items`.
`buyer` precisa ser do grupo Comprador e `driver` do grupo Motorista.

Status: `planned` (Planejada) → `active` (Em andamento) → `delivered` (Entregue, aguardando confirmação) → `completed` (Concluída); ou `cancelled`.

`/confirm` é `multipart/form-data`: `condition` (`good`, `damaged` ou `critical`), `notes` (opcional) e `photos`
(JPEG/PNG, até 10). **Com avaria (`condition` diferente de `good`), a foto é obrigatória.**

Tempo real: chame `/summary` e `/readings?since=<recorded_at da última leitura>` a cada 5–10 s.

## Chat com o assistente (Gemini)

`POST /chat` com `{"message": "...", "shipment_id": 13, "history": [{"role": "user"|"model", "text": "..."}]}`.
`shipment_id` e `history` são opcionais. Resposta: `{"answer", "shipments": [ids usados no contexto]}`.

| Status | `code` | Significado |
|---|---|---|
| 400 | `invalid_message` | mensagem vazia ou com mais de 1000 caracteres |
| 404 | — | `shipment_id` não existe ou não é do usuário |
| 429 | — | mais de 5 mensagens por minuto (ver `Retry-After`) |
| 429 | `assistant_quota_exceeded` | acabou a cota gratuita do Gemini |
| 503 | `assistant_unavailable` | Gemini fora do ar, demorou ou sem chave configurada |

O assistente só recebe dados das viagens que o usuário pode ver (mesma regra do IDOR) e nenhum dado pessoal.

## Placa (ESP32)

| Método | Rota | Para quê |
|---|---|---|
| GET | `/iot/config` | Viagem ativa (`shipment_id`) e limites da placa |
| POST | `/iot/telemetry/batch` | Envia leituras e impactos em lote |
| POST | `/iot/heartbeat` | `{"network": "wifi", "wifi_ssid": "..."}`: marca a placa como online |

Lote (até 200 itens):

```json
{
  "device_uid": "VSF-001",
  "shipment_id": 3,
  "network": "wifi",
  "readings": [
    {"sequence": 1001, "recorded_at": "2026-10-31T10:00:00Z", "temperature_c": 7.8, "humidity_pct": 88.2, "impact_peak_g": 1.6}
  ],
  "shocks": [
    {"event_id": "evt-001", "recorded_at": "2026-10-31T10:02:00Z", "impact_peak_g": 3.1}
  ]
}
```

Resposta: `{"data": {"accepted_reading_sequences": [1001], "accepted_shock_ids": ["evt-001"]}}`.
A placa apaga da fila local só o que vier nessas listas. Reenviar não duplica.

Regras para a placa: `recorded_at` em UTC; `sequence` salvo na flash e nunca reiniciado;
a viagem precisa estar `active` (ou `delivered`/`completed`, para dado atrasado da fila offline).
A chave sai do comando `python manage.py criar_credencial_dispositivo <uid>` ou da seed.

Passo a passo do teste com a placa real: [`TESTE_PLACA.md`](TESTE_PLACA.md).
Segurança (2FA, IDOR, testes e evidências): pasta [`../seguranca/`](../seguranca/).
