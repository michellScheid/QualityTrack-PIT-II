"""Testes automatizados do MVP: executar após instalar requirements.txt.

Comando: python -m unittest discover -s tests -v
"""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from werkzeug.security import generate_password_hash
from app import create_app
from storage import init_db, get_db

class QualityTrackFlowTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.dbfile = str(Path(self.tempdir.name) / 'test.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.dbfile, 'SECRET_KEY': 'test-key-local'})
        with self.app.app_context():
            init_db()
            db = get_db()
            db.execute('INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)',
                       ('Teste Admin', 'admin@exemplo.test', generate_password_hash('senha-segura-123'), 'admin'))
            db.execute('INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)',
                       ('Consulta', 'consulta@exemplo.test', generate_password_hash('senha-consulta-123'), 'consulta'))
            db.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def token(self):
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            return sess['csrf_token']

    def login(self, email='admin@exemplo.test', password='senha-segura-123'):
        response = self.client.post('/login', data={'email':email, 'password':password, 'csrf_token':self.token()})
        self.assertEqual(response.status_code, 302)
        return response

    def post(self, path, data):
        with self.client.session_transaction() as sess:
            token=sess['csrf_token']
        return self.client.post(path, data={**data, 'csrf_token':token}, follow_redirects=True)

    def test_login_senha_incorreta(self):
        response = self.client.post('/login', data={'email':'admin@exemplo.test', 'password':'errada', 'csrf_token':self.token()})
        self.assertEqual(response.status_code, 200)
        self.assertIn('inválidos'.encode('utf-8'), response.data)

    def test_cadastro_e_fluxo_ate_encerramento(self):
        self.login()
        response = self.post('/ocorrencias/nova', {
            'title': 'Peça fora da tolerância',
            'description': 'Diâmetro excede limite especificado na medição interna.',
            'sector_id': '1', 'assigned_user_id': '1', 'origin':'Interna', 'severity':'Alta'
        })
        self.assertEqual(response.status_code,200)
        with self.app.app_context():
            nc_id=get_db().execute('SELECT id FROM nonconformities').fetchone()['id']
        self.post(f'/ocorrencias/{nc_id}/acao', {
            'description':'Rever ajuste de máquina e medir novamente', 'assigned_user_id':'1', 'due_date':'2026-12-01'
        })
        result=self.post(f'/ocorrencias/{nc_id}/status',{'status':'Aguardando verificação'})
        self.assertIn('Conclua todas'.encode('utf-8'),result.data)
        with self.app.app_context():
            action_id=get_db().execute('SELECT id FROM corrective_actions').fetchone()['id']
        self.post(f'/acoes/{action_id}/status',{'status':'Concluída'})
        self.post(f'/ocorrencias/{nc_id}/status',{'status':'Aguardando verificação'})
        self.post(f'/ocorrencias/{nc_id}/verificar',{'verification_result':'Medição repetida em cinco peças e aprovada.'})
        with self.app.app_context():
            nc=get_db().execute('SELECT status,verification_result FROM nonconformities WHERE id=?',(nc_id,)).fetchone()
            self.assertEqual(nc['status'],'Encerrada')
            self.assertTrue(nc['verification_result'])

    def test_consulta_nao_pode_criar_ocorrencias(self):
        self.login('consulta@exemplo.test','senha-consulta-123')
        response=self.client.get('/ocorrencias/nova')
        self.assertEqual(response.status_code,403)

    def test_formulario_sem_csrf_e_rejeitado(self):
        self.login()
        response=self.client.post('/ocorrencias/nova', data={'title':'Teste'})
        self.assertEqual(response.status_code,400)

if __name__=='__main__':
    unittest.main()
