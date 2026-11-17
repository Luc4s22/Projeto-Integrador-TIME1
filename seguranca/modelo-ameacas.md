# Modelo de ameaças — Caminho do Vale (monitoramento do transporte de frutas)

**O que protegemos:** a conta de cada usuário (vendedor, comprador, motorista e plataforma) e o acesso a cada placa (ESP32-C3) e às viagens dela: leituras de temperatura e umidade, alertas e os comandos de iniciar e finalizar a viagem.

**Como o sistema funciona:** a placa envia as leituras para a API Django (Render) com uma chave própria (`X-Device-Key`); a API grava no PostgreSQL (Neon); o painel web/PWA consome a API com token JWT depois do login.

Classificação pelo STRIDE (S = falsificação de identidade, T = adulteração, I = vazamento de informação, D = negação de serviço, E = elevação de privilégio).

| # | Ameaça (STRIDE) | O que pode dar errado | Impacto | Controle |
| --- | --- | --- | --- | --- |
| 1 | **Senha roubada ou vazada** (S) | Quem descobre a senha de um usuário (vazamento, senha repetida em outro site, phishing) entra na conta só com ela | Vê cargas, clientes e rotas; encerra viagens; com a conta da plataforma, controla o sistema inteiro | **Tratada pelo 2FA com OTP** |
| 2 | **IDOR: acesso a recurso de outro usuário trocando o ID** (I, T, E) | Um usuário legítimo (outro vendedor, um comprador, um motorista) troca o ID na URL e lê, altera ou comanda a placa e a viagem de outro | Vazamento comercial (cargas, destinos, compradores) e sabotagem (encerrar a viagem alheia, alterar dados) | **Tratada pela verificação de dono** |
| 3 | **Placa falsa enviando leituras** (S, T) | Alguém imita a placa e manda temperaturas falsas para esconder uma falha na refrigeração | Alertas falsos ou ausentes; avaliação da carga errada | Parcial: a API exige a `X-Device-Key` e guarda só o hash. Continua aberto: quem tiver a placa em mãos lê a chave na memória dela |
| 4 | **MQTT em broker público** (I, T) | Os tópicos MQTT ficam num broker público, sem senha: qualquer um lê ou publica | Quem descobrir o tópico vê as leituras ao vivo ou publica dados falsos no painel que usa MQTT | **Aberta**: o histórico oficial vem da API, não do MQTT. Próximo passo: broker com usuário, senha e TLS |
| 5 | **Força bruta no login e no código OTP** (S, D) | Tentativas em massa de senha ou dos 6 dígitos do OTP | Adivinhar a senha ou o código; derrubar o serviço no plano gratuito | Parcial: o login já tem limite de 10 tentativas por minuto. O 2FA ganha o mesmo limite na verificação do código |

## Por que as ameaças 1 e 2 foram priorizadas

- **São as mais fáceis de explorar:** a 1 precisa só de uma senha vazada, e a 2 precisa só de uma conta comum do próprio sistema e de trocar um número na URL. Nenhuma exige acesso físico à placa.
- **Atingem o que o sistema existe para proteger:** os dados da carga e o controle da viagem. Comprador e vendedor são empresas diferentes, então o vazamento entre eles é um risco comercial real.
- **O teste do "antes" comprova as duas no sistema em produção:** o usuário A leu, alterou e encerrou a viagem do usuário B (6 de 6 tentativas passaram), e o login entregou o token só com a senha (evidências em `seguranca/evidencias/`).

## O que continua aberto depois dos dois controles

A ameaça 3 (chave legível na placa física), a 4 (MQTT público) e parte da 5 (negação de serviço no plano gratuito). Elas ficam registradas como próximos passos no `README.md`.
