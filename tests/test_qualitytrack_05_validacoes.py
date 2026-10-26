"""Teste tecnico individual do cenario 05_validacoes do QualityTrack.

Utiliza contas de teste e banco SQLite temporario, separado da producao.
Nao registra avaliacoes de participantes externos.
Execute: python -m unittest discover -s tests -p 'test_qualitytrack_05_validacoes.py' -v
"""
import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta

from werkzeug.security import generate_password_hash
from app import create_app
from storage import get_db, init_db


class QualityTrackCenarioTeste(unittest.TestCase):
    CONTAS = (
        ('Marina Costa - Consulta', 'sim01@exemplo.test', 'consulta'),
        ('Lucas Ferreira - Analista', 'sim02@exemplo.test', 'analista'),
        ('Renata Almeida - Gestor', 'sim03@exemplo.test', 'gestor'),
        ('Paulo Ribeiro - Admin', 'sim04@exemplo.test', 'admin'),
        ('Juliana Martins - Analista iniciante', 'sim05@exemplo.test', 'analista'),
    )
    SENHA = 'Senha-Somente-Teste-2026!'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='qualitytrack_teste_')
        self.app = create_app({
            'TESTING': True,
            'DATABASE': str(Path(self.tmp.name) / 'dados_teste.sqlite3'),
            'SECRET_KEY': 'chave-apenas-para-testes-integracao',
            'SESSION_COOKIE_SECURE': False,  # test_client nao utiliza HTTPS real
        })
        self.ids = {}
        with self.app.app_context():
            init_db()
            db = get_db()
            for nome, email, perfil in self.CONTAS:
                cursor = db.execute(
                    'INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)',
                    (nome, email, generate_password_hash(self.SENHA), perfil),
                )
                self.ids[perfil if email != 'sim05@exemplo.test' else 'analista2'] = cursor.lastrowid
            db.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def sql_one(self, sql, params=()):
        with self.app.app_context():
            row = get_db().execute(sql, params).fetchone()
            return dict(row) if row else None

    def csrf(self):
        with self.client.session_transaction() as sess:
            return sess.get('csrf_token')

    def fazer_login(self, numero):
        self.client.get('/login')
        resp = self.client.post('/login', data={
            'email': f'sim{numero:02d}@exemplo.test',
            'password': self.SENHA,
            'csrf_token': self.csrf(),
        })
        self.assertEqual(resp.status_code, 302, 'Login com credenciais de teste deve ser aceito')

    def postar(self, rota, dados, esperado=302):
        resp = self.client.post(rota, data={**dados, 'csrf_token': self.csrf()})
        self.assertEqual(resp.status_code, esperado, f'{rota}: HTTP inesperado: {resp.status_code}')
        return resp

    def nova_nc(self, titulo='NC para teste de integracao', responsavel='analista'):
        self.postar('/ocorrencias/nova', {
            'title': titulo,
            'description': 'Verificacao tecnica do fluxo de cadastro com dados de teste.',
            'sector_id': '1',
            'assigned_user_id': str(self.ids[responsavel]),
            'origin': 'Interna',
            'severity': 'Média',
        })
        item = self.sql_one('SELECT * FROM nonconformities ORDER BY id DESC LIMIT 1')
        self.assertIsNotNone(item, 'NC deveria ter sido cadastrada')
        return item['id']

    def nova_acao(self, nc_id, responsavel='analista'):
        prazo = (date.today() + timedelta(days=7)).isoformat()
        self.postar(f'/ocorrencias/{nc_id}/acao', {
            'description': 'Revisar procedimento de inspecao e registrar a orientacao de teste.',
            'assigned_user_id': str(self.ids[responsavel]),
            'due_date': prazo,
        })
        acao = self.sql_one('SELECT * FROM corrective_actions WHERE nc_id=? ORDER BY id DESC LIMIT 1', (nc_id,))
        self.assertIsNotNone(acao)
        return acao['id']

    def test_05_perfil_analista_iniciante_erros_e_csrf(self):
        """SIM05 Analista iniciante: credenciais, campos invalidos, CSRF e filtros."""
        self.client.get('/login')
        resposta = self.client.post('/login', data={'email':'sim05@exemplo.test','password':'senha-errada','csrf_token':self.csrf()})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.client.get('/').status_code, 302, 'Nao pode acessar painel apos login invalido')
        self.fazer_login(5)
        self.assertEqual(self.client.get('/ocorrencias?status=Aberta&sector=1').status_code, 200)
        resposta = self.postar('/ocorrencias/nova', {
            'title': 'NC', 'description': 'curta', 'sector_id': '1',
            'assigned_user_id': str(self.ids['analista2']), 'origin':'INVALIDA', 'severity':'Baixa',
        }, esperado=200)
        self.assertEqual(self.sql_one('SELECT COUNT(*) AS n FROM nonconformities')['n'], 0)
        resposta = self.client.post('/ocorrencias/nova', data={'title':'Tentativa sem token'})
        self.assertEqual(resposta.status_code, 400, 'Formulario sem CSRF deve ser rejeitado')
        nc_id = self.nova_nc('NC valida analista iniciante', responsavel='analista2')
        self.assertEqual(self.sql_one('SELECT id FROM nonconformities WHERE id=?', (nc_id,))['id'], nc_id)
        self.assertEqual(self.client.get('/usuarios').status_code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
