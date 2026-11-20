# Uso de inteligência artificial — documentação de segurança

## 1. Objetivo

Registrar de forma transparente a participação de ferramentas de IA no desenvolvimento e na documentação dos controles de segurança do projeto **Caminho do Vale**, distinguindo assistência automatizada, validação humana e evidências verificáveis.

**Estado do registro:** este arquivo foi preparado a partir da versão do código fornecida em 19/11/2026 e da divisão de tarefas da mesma data. O arquivo ZIP não contém o histórico `.git`, os prompts originais nem o documento de apoio `aula-seguranca-codigo.md`. As entradas que dependem desses materiais ficam explicitamente **pendentes de confirmação**, em vez de receber exemplos apresentados como fatos.

## 2. Áreas em que a IA foi utilizada ou deve ser documentada

O documento de tarefas informa que o registro precisa contemplar auxílio na **geração de código, criação de testes, revisão e documentação**. O quadro abaixo distingue o que está disponível no projeto da contribuição específica ainda não comprovada.

| Área | Artefatos existentes | Contribuição da IA e validação humana a confirmar |
| --- | --- | --- |
| Código do 2FA | `usuarios/dois_fatores.py`, `usuarios/views.py`, `usuarios/models.py` | **Pendente:** quais trechos foram propostos por IA, quem revisou, o que alterou e por quê. |
| Código de autorização IDOR | `usuarios/acesso.py`, `transporte/views.py`, `iot/views.py`, `alertas/views.py`, `dominio/views.py` | **Pendente:** alterações humanas após sugestões da IA, especialmente nos filtros e no tratamento de 403/404. |
| Testes | `usuarios/test_2fa.py`, `usuarios/test_idor.py`, `usuarios/test_idor_cadastros.py`, `seguranca/testes/` | **Pendente:** identificação dos testes sugeridos por IA e das correções efetuadas pela equipe. |
| Revisão | Código, modelo de ameaças e logs de teste | **Pendente:** observações reais das revisões, erros detectados e decisões tomadas pelos integrantes. |
| Documentação | `seguranca/README.md`, `seguranca/modelo-ameacas.md`, este arquivo | A estrutura e redação inicial dos três documentos de segurança foram auxiliadas por ChatGPT em 19/11/2026, com base no PDF de tarefas e na leitura dos arquivos do projeto; a validação e aprovação finais são da equipe. |

A revisão do código existente para redigir a documentação **não equivale a comprovar que a IA escreveu aquele código**.

## 3. Revisões humanas e alterações no material produzido por IA

Para cada contribuição relevante, preencher com evidências reais antes da entrega:

| Componente/PR | Sugestão inicial da IA | Ajuste ou rejeição realizado por integrante | Como foi verificado | Responsável |
| --- | --- | --- | --- | --- |
| 2FA e recuperação | **A confirmar** | **A confirmar** | Testes e PR correspondente, a identificar | **A confirmar** |
| Controle IDOR | **A confirmar** | **A confirmar** | Testes e PR correspondente, a identificar | **A confirmar** |
| Scripts de teste | **A confirmar** | **A confirmar** | Saída dos testes e commit, a identificar | **A confirmar** |
| Documentação de segurança | Organização/redação assistidas por ChatGPT em 19/11/2026 | **Revisão da equipe pendente** | Conferência com PDF, código, evidências e guia externo | Lucas (documentação) |

Não registrar uma revisão como concluída sem indicação de quem a realizou e do que foi mudado.

## 4. Principais prompts usados

**Prompts originais do desenvolvimento:** não foram fornecidos com o ZIP. Solicitar à equipe os textos ou links dos diálogos originais e registrar aqui apenas os que puderem ser comprovados, acompanhados da finalidade e da decisão humana.

**Solicitação documentada nesta etapa (19/11/2026):** a equipe solicitou comparar o projeto com o PDF de tarefas de documentação de segurança e, em seguida, preparar os três arquivos Markdown faltantes. Esta é uma descrição da solicitação desta etapa, **não** uma transcrição literal de prompts antigos nem evidência sobre a geração do backend.

| Data | Prompt ou resumo fiel da solicitação | Objetivo | Resultado conferido por |
| --- | --- | --- | --- |
| 19/11/2026 | Comparar o ZIP do projeto com o documento `Tarefas do Lucas — documentação de segurança.pdf` e produzir os documentos faltantes com base no código real. | Identificar pendências e redigir `README.md`, `uso-de-ia.md`, `modelo-ameacas.md`. | **Revisão final da equipe pendente** |
| **A preencher** | **Prompt original de criação dos controles** | **A preencher** | **A preencher** |
| **A preencher** | **Prompt original de geração/revisão dos testes** | **A preencher** | **A preencher** |

## 5. Commits de 02/10 com coautoria do Claude

A divisão de tarefas informa expressamente que **existem commits de 02/10 com coautoria do Claude** e exige mencioná-los e explicar o que fizeram. **Não foi possível conferir hash, ano, mensagem, arquivos alterados ou a linha `Co-authored-by`**, pois o ZIP do projeto não traz metadados Git.

Para obter informações verificáveis, dentro de um clone com histórico Git execute:

```powershell
git log --all --since='2026-10-02 00:00:00' --until='2026-10-03 00:00:00' --format='%H%n%ad%n%s%n%b%n---' --date=iso
```

Se a data de 02/10 indicada pelo responsável for de outro ano, ajuste o intervalo de datas. Para conferir o conteúdo de um commit identificado:

```powershell
git show --stat <hash-do-commit>
git show <hash-do-commit>
```

Depois, substituir este quadro pelos dados comprovados:

| Hash do commit | Data | Mensagem / contribuição do Claude | Arquivos e funcionalidade alterados | Revisão humana |
| --- | --- | --- | --- | --- |
| **Pendente de consulta ao Git** | 02/10 (ano a confirmar) | **A confirmar a partir do commit** | **A confirmar com `git show`** | **A confirmar com o responsável** |

**Importante:** a menção aos commits é exigência do documento de tarefas; não declarar coautoria de um commit específico nem atribuir correções ao Claude sem verificar o histórico.

## 6. Limitações e responsabilidade

Respostas de IA podem conter sugestões incompletas, erros de segurança ou suposições sobre requisitos. A equipe precisa conferir os controles no código, revisar os testes e validar o funcionamento em ambiente autorizado. Não incluir em prompts compartilhados senhas, chaves de dispositivos, segredos TOTP, tokens ou `.env`. Evidências de teste não podem ser simuladas.

**Checklist de validação antes da entrega**

- [ ] Obter histórico real de 02/10 e identificar os commits com coautoria do Claude.
- [ ] Identificar os principais prompts efetivamente utilizados e sua finalidade.
- [ ] Registrar modificações humanas concretas e os nomes dos revisores.
- [ ] Conferir nomes dos arquivos, links, commits e os resultados dos testes.
- [ ] Revisar o texto com Wendell e demais integrantes envolvidos.
