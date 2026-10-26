# Escopo, requisitos e rastreabilidade — QualityTrack

**Curso:** Engenharia de Software | **Disciplina:** Projeto Integrador Transdisciplinar em Engenharia de Software II  
**Discente:** Michell Scheid da Silva |   
**Professora:** Katia Alves Bezerra | **Prazo interno:** 10/11/2026  

## Problema e objetivo

Centralizar o registro, tratamento e acompanhamento de não conformidades industriais em sistema web, permitindo designação de responsáveis, ações corretivas, controle de prazos e indicadores.

## Escopo implementável do MVP

- Autenticação e perfis (`admin`, `analista`, `gestor`, `consulta`)
- Cadastro, edição e filtro de não conformidades
- Classificação por setor, origem e gravidade
- Cadastro e atualização de ações corretivas com prazo e responsável
- Histórico de alterações e verificação de eficácia antes do encerramento
- Dashboard: ocorrências totais, abertas, % de ações concluídas no prazo e tempo médio de encerramento

## Fora do escopo da primeira versão

ERP, SAP, envio automático de e-mails, aplicativo móvel nativo, anexos em nuvem, integração com equipamentos, inteligência artificial e hospedagem de produção com alta disponibilidade.

## Rastreabilidade resumida

| Requisito | Local no sistema | Verificação proposta |
|---|---|---|
| RF01 autenticação | `/login` | Credenciais inválidas e válidas |
| RF02 usuários/perfis | `/usuarios` | Acesso restrito a `admin` |
| RF03 cadastro de NC | `/ocorrencias/nova` | Validação dos campos e persistência |
| RF04 edição/consulta | `/ocorrencias/<id>` e `/editar` | Atualização e leitura do registro |
| RF05 classificação | formulário de ocorrência | Apenas valores permitidos |
| RF06 ação corretiva | `/ocorrencias/<id>/acao` | Ação vinculada à NC |
| RF07 responsável/prazo | formulário de ação | Obrigatoriedade de responsável e data |
| RF08 atualização de status | formulários de status | Transição e registro de conclusão |
| RF09 dashboard | `/` | Cálculo a partir do banco |
| RF10 filtros | `/ocorrencias` | Status e setor |
| RF11 histórico | detalhe da NC | Registro de eventos relevantes |
| RF12 exportação | — | Fora do MVP, evolução futura |

## Critérios de encerramento

A ocorrência só poderá ser encerrada após todas as ações vinculadas serem concluídas, status `Aguardando verificação` e avaliação de eficácia de pelo menos 10 caracteres realizada por gestor ou administrador.

## Estado da evidência

A documentação e o código-fonte podem ser verificados neste repositório. Testes realizados com cinco avaliadores, comprovantes de hospedagem e vídeos deverão ser adicionados **apenas depois de sua execução real**.
