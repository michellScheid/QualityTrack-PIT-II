# QualityTrack — Dicionário de dados (versão 1.0)

O banco usa **SQLite** com integridade referencial ligada por `PRAGMA foreign_keys=ON`. Esquema executável em `schema.sql`.

| Tabela | Campo-chave | Finalidade | Relacionamentos |
|---|---|---|---|
| `users` | `id` (INTEGER, PK) | Nome, e-mail único, hash da senha, perfil e status do usuário | Referenciada por ocorrências, ações e histórico |
| `sectors` | `id` (INTEGER, PK) | Setor de origem do desvio | 1:N com ocorrências |
| `nonconformities` | `id` (INTEGER, PK) | Ocorrência, gravidade, origem, causa, status e datas | `sector_id`, `assigned_user_id`, `created_by`, `verifier_id` |
| `corrective_actions` | `id` (INTEGER, PK) | Ação, responsável, prazo, status e conclusão | `nc_id`, `assigned_user_id` |
| `audit_history` | `id` (INTEGER, PK) | Eventos e alterações relevantes de uma NC | `nc_id`, `actor_id` |

## Campos e regras essenciais

- `users.email`: `TEXT NOT NULL UNIQUE`, usado como identificador de login.
- `users.password_hash`: `TEXT NOT NULL`, hash gerado via Werkzeug (sem guardar senha em texto puro).
- `users.role`: um de `admin`, `analista`, `gestor`, `consulta`.
- `nonconformities.origin`: `Interna`, `Fornecedor`, `Cliente` ou `Auditoria`.
- `nonconformities.severity`: `Baixa`, `Média`, `Alta`, `Crítica`.
- `nonconformities.status`: `Aberta`, `Em análise`, `Em tratamento`, `Aguardando verificação`, `Encerrada`.
- `corrective_actions.status`: `Pendente`, `Em andamento`, `Concluída`.
- `nonconformities.closed_at`: só é preenchido no encerramento mediante registro da verificação de eficácia.
- `corrective_actions.completed_at`: preenchido quando a ação for concluída.
- `audit_history`: conserva o tipo de alteração, autoria e momento do registro.

## Cardinalidades

- Um setor pode conter várias ocorrências; cada ocorrência pertence a um setor.
- Uma ocorrência pode conter várias ações e eventos de histórico.
- Cada ação possui exatamente um responsável ativo no momento do cadastro.

## Observação acadêmica

O modelo documenta uma implementação **MVP**. Para uso empresarial, serão necessárias políticas adicionais de segurança, retenção, backup, conformidade e escala.
