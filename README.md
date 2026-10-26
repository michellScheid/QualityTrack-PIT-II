git add README.md# QualityTrack — Sistema de Gestão de Não Conformidades

**Projeto Integrador Transdisciplinar em Engenharia de Software II · Cruzeiro do Sul Virtual · 2026**  
**Aluno:** Michell Scheid da Silva ·   
**Professora:** Katia Alves Bezerra

## 1. Apresentação

O **QualityTrack** é um protótipo acadêmico de sistema web para o registro, acompanhamento e tratamento de não conformidades. Centraliza ocorrências, responsáveis, prazos, ações corretivas, verificação de eficácia e histórico de alterações, apoiando a rastreabilidade das atividades de qualidade.

**Aplicação online:** https://michellscheid.pythonanywhere.com  
**Repositório de código:** https://github.com/michellScheid/QualityTrack-PIT-II

> **Ambiente demonstrativo.** Utilize somente dados fictícios. O sistema não foi homologado para uso industrial em produção ou para armazenamento de informações sensíveis.

## 2. Funcionalidades implementadas

- Autenticação e controle de permissões para os perfis **Admin, Gestor, Analista e Consulta**.
- Cadastro, edição, consulta e filtros de não conformidades.
- Registro de ações corretivas com responsável, prazo e status (**Pendente**, **Em andamento**, **Concluída**).
- Acompanhamento do fluxo das ocorrências, incluindo **Aguardando verificação**.
- Verificação de eficácia e encerramento por usuário autorizado, respeitando as regras de conclusão das ações.
- Painel de indicadores e histórico das alterações relevantes.
- Persistência dos registros em banco de dados SQLite.

## 3. Tecnologias e arquitetura

| Camada | Tecnologia |
|---|---|
| Interface | HTML, CSS e templates Jinja2 |
| Back-end | Python e Flask |
| Banco de dados | SQLite |
| Hospedagem | PythonAnywhere |
| Versionamento | Git e GitHub |

A implementação separa rotas e regras da aplicação (`app.py`), operações de persistência (`storage.py`), definição do banco (`schema.sql`), telas (`templates/`) e estilos (`static/`).

## 4. Como acessar a demonstração online

1. Acesse **https://michellscheid.pythonanywhere.com**.
2. Entre com as credenciais individuais fornecidas pelo responsável pelos testes.
3. Use somente registros demonstrativos durante a avaliação.

**Segurança:** não publique senhas, chaves, bancos de dados locais ou registros de terceiros neste repositório. O arquivo `.gitignore` reduz o risco de inclusão acidental desses arquivos, mas não substitui a revisão antes de cada envio.

## 5. Como executar localmente no Windows

**Pré-requisito:** Python 3.10 ou mais recente e acesso à internet para instalar as dependências.

1. Clone ou baixe este repositório e abra a pasta do projeto.
2. Execute `INICIAR_QUALITYTRACK_WINDOWS.bat` e siga as instruções do terminal para instalar as dependências e criar o primeiro administrador, caso ainda não exista.
3. Abra **http://127.0.0.1:5000** no navegador e faça login.
4. Para encerrar o servidor local, pressione `Ctrl + C` no terminal.

Também é possível instalar as dependências manualmente usando `python -m pip install -r requirements.txt`. Consulte `LEIA_PRIMEIRO.txt` e `INSTRUCOES.txt` para orientações adicionais.

## 6. Estrutura do repositório

```text
QualityTrack/
├── app.py                         # Aplicação, rotas e regras
├── storage.py                     # Persistência SQLite
├── schema.sql                     # Estrutura do banco
├── requirements.txt               # Dependências Python
├── templates/                     # Interface HTML
├── static/                        # Estilos CSS
├── docs/                          # Documentação e diagramas UML
├── tests/                         # Testes automatizados
├── INICIAR_QUALITYTRACK_WINDOWS.bat
├── INSTRUCOES.txt
└── LEIA_PRIMEIRO.txt
```

A pasta `docs/uml/` contém os diagramas de casos de uso, classes, sequência e entidade-relacionamento. Os demais documentos em `docs/` incluem dicionário de dados, escopo e rastreabilidade e materiais de teste.

## 7. Testes e resultados

Na versão publicada em outubro de 2026, foram executados **13 testes automatizados em conjunto, com 13 aprovações e nenhuma falha**:

| Grupo | Arquivos | Quantidade |
|---|---|---:|
| Fluxos básicos | `tests/test_fluxo_basico.py` | 4 |
| Regressão QT-001 | `tests/test_regressao_qt001.py` | 4 |
| Cinco cenários de perfis e validações | `tests/test_qualitytrack_*.py` | 5 |
| **Total** | | **13** |

Com o ambiente virtual ativado e na raiz do repositório, execute:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Os testes utilizam ambientes de teste isolados, de acordo com sua implementação. O resultado da bateria automatizada **não substitui** as cinco avaliações humanas previstas na atividade acadêmica.

### Correção QT-001 — Consistência de status

Foi reproduzida uma inconsistência: ao reabrir uma ação corretiva, a ocorrência podia permanecer em **Aguardando verificação**. A regra foi ajustada para retornar a ocorrência a **Em tratamento**, preservando a coerência do fluxo.

- **Antes da correção:** 2 de 4 testes de regressão aprovados.
- **Depois da correção:** 4 de 4 testes de regressão aprovados.
- **Validação adicional:** comportamento confirmado na interface online.

O código e os testes de regressão estão versionados neste repositório.

## 8. Documentação e avaliação acadêmica

A documentação técnica, os modelos UML e os testes estão organizados nas pastas `docs/` e `tests/`. O Projeto Integrador inclui ainda um relatório de qualidade e o manual do usuário, elaborados como documentos complementares.

As avaliações de **cinco participantes reais** e os vídeos demonstrativos serão incorporados aos documentos acadêmicos após sua realização. Resultados ainda não coletados não são apresentados como concluídos.

## 9. Limitações e uso responsável

O QualityTrack é um **MVP acadêmico** com dados demonstrativos. Antes de qualquer adoção real, seriam necessárias avaliações adicionais de segurança, privacidade, disponibilidade, rotinas de backup, manutenção e adequação às políticas da organização.
