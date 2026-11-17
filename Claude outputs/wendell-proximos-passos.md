# Próximos passos: Wendell (backend + entrega de segurança)

Prazo considerado: **22/11** (AVA). Hoje: 17/11.

Pasta do projeto no seu PC: `C:\Users\Miguel.Luis\Documents\Wendell\projetos\new-pi\Projeto-Integrador-TIME1\`
Todos os comandos abaixo rodam no **PowerShell, nessa pasta, com a venv ativa** (`.\venv\Scripts\Activate.ps1`).

---

## Passo 1: conferir e testar localmente (hoje)

1. Instalar as bibliotecas novas (`pyotp`, `qrcode`, `cryptography`):
   ```powershell
   pip install -r requirements.txt
   ```
2. Conferir o `.env` local (só **você** abre esse arquivo). Variáveis novas, todas opcionais:

   | Variável | Para quê | Se ficar vazia |
   |---|---|---|
   | `SECURITY_MISSION_CODE` | código da missão que aparece nos logs | aparece `SEM-CODIGO` |
   | `GEMINI_API_KEY` | chave do Gemini para o chat | `/chat` responde 503 |
   | `OTP_ENCRYPTION_KEY` | chave que cifra os segredos do 2FA | usa uma derivada do `SECRET_KEY` |

   O `.env.example` já lista todas.
3. Aplicar as migrations no banco que o `.env` aponta:
   ```powershell
   python manage.py migrate
   python manage.py criar_grupos
   ```
   - `migrate` cria `SegundoFator` e `CodigoRecuperacao` e revoga os refresh tokens antigos.
   - `criar_grupos` cria e atualiza os grupos Vendedor, Comprador e Motorista.

   **Atenção:** se o `.env` local aponta para o Neon de **produção**, essas migrations já mudam a produção. A API publicada (código antigo) continua funcionando, porque as tabelas novas são só acréscimos. Mas a 0004 desloga todo mundo, e os usuários entram de novo normalmente pelo login antigo até o deploy.
4. Rodar os testes. Agora funcionam também com `DEBUG=False` (detalhe no Passo 6):
   ```powershell
   python manage.py test
   ```
   Esperado: `Ran 131 tests ... OK`.

---

## Passo 2: commit e PR (hoje)

```powershell
git status                      # o .env NÃO pode aparecer (ele está no .gitignore)
git checkout -b seguranca/fases234
git add .
git commit -m "Seguranca: protecao IDOR, 2FA com TOTP e chat com Gemini"
git push -u origin seguranca/fases234
```

- **Base da branch:** se o PR da **fase 1** (`seguranca/fase1`) ainda não foi aceito, crie esta branch a partir dela: `git checkout seguranca/fase1` e depois `git checkout -b seguranca/fases234`. Os arquivos alterados vêm junto, porque o Git não mexe neles ao trocar de branch.
- **Commits separados:** dá para dividir em vários commits no mesmo dia, para o histórico ficar legível. Faça `git add` por grupo de arquivos (lista na seção "Onde está cada coisa" abaixo).
- **PR:** abra no GitHub, mas **segure o merge** até o Matheus adaptar o login.
- **Commits em 3 dias diferentes:** este é o 1º dia. Os passos 4 e 5 (evidências, README, uso-de-ia) dão o 2º e o 3º. **Lucas e Matheus também precisam ter commits.** Sugestão:
  - Lucas faz o teste do "depois" em produção e commita as evidências;
  - Matheus commita o front do 2FA.

### Onde está cada coisa

| Pasta/arquivo | O que tem | Fase |
|---|---|---|
| `usuarios/acesso.py` | regra de dono (IDOR) + log de bloqueio | 2 |
| `transporte/views.py` | viagens: filtro de dono, papéis, `/current`, `/finish`, `/confirm` | 1 e 2 |
| `iot/views.py`, `alertas/views.py` | placas, leituras e alertas filtrados pelo dono | 2 |
| `usuarios/test_idor.py`, `transporte/tests.py` | testes automáticos de IDOR | 2 |
| `usuarios/models.py` + `usuarios/migrations/0003`, `0004` | tabelas do 2FA + revogação dos tokens antigos | 3 |
| `usuarios/dois_fatores.py` | toda a lógica do TOTP e dos códigos de recuperação | 3 |
| `usuarios/views.py`, `urls.py`, `serializers.py` | rotas `/auth/login` e `/auth/2fa/*` | 3 |
| `usuarios/admin.py` + `usuarios/templates/admin/login_com_codigo.html` | login do `/admin` pedindo código | 3 |
| `usuarios/management/commands/configurar_2fa.py`, `resetar_2fa.py`, `invalidar_codigos_recuperacao.py` | comandos de manutenção | 3 |
| `usuarios/test_2fa.py`, `usuarios/tests.py`, `piADS04/tests_utils.py` | testes do 2FA | 3 |
| `assistente/` (app inteiro) | chat com Gemini | 4 |
| `piADS04/settings.py`, `piADS04/urls.py`, `requirements.txt`, `.env.example` | configuração das 3 fases | 2, 3, 4 |
| `seguranca/testes/comum.py`, `teste_idor.py`, `teste_otp.py` | scripts antes/depois (evidência) | 2 e 3 |
| `usuarios/management/commands/preparar_teste_seguranca.py` | cria os usuários de teste | 2 e 3 |

---

## Passo 3: deploy (depois que o Matheus adaptar o login)

1. **Render → Environment**, adicionar:
   - `SECURITY_MISSION_CODE` = código da missão;
   - `GEMINI_API_KEY` = chave do Google AI Studio;
   - `OTP_ENCRYPTION_KEY`: opcional. Se usar, gere com:
     ```powershell
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
     Cole o valor **direto no Render**, não no chat. Depois de definida, **não troque mais**: trocar invalida todos os 2FA cadastrados.
2. Fazer o merge do PR. O Render faz o deploy, instala as bibliotecas e roda as migrations, se o build command já roda `migrate`. Se não rodar, rode o Passo 1.3 apontando para produção.
3. **Configurar o 2FA do seu superusuário** (sem isso você não entra no `/admin`). Com o `.env` local apontando para o Neon de produção:
   ```powershell
   python manage.py configurar_2fa SEU_EMAIL
   ```
   - Aparece um QR no terminal. Leia com o app autenticador e digite o código.
   - O comando imprime 10 códigos de recuperação. **Guarde fora do Git** (gerenciador de senhas ou papel).
4. Se alguém perder o celular e os códigos: `python manage.py resetar_2fa EMAIL`. No próximo login, a pessoa cadastra de novo.
5. Os usuários reais precisam estar nos grupos certos (`/admin` → Usuários → Grupos):
   - vendedor → **Vendedor**;
   - comprador → **Comprador**;
   - motorista → **Motorista**.

   Cada placa precisa ter **dono** (`owner`), definido no `/admin` → Placas. Placa sem dono só a plataforma vê.

---

## Passo 4: evidências do "depois" (itens 5 e 6, ~18 a 20/11)

1. Preparar os usuários de teste em produção (com o `.env` apontando para produção):
   ```powershell
   $env:TESTE_SENHA = "uma-senha-forte"
   $env:TESTE_TOTP_SEGREDO = "JBSWY3DPEHPK3PXP"   # qualquer base32 de 16+ caracteres, só para teste
   $env:MISSAO = "CODIGO-DA-MISSAO"
   python manage.py preparar_teste_seguranca
   ```
2. Rodar contra a API publicada e salvar a saída em UTF-8:
   ```powershell
   python seguranca/testes/teste_idor.py | Out-File -Encoding utf8 seguranca/evidencias/CODIGO-idor-depois.txt
   python seguranca/testes/teste_otp.py  | Out-File -Encoding utf8 seguranca/evidencias/CODIGO-otp-depois.txt
   ```
   Esperado: IDOR 6/6 `PROTEGIDO`; OTP com todos os itens `OK`.
3. Prints dos **logs do Render** mostrando `[CODIGO] IDOR bloqueado` e `[CODIGO] OTP recusado`.
4. Vídeos de até 90 s em `seguranca/evidencias/`, um por controle:
   - **2FA:** login com senha → pede código → código errado recusado → certo entra → mesmo código de novo recusado;
   - **IDOR:** usuário A tenta abrir a viagem de B trocando o ID → 404.
5. **Renomear** as evidências do "antes" com o código da missão (`CODIGO-idor-antes.txt` etc.).
6. Commit (2º dia): `git add seguranca/evidencias` e depois `git commit -m "Evidencias depois dos controles"`.

## Passo 5: documentos (itens 7 e 8, até 21/11)

- **`seguranca/README.md`**: o que foi implementado, como rodar os testes, onde estão as evidências, quem fez o quê.
- **`seguranca/uso-de-ia.md`**: onde a IA ajudou (geração de código, testes, revisão), o que vocês revisaram e alteraram, e os prompts principais.
- `seguranca/modelo-ameacas.md` já existe. Revise o status das ameaças 1 e 2 para "mitigada".
- Commit (3º dia) e depois a tag:
  ```powershell
  git tag entrega-final
  git push origin entrega-final
  ```
  Crie a tag **só depois do merge na main**, no commit final.
- Ensaiar a **mudança ao vivo**. Sugestão: mudar `OTP_VALID_WINDOW` ou o limite `'mfa': '10/min'` em `piADS04/settings.py`, rodar o teste e mostrar o efeito.

Posso escrever o README e o uso-de-ia quando você mandar.

---

## Passo 6: o que mudou para os testes rodarem com `DEBUG=False`

Em `piADS04/settings.py`, logo depois do bloco `if DEBUG: ... else: ...`:

```python
TESTANDO = len(sys.argv) > 1 and sys.argv[1] == 'test'
if TESTANDO:
    SECURE_SSL_REDIRECT = False
```

O cliente de teste do Django usa `http://`. Em produção (`DEBUG=False`) o Django redireciona todo `http` para `https` (301), e por isso todos os testes falhavam. Agora, **só quando o comando é `manage.py test`**, o redirecionamento é desligado. O resto (cookies seguros, HSTS) continua igual ao de produção. Verificado: 131 testes OK com `DEBUG=False` e com `DEBUG=True`.

---

## Outras pendências do backend

| Item | Onde | Prioridade |
|---|---|---|
| Rota para listar compradores e motoristas (id + nome) para o formulário de viagem | nova view em `usuarios/` | **alta**: o Matheus precisa |
| Start Command do Render: `gunicorn piADS04.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60` | painel do Render | média |
| Otimização do `/summary` (refazer sobre o `services.py` do Lucas) | `transporte/services.py` | média |
| Atualizar `docs/API.md` com as rotas novas (dá para copiar do arquivo do Matheus) | `docs/API.md` | média |
| Atualizar o PR #2 da placa com a versão dos três destinos e pedir o merge ao Anderson | repo da placa | média |
| Apagar o projeto Neon de São Paulo (backup) depois da entrega | painel do Neon | baixa |
| Avisos do drf-spectacular nas APIViews | não bloqueia | baixa |
