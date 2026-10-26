PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL CHECK(length(trim(name))>=2),
 email TEXT NOT NULL UNIQUE COLLATE NOCASE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','analista','gestor','consulta')),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sectors (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS nonconformities (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 description TEXT NOT NULL,
 sector_id INTEGER NOT NULL REFERENCES sectors(id),
 origin TEXT NOT NULL CHECK(origin IN ('Interna','Fornecedor','Cliente','Auditoria')),
 severity TEXT NOT NULL CHECK(severity IN ('Baixa','Média','Alta','Crítica')),
 assigned_user_id INTEGER NOT NULL REFERENCES users(id),
 created_by INTEGER NOT NULL REFERENCES users(id),
 root_cause TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'Aberta' CHECK(status IN ('Aberta','Em análise','Em tratamento','Aguardando verificação','Encerrada')),
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 updated_at TEXT NOT NULL DEFAULT (datetime('now')),
 closed_at TEXT,
 verifier_id INTEGER REFERENCES users(id),
 verification_result TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS corrective_actions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 nc_id INTEGER NOT NULL REFERENCES nonconformities(id) ON DELETE CASCADE,
 description TEXT NOT NULL,
 assigned_user_id INTEGER NOT NULL REFERENCES users(id),
 due_date TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'Pendente' CHECK(status IN ('Pendente','Em andamento','Concluída')),
 completed_at TEXT,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS audit_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 nc_id INTEGER NOT NULL REFERENCES nonconformities(id) ON DELETE CASCADE,
 actor_id INTEGER NOT NULL REFERENCES users(id),
 event TEXT NOT NULL,
 details TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nc_status ON nonconformities(status);
CREATE INDEX IF NOT EXISTS idx_nc_sector ON nonconformities(sector_id);
CREATE INDEX IF NOT EXISTS idx_actions_nc ON corrective_actions(nc_id);
