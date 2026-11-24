Caminho do Vale
Projeto Integrador — Computação em Nuvem

Sistema de monitoramento IoT das condições de transporte de frutas, desenvolvido como Projeto Integrador. Este README apresenta a aplicação, sua execução local e a documentação da infraestrutura em nuvem.
Identificação acadêmica
Informação	Descrição
Instituição	Faculdade SENAC Pernambuco
Curso	Análise e Desenvolvimento de Sistemas (ADS)
Turma	ADS047
Disciplina / atividade	Projeto Integrador — Computação em Nuvem
Professor	Ronierison Maciel
Projeto	Caminho do Vale


Equipe
Nº	Integrante
01	Anderson Bem
02	Lais Nayara
03	Lucas Mendes
04	Matheus Henrique
05	Wendel Brasiliano
06	Wendell Barboza


Sobre o sistema
O Caminho do Vale centraliza informações de viagens e cargas, leituras de temperatura e umidade, impactos e alertas. A API Django recebe dados dos dispositivos IoT e disponibiliza informações para acompanhamento pelo frontend. O projeto também contempla autenticação, controle de acesso e inspeção final de cargas.
Tecnologias e organização do backend
Diretório	Responsabilidade
piADS04/	Configurações e rotas principais do Django
usuarios/	Autenticação e usuários
dominio/	Cadastros e entidades do domínio
iot/	Dispositivos e telemetria
transporte/	Viagens e acompanhamento de cargas
alertas/	Alertas do sistema
assistente/	Integração do assistente
docs/ e seguranca/	Documentação técnica e segurança
infra/	Templates de infraestrutura Bicep e ARM
.github/workflows/	Automação CI/CD


Execução local
Para executar o projeto localmente, é necessário instalar o Python e as dependências do projeto, configurar as variáveis de ambiente, preparar um banco PostgreSQL de desenvolvimento e aplicar as migrações do Django. Em seguida, iniciar o servidor local.

A documentação da API está disponível pelo Swagger. Recomenda-se utilizar um banco isolado para desenvolvimento e testes.
1. URLs públicas
- Frontend (Azure Static Web Apps): https://icy-desert-0fc71aa10.3.azurestaticapps.net
- Backend (Azure App Service): https://app-caminho-vale-backend-novo-btawcgdkbzayhvc5.brazilsouth-01.azurewebsites.net
- Health Check: https://app-caminho-vale-backend-novo-btawcgdkbzayhvc5.brazilsouth-01.azurewebsites.net/health/
O endpoint /health/ respondeu HTTP 200 nos testes realizados em 23/11/2026.
2. Provedores, serviços e modelos
A solução utiliza nuvem pública multicloud: Microsoft Azure para frontend e backend e Neon para o banco de dados PostgreSQL. Serviços gerenciados reduzem a administração direta de servidores.
Componente	Serviço	Modelo de serviço	Justificativa
Frontend	Azure Static Web Apps	PaaS	Hospedagem gerenciada de aplicação web estática com HTTPS
Backend	Azure App Service (Linux/Python)	PaaS	Execução gerenciada da API Django e integração com deploy automatizado
Banco	Neon PostgreSQL	DBaaS (categoria PaaS)	PostgreSQL gerenciado e conexão criptografada
Pipeline	GitHub Actions	SaaS	Automação de build, testes e publicação
Observabilidade	Azure Monitor / App Service	Serviço gerenciado	Métricas, logs e verificações de integridade
Upload de imagens	Integração Cloudinary prevista no código	Serviço externo gerenciado, não validado em produção	Credenciais e funcionamento ainda precisam ser comprovados


3. Diagrama da arquitetura
Fluxo da aplicação: Usuário → Frontend Azure Static Web Apps → Backend Azure App Service → Banco PostgreSQL Neon.

Fluxo de implantação: GitHub → GitHub Actions → Azure App Service.

Monitoramento: Azure Monitor, logs e Health Check.

O frontend chama a API REST do backend, que acessa o PostgreSQL gerenciado. O repositório do backend utiliza GitHub Actions para validação e publicação na Azure.
4. CI/CD: funcionamento e evidências
Workflow versionado: .github/workflows/main_app-caminho-vale-backend-novo.yml.
1. Alterações são enviadas em branches e Pull Requests.
2. O pipeline executa o job Build e testes Django.
3. Após integração na branch principal (main), executa o job Deploy Azure App Service.
4. A publicação pode ser conferida no endpoint /health/ e na URL pública.
Execuções: https://github.com/Luc4s22/Projeto-Integrador-TIME1/actions

Evidência de 23/11/2026: execução de merge da PR #3 concluída com sucesso; build e testes em 1min59s, deploy em 2min07s e duração total de 4min13s. Avisos de depreciação do Node.js 20 não impediram essa execução.

Evidência adicional: PR #4 integrada à main do repositório Luc4s22, com build e testes em 2min17s, deploy em 2min34s e duração total de 4min55s. Execução do pipeline.

Frontend: https://github.com/Luc4s22/caminh-do-vale-front — o mecanismo exato de publicação automática do frontend precisa ser confirmado no respectivo repositório.
5. Como reproduzir o deploy do zero
Procedimento orientativo. Antes de criar recursos ou aplicar IaC, revisar o workflow, as permissões e os nomes dos recursos. Não aplicar infra/main.bicep diretamente sobre produção sem análise: o arquivo referencia infraestrutura existente/compartilhada.

1. Criar ou selecionar uma assinatura Azure e um grupo de recursos.
2. Provisionar um App Service Plan Linux e um Azure App Service com versão de Python compatível com o projeto; criar um Azure Static Web Apps para o frontend.
3. Criar um banco PostgreSQL gerenciado no Neon, habilitar SSL e obter as credenciais por canal seguro.
4. Configurar no App Service as variáveis de ambiente necessárias (seção 6), incluindo origens confiáveis e parâmetros do banco.
5. Configurar a autenticação e as permissões necessárias ao workflow do GitHub Actions, armazenando segredos somente nas configurações seguras do GitHub/Azure.
6. Revisar o workflow .github/workflows/main_app-caminho-vale-backend-novo.yml e a infraestrutura infra/main.bicep antes de reproduzir a implantação.
7. Executar os comandos Django apropriados ao ambiente (verificações e migrações) de forma controlada, evitando alterações inadvertidas no banco de produção.
8. Abrir uma Pull Request, conferir os testes e integrar na main para acionar o deploy automático do backend.
9. Configurar o frontend para apontar à URL pública da API e publicá-lo pelo processo previsto no repositório do frontend.
10. Habilitar Health Check com caminho /health/, verificar logs, acessar as URLs públicas e validar o funcionamento.
Infraestrutura como código: infra/main.bicep está versionado e foi compilado com sucesso pelo Azure CLI 2.93.0. O template ARM resultante (infra/main.json) foi integrado à main pela PR #4; a aplicação desse template aos recursos de produção não foi comprovada.
6. Variáveis de ambiente (sem valores reais)
As configurações variam entre desenvolvimento e produção. Principais grupos de configuração:
Configuração	Finalidade
Django	Chave secreta, depuração e hosts permitidos
CORS e CSRF	Controle de origens autorizadas
PostgreSQL	Banco, usuário, senha, servidor, porta e SSL
Autenticação	Recuperação de senha e criptografia do segundo fator
Integrações externas	Serviços de IA, e-mail e armazenamento de imagens


O .env.example apresentado foi conferido e não contém senhas nem chaves reais. O .env local não deve ser enviado ao Git. Variáveis opcionais para upload de fotografias (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET) aparecem no código, mas a integração em produção não foi comprovada.

Ambientes: o backend de produção está publicado no Azure e usa Neon. A conexão local ao PostgreSQL Neon com SSL obrigatório foi validada, assim como manage.py check e a ausência de migrações pendentes. Para desenvolvimento isolado, utilizar banco separado de produção.
7. Logs, saúde, segurança e escalabilidade
Logs: no Portal Azure, abrir o App Service app-caminho-vale-backend-novo → Monitoramento → Fluxo de log (Log stream). A conexão com o fluxo foi confirmada (Connected!). A coleta de logs da aplicação está habilitada em File System, com limite de 35 MB e retenção de 7 dias. A geração de registros de requisições no fluxo ainda precisa ser comprovada.

Health Check: no mesmo App Service, acessar Monitoramento → Verificação de saúde e conferir /health/. A aplicação apresentou estado Healthy, e a métrica Health check status mostrou 100 no período consultado.

Alertas: existe uma regra de alerta de saúde e um grupo de ações cadastrado. A notificação por e-mail não foi validada: o teste retornou Unknown.

Segurança verificada: HTTPS obrigatório, TLS mínimo 1.2 e depuração remota desabilitada. Senhas e tokens devem ficar em variáveis seguras do provedor ou segredos do GitHub. Adotar permissões mínimas para usuários e identidades de serviço.

Escalabilidade: App Service Plan Basic B1, com uma instância ativa, escalonamento manual e limite indicado de três instâncias no plano. O escalonamento automático não está habilitado nesse plano. O dimensionamento para mais usuários exige reavaliar processamento, memória, banco e custos.

Testes realizados: 10 requisições sequenciais ao /health/ retornaram HTTP 200; outras 10 requisições concorrentes também retornaram HTTP 200, sem erros. Trata-se de um teste básico do endpoint, não de uma validação de capacidade para dez vezes mais usuários.

Banco e backup: o PostgreSQL está no Neon, mas política de backup, retenção e teste de restauração ainda dependem de comprovação pelo responsável pelo serviço. Recomenda-se verificar a janela de recuperação no painel Neon, manter exportações protegidas conforme a necessidade e testar a restauração em ambiente isolado, sem sobrescrever produção.
8. Estimativa mensal de custos
Simulações realizadas em 23/11/2026 na Calculadora de preços Azure, para Linux, Brazil South, Basic B1 (1 núcleo, 1,75 GB RAM e 10 GB de armazenamento), a US$ 0,020 por hora.
Configuração	Uso atual	Expansão para demanda de 10× usuários
Instâncias B1	1	3
Horas mensais por instância	730	730
Custo mensal App Service	US$ 14,60	US$ 43,80
Custo anual App Service	US$ 175,20	US$ 525,60


O cenário de expansão representa escala horizontal manual, não uma garantia de capacidade para dez vezes mais usuários. Testes de carga representativos devem orientar eventual mudança para planos superiores. O App Service Plan é compartilhado por duas aplicações; o custo é do plano, não de cada aplicação. Os valores acima não incluem custos não confirmados de Static Web Apps, Neon, Cloudinary, tráfego ou monitoramento. Portanto, não representam o total consolidado da solução. As capturas da calculadora comprovam os valores do App Service.
9. Repositórios
- Backend: https://github.com/Luc4s22/Projeto-Integrador-TIME1
- Frontend: https://github.com/Luc4s22/caminh-do-vale-front
10. Pendências e pontos de atenção
- Validar a implantação declarativa pelo Bicep em ambiente isolado; o login na CLI não foi concluído na assinatura correta.
- Realizar testes de carga representativos para o cenário de 10× usuários.
- Confirmar os custos dos demais serviços e consolidar o orçamento.
- Confirmar backups/retenção e procedimento de restauração do Neon.
- Validar armazenamento externo de imagens, caso exigido pelo fluxo da aplicação.
- Confirmar o mecanismo de publicação do frontend.
11. Referências
Documentações oficiais para consulta sobre as tecnologias utilizadas no projeto:
- Microsoft Azure — hospedagem e infraestrutura em nuvem.
- Azure App Service — publicação e gerenciamento do backend.
- Azure Static Web Apps — hospedagem do frontend.
- Azure Bicep — infraestrutura como código.
- GitHub Actions — automação de testes e implantação.
- Django — desenvolvimento do backend.
- Django REST Framework — desenvolvimento da API REST.
- PostgreSQL e Neon — banco de dados em nuvem.
- Calculadora de preços Azure — estimativas de custos.
12. Considerações finais
O projeto Caminho do Vale integra o monitoramento do transporte de frutas com serviços de computação em nuvem. A publicação do frontend e do backend na Azure, a integração com o PostgreSQL e a automação da implantação pelo GitHub Actions representam os principais resultados alcançados nesta etapa do projeto.

Desenvolvido pela equipe Caminho do Vale — Faculdade SENAC Pernambuco, turma ADS047.
