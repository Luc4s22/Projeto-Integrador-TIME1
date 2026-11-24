
<div align="center">

# 🍇 CAMINHO DO VALE

### Monitoramento Inteligente do Transporte de Frutas

**Projeto Integrador | Cloud Computing | 2026**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Azure](https://img.shields.io/badge/Microsoft_Azure-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![IoT](https://img.shields.io/badge/Internet_of_Things-2E7D32?style=for-the-badge)

[🌐 Acessar sistema](https://icy-desert-0fc71aa10.3.azurestaticapps.net) •
[⚙️ Backend](https://app-caminho-vale-backend-novo-btawcgdkbzayhvc5.brazilsouth-01.azurewebsites.net) •
[💚 Health Check](https://app-caminho-vale-backend-novo-btawcgdkbzayhvc5.brazilsouth-01.azurewebsites.net/health/) •
[🚀 Pipeline](https://github.com/Luc4s22/Projeto-Integrador-TIME1/actions)

</div>

---

## 🎓 Identificação acadêmica

| Informação | Descrição |
| :--- | :--- |
| **Instituição** | Faculdade SENAC Pernambuco |
| **Curso** | Análise e Desenvolvimento de Sistemas |
| **Turma** | ADS047 |
| **Disciplina** | Cloud Computing |
| **Professor** | Ronierison Maciel |
| **Projeto** | Caminho do Vale |
| **Ano** | 2026 |

### 👥 Equipe de desenvolvimento

| Nº | Integrante |
| :---: | :--- |
| 01 | Anderson Bem |
| 02 | Lais Nayara |
| 03 | Lucas Mendes |
| 04 | Matheus Henrique |
| 05 | Wendel Brasiliano |
| 06 | Wendell Barboza |

---

## 📖 Sobre o projeto

O **Caminho do Vale** é uma solução tecnológica voltada ao monitoramento das condições de transporte de frutas, utilizando Internet das Coisas (IoT), desenvolvimento web e computação em nuvem.

O sistema permite acompanhar informações relacionadas às viagens, cargas e condições ambientais durante o transporte, contribuindo para a identificação de riscos, redução de perdas e melhoria da qualidade dos produtos transportados.

A aplicação utiliza uma API REST desenvolvida em Django, responsável pelo recebimento, processamento e disponibilização dos dados coletados pelos dispositivos IoT.

A infraestrutura em nuvem foi estruturada utilizando serviços gerenciados, buscando disponibilidade, segurança, escalabilidade e facilidade de manutenção.

### Principais funcionalidades

- Gerenciamento de viagens e cargas.
- Monitoramento de temperatura e umidade.
- Registro de impactos durante o transporte.
- Recebimento de dados de dispositivos IoT.
- Gerenciamento de alertas.
- Autenticação e controle de acesso.
- Inspeção final das cargas.
- Acompanhamento das informações pelo frontend.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Finalidade |
| :--- | :--- |
| Python | Linguagem de desenvolvimento do backend |
| Django | Framework de desenvolvimento web |
| Django REST Framework | Desenvolvimento da API REST |
| PostgreSQL | Banco de dados relacional |
| Neon | Banco de dados gerenciado em nuvem |
| Microsoft Azure | Infraestrutura e hospedagem |
| Azure App Service | Hospedagem do backend |
| Azure Static Web Apps | Hospedagem do frontend |
| GitHub Actions | Automação de testes e deploy |
| Azure Bicep | Infraestrutura como código |
| ARM | Representação declarativa da infraestrutura |
| Gunicorn | Servidor da aplicação Python |
| Swagger | Documentação da API |
| IoT | Coleta e transmissão de dados |

---

## 📁 Organização do projeto

| Diretório | Responsabilidade |
| :--- | :--- |
| `piADS04/` | Configurações e rotas principais do Django |
| `usuarios/` | Autenticação e gerenciamento de usuários |
| `dominio/` | Entidades e cadastros do sistema |
| `iot/` | Dispositivos e recebimento de telemetria |
| `transporte/` | Gerenciamento de viagens e cargas |
| `alertas/` | Gerenciamento de alertas |
| `assistente/` | Integração do assistente |
| `docs/` | Documentação técnica |
| `seguranca/` | Documentação de segurança |
| `infra/` | Infraestrutura Bicep e ARM |
| `.github/workflows/` | Automação de CI/CD |

### Execução local

Para executar o projeto em ambiente de desenvolvimento, é necessário instalar o Python e as dependências da aplicação, configurar as variáveis de ambiente, preparar o banco de dados PostgreSQL e aplicar as migrações do Django.

Após a configuração, o servidor local poderá ser iniciado para desenvolvimento e testes.

Recomenda-se utilizar um banco de dados separado do ambiente de produção.

---

# ☁️ DOCUMENTAÇÃO DE COMPUTAÇÃO EM NUVEM

---

## 01. URLs públicas da aplicação

| Ambiente | Acesso |
| :--- | :---: |
| Frontend — Azure Static Web Apps | [Acessar sistema](https://icy-desert-0fc71aa10.3.azurestaticapps.net) |
| Backend — Azure App Service | [Acessar backend](https://app-caminho-vale-backend-novo-btawcgdkbzayhvc5.brazilsouth-01.azurewebsites.net) |
| Health Check | [Verificar disponibilidade](https://app-caminho-vale-backend-novo-btawcgdkbzayhvc5.brazilsouth-01.azurewebsites.net/health/) |
| GitHub Actions | [Acompanhar pipeline](https://github.com/Luc4s22/Projeto-Integrador-TIME1/actions) |

O endpoint de verificação de saúde retornou HTTP 200 nos testes realizados em 23/11/2026, demonstrando a disponibilidade do backend no momento da validação.

---

## 02. Provedores, serviços e modelos de nuvem

A arquitetura utiliza serviços de nuvem pública de diferentes provedores, com a Microsoft Azure responsável pela hospedagem da aplicação e o Neon pelo gerenciamento do banco de dados PostgreSQL.

A utilização de serviços gerenciados reduz a necessidade de administração direta de servidores físicos e facilita a manutenção da infraestrutura.

| Serviço | Modelo | Responsabilidade |
| :--- | :---: | :--- |
| Azure App Service | PaaS | Hospedagem e execução do backend |
| Azure Static Web Apps | PaaS | Hospedagem do frontend |
| Neon PostgreSQL | DBaaS | Gerenciamento do banco de dados |
| GitHub Actions | SaaS | Automação de testes e implantação |
| Azure Monitor | Serviço gerenciado | Monitoramento da aplicação |
| Cloudinary | Serviço externo | Armazenamento de imagens previsto no código |

### Justificativa da escolha

A Microsoft Azure foi escolhida por disponibilizar serviços gerenciados para publicação de aplicações web, integração com o GitHub, monitoramento e gerenciamento de recursos.

O Neon foi utilizado por oferecer PostgreSQL gerenciado, conectividade segura e integração com aplicações Django.

A integração com o Cloudinary está prevista no código da aplicação, porém seu funcionamento em produção ainda precisa ser validado.

---

## 03. Arquitetura da solução

<div align="center">

### Fluxo de comunicação

**👤 Usuário**

⬇️ HTTPS

**🌐 Azure Static Web Apps**

*Frontend da aplicação*

⬇️ API REST / HTTPS

**⚙️ Azure App Service**

*Backend Django + Gunicorn*

⬇️ Conexão PostgreSQL / SSL

**🗄️ Neon PostgreSQL**

*Banco de dados gerenciado*

</div>

### Integração dos dispositivos IoT

Os dispositivos IoT enviam informações coletadas durante o transporte para a API do sistema. O backend processa os registros e realiza o armazenamento no banco de dados, permitindo sua consulta pelo frontend.

### Fluxo de implantação

<div align="center">

**GitHub → GitHub Actions → Azure App Service**

</div>

### Monitoramento

O acompanhamento da infraestrutura é realizado por meio dos recursos de monitoramento da Azure, incluindo métricas, fluxo de logs e verificação de saúde da aplicação.

---

## 04. Integração e entrega contínua — CI/CD

O processo de implantação do backend foi automatizado utilizando o GitHub Actions, permitindo que alterações integradas à branch principal sejam validadas e publicadas na infraestrutura da Azure.

### Etapas do pipeline

| Etapa | Processo |
| :---: | :--- |
| 01 | Desenvolvimento e alteração do código |
| 02 | Commit e envio ao GitHub |
| 03 | Abertura de Pull Request |
| 04 | Instalação das dependências |
| 05 | Build e testes da aplicação Django |
| 06 | Integração à branch principal |
| 07 | Deploy automático na Azure |
| 08 | Verificação da aplicação publicada |

### Workflow

O arquivo responsável pela automação está localizado em:

`.github/workflows/main_app-caminho-vale-backend-novo.yml`

### Evidências de execução

| Execução | Build e testes | Deploy | Tempo total | Resultado |
| :--- | :---: | :---: | :---: | :---: |
| Pull Request #3 | 1min 59s | 2min 07s | 4min 13s | Sucesso |
| Pull Request #4 | 2min 17s | 2min 34s | 4min 55s | Sucesso |

Os avisos relacionados à depreciação do Node.js 20 não impediram a conclusão das execuções.

- [Histórico de execuções do GitHub Actions](https://github.com/Luc4s22/Projeto-Integrador-TIME1/actions)
- [Evidência da execução do pipeline](https://github.com/Luc4s22/Projeto-Integrador-TIME1/actions/runs/45295518928)

O mecanismo de publicação automática do frontend deve ser confirmado em seu respectivo repositório.

---

## 05. Implantação e infraestrutura como código

A infraestrutura foi planejada utilizando os recursos da Microsoft Azure e documentada por meio do Azure Bicep e de templates ARM.

### Procedimento de implantação

| Etapa | Configuração |
| :---: | :--- |
| 01 | Configurar assinatura e grupo de recursos na Azure |
| 02 | Criar o App Service Plan |
| 03 | Provisionar o Azure App Service |
| 04 | Configurar o ambiente Python |
| 05 | Provisionar o banco PostgreSQL no Neon |
| 06 | Configurar variáveis de ambiente |
| 07 | Configurar autenticação e permissões do GitHub Actions |
| 08 | Revisar os templates de infraestrutura |
| 09 | Validar e aplicar as migrações do Django |
| 10 | Executar o pipeline de implantação |
| 11 | Configurar e publicar o frontend |
| 12 | Validar URLs, logs e Health Check |

### Infrastructure as Code — IaC

| Arquivo | Finalidade |
| :--- | :--- |
| `infra/main.bicep` | Descrição declarativa dos recursos |
| `infra/main.json` | Template ARM gerado a partir do Bicep |

O Azure Bicep permite descrever configurações da infraestrutura de forma declarativa, facilitando o versionamento, a padronização e a reprodução de ambientes.

O arquivo Bicep foi compilado com sucesso utilizando o Azure CLI 2.93.0. O template ARM resultante foi integrado à branch principal por meio da Pull Request #4.

A aplicação do template diretamente em produção ainda não foi comprovada. Como a infraestrutura referencia um App Service Plan existente e compartilhado, sua execução deve ser precedida de uma análise dos recursos e permissões.

---

## 06. Variáveis de ambiente e gerenciamento de segredos

As configurações sensíveis da aplicação devem permanecer fora do código-fonte, utilizando variáveis de ambiente e os mecanismos de gerenciamento de segredos disponibilizados pela Azure e pelo GitHub.

| Configuração | Finalidade |
| :--- | :--- |
| Django | Chave secreta, depuração e hosts permitidos |
| PostgreSQL | Credenciais e parâmetros de conexão |
| CORS | Controle de origens autorizadas |
| CSRF | Proteção contra requisições indevidas |
| SSL | Criptografia da conexão com o banco |
| Autenticação | Recuperação de senha e segundo fator |
| Integrações externas | Serviços de IA, e-mail e imagens |

### Proteção das credenciais

- Utilização do `.env.example` como modelo de configuração.
- Arquivos de ambiente reais mantidos fora do versionamento.
- Utilização do `.gitignore` para proteger arquivos sensíveis.
- Armazenamento de credenciais em configurações seguras.
- Separação entre ambientes de desenvolvimento e produção.
- Utilização de conexões criptografadas.
- Controle de permissões de acesso.

O arquivo `.env.example` não apresenta valores reais de senhas ou chaves de acesso.

A conexão ao PostgreSQL Neon foi validada com SSL obrigatório, assim como as verificações do Django e a ausência de migrações pendentes no ambiente testado.

---

## 07. Monitoramento, segurança e escalabilidade

### 📊 Monitoramento da aplicação

O monitoramento da infraestrutura utiliza os recursos disponibilizados pelo Azure App Service.

| Recurso | Configuração |
| :--- | :--- |
| Azure Monitor | Acompanhamento de métricas |
| Log Stream | Visualização do fluxo de logs |
| Health Check | Verificação de disponibilidade |
| Application Logging | File System |
| Limite de armazenamento de logs | 35 MB |
| Retenção de logs | 7 dias |

O acesso ao fluxo de logs foi confirmado. A geração efetiva de registros de requisições ainda precisa ser comprovada.

### 💚 Health Check

O endpoint de verificação de saúde permite acompanhar a disponibilidade do backend.

**Endpoint:** `/health/`

Durante os testes, a aplicação apresentou estado Healthy e a métrica de integridade registrou 100 no período consultado.

[Consultar Health Check](https://app-caminho-vale-backend-novo-btawcgdkbzayhvc5.brazilsouth-01.azurewebsites.net/health/)

### 🔔 Alertas

Foi cadastrada uma regra de alerta de saúde com um grupo de ações associado.

O funcionamento da notificação por e-mail ainda precisa ser validado, pois o teste apresentou estado Unknown.

### 🔐 Segurança

| Medida | Finalidade |
| :--- | :--- |
| HTTPS obrigatório | Proteção da comunicação web |
| TLS mínimo 1.2 | Segurança das conexões |
| SSL no PostgreSQL | Criptografia da conexão com o banco |
| Variáveis de ambiente | Proteção de credenciais |
| CORS e CSRF | Controle e proteção das requisições |
| Autenticação | Controle de acesso à aplicação |
| Depuração remota desabilitada | Redução da exposição do ambiente |

### 📈 Escalabilidade

A aplicação utiliza um App Service Plan Basic B1, com possibilidade de expansão manual da infraestrutura.

| Característica | Configuração |
| :--- | :--- |
| Plano | Basic B1 |
| Sistema operacional | Linux |
| Região | Brazil South |
| Instâncias atuais | 1 |
| Limite de instâncias | 3 |
| Escalonamento horizontal | Manual |
| Escalonamento automático | Não habilitado no plano atual |

A escalabilidade horizontal permite distribuir a demanda entre mais instâncias, enquanto a escalabilidade vertical permite ampliar os recursos computacionais por meio da alteração do plano contratado.

### Testes de disponibilidade

| Teste | Requisições | Respostas HTTP 200 | Erros |
| :--- | :---: | :---: | :---: |
| Sequencial | 10 | 10 | 0 |
| Concorrente | 10 | 10 | 0 |

Os testes demonstraram disponibilidade do endpoint de saúde durante as verificações realizadas.

Esses resultados não representam uma validação completa da capacidade de atendimento para dez vezes mais usuários.

### Banco de dados e recuperação

O banco de dados utiliza PostgreSQL gerenciado pelo Neon.

A política de backup, a retenção e os procedimentos de restauração ainda precisam ser confirmados pelo responsável pelo serviço.

Recomenda-se realizar testes de recuperação em ambiente isolado, preservando os dados de produção.

---

## 08. Estimativa de custos

A estimativa foi elaborada utilizando a calculadora oficial de preços da Microsoft Azure, considerando a região Brazil South e o plano Basic B1.

**Data da simulação:** 23/11/2026.

### Configuração utilizada

| Recurso | Especificação |
| :--- | :--- |
| Plano | Basic B1 |
| Sistema operacional | Linux |
| Processamento | 1 núcleo |
| Memória RAM | 1,75 GB |
| Armazenamento | 10 GB |
| Horas mensais | 730 horas |
| Valor por hora | US$ 0,020 |

### Comparação de cenários

| Característica | Cenário atual | Cenário de expansão |
| :--- | :---: | :---: |
| Instâncias | 1 | 3 |
| Horas mensais por instância | 730 | 730 |
| Custo mensal | US$ 14,60 | US$ 43,80 |
| Custo anual | US$ 175,20 | US$ 525,60 |

### Cenário atual

O ambiente utiliza uma instância do App Service Plan Basic B1, com custo mensal estimado de **US$ 14,60**.

### Cenário de expansão

Para um cenário de crescimento da demanda, considerando dez vezes mais usuários, foi simulada a expansão horizontal para três instâncias, com custo mensal estimado de **US$ 43,80**.

A ampliação representa uma possibilidade de dimensionamento da infraestrutura, sendo necessários testes de carga para determinar a capacidade efetiva de atendimento.

### Considerações sobre os custos

Os valores apresentados correspondem exclusivamente ao App Service Plan, que é compartilhado por duas aplicações.

Os custos de outros serviços, incluindo Neon, Static Web Apps, Cloudinary, tráfego de rede e monitoramento, não foram consolidados nesta estimativa.

[Consultar calculadora de preços Azure](https://azure.microsoft.com/pt-br/pricing/calculator/)

---

## 🔗 Repositórios do projeto

| Repositório | Acesso |
| :--- | :---: |
| Backend — Django | [GitHub Backend](https://github.com/Luc4s22/Projeto-Integrador-TIME1) |
| Frontend | [GitHub Frontend](https://github.com/Luc4s22/caminh-do-vale-front) |
| Automação CI/CD | [GitHub Actions](https://github.com/Luc4s22/Projeto-Integrador-TIME1/actions) |

---

## 📌 Melhorias futuras

Como continuidade do desenvolvimento e aprimoramento da infraestrutura, destacam-se:

- Validação da implantação declarativa pelo Azure Bicep em ambiente isolado.
- Realização de testes de carga mais abrangentes.
- Consolidação dos custos de todos os serviços utilizados.
- Validação das políticas de backup e recuperação.
- Aprimoramento do monitoramento e das notificações.
- Validação do armazenamento externo de imagens.
- Confirmação do processo de publicação automática do frontend.

---

## 📚 Referências

A documentação do projeto foi fundamentada nas documentações oficiais das tecnologias e serviços utilizados.

| Plataforma | Documentação |
| :--- | :--- |
| Microsoft Azure | [Documentação oficial](https://learn.microsoft.com/pt-br/azure/) |
| Azure App Service | [Hospedagem de aplicações](https://learn.microsoft.com/pt-br/azure/app-service/) |
| Azure Static Web Apps | [Aplicações web estáticas](https://learn.microsoft.com/pt-br/azure/static-web-apps/) |
| Azure Bicep | [Infraestrutura como código](https://learn.microsoft.com/pt-br/azure/azure-resource-manager/bicep/) |
| GitHub Actions | [Integração e entrega contínua](https://docs.github.com/pt/actions) |
| Django | [Documentação do framework](https://docs.djangoproject.com/) |
| Django REST Framework | [Documentação da API REST](https://www.django-rest-framework.org/) |
| PostgreSQL | [Documentação do banco de dados](https://www.postgresql.org/docs/) |
| Neon | [PostgreSQL gerenciado](https://neon.com/docs) |
| Azure Pricing Calculator | [Estimativa de custos](https://azure.microsoft.com/pt-br/pricing/calculator/) |

---

## 📝 Considerações finais

O projeto Caminho do Vale demonstra a integração entre Internet das Coisas, desenvolvimento de software e computação em nuvem, aplicados ao monitoramento do transporte de frutas.

A publicação da aplicação na Microsoft Azure, a utilização de um banco de dados gerenciado e a automação da implantação por meio do GitHub Actions representam os principais resultados alcançados nesta etapa do projeto.

A adoção de práticas de segurança, versionamento, monitoramento e infraestrutura como código contribui para a organização, manutenção e evolução da solução.

---

<div align="center">

### 🍇 Caminho do Vale

**Tecnologia, inovação e monitoramento inteligente.**

Desenvolvido pela equipe Caminho do Vale.

**Faculdade SENAC Pernambuco | ADS047 | 2026**

</div>
