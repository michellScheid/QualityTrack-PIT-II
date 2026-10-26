"""Regressões QT-001: reabrir ação não pode deixar NC aguardando eficácia."""
import tempfile
import unittest
from pathlib import Path
from werkzeug.security import generate_password_hash
from app import create_app
from storage import get_db, init_db

class StatusConsistencyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({'TESTING':True, 'DATABASE':str(Path(self.tmp.name)/'test.sqlite3'),
                               'SECRET_KEY':'chave-de-teste-nao-publica'})
        with self.app.app_context():
            init_db()
            db=get_db()
            db.execute('INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)',
                       ('Admin Teste','admin@qt.test',generate_password_hash('teste12345678'),'admin'))
            db.commit()
        self.client=self.app.test_client()
        self.client.get('/login')
        with self.client.session_transaction() as session:
            csrf=session['csrf_token']
        self.client.post('/login',data={'csrf_token':csrf,'email':'admin@qt.test','password':'teste12345678'})

    def tearDown(self):
        self.tmp.cleanup()

    def post(self,path,data):
        with self.client.session_transaction() as session:
            csrf=session['csrf_token']
        return self.client.post(path,data={**data,'csrf_token':csrf},follow_redirects=True)

    def cria_ocorrencia_e_acao(self):
        response=self.post('/ocorrencias/nova',{
            'title':'Teste de consistência NC',
            'description':'Registro fictício de validação do status da não conformidade',
            'sector_id':'1','assigned_user_id':'1','origin':'Interna','severity':'Média'
        })
        self.assertEqual(response.status_code,200)
        with self.app.app_context():
            nc_id=get_db().execute('SELECT id FROM nonconformities ORDER BY id DESC').fetchone()['id']
        response=self.post(f'/ocorrencias/{nc_id}/acao',{
            'description':'Revisar o processo de inspeção','assigned_user_id':'1','due_date':'2026-12-01'
        })
        self.assertEqual(response.status_code,200)
        with self.app.app_context():
            action_id=get_db().execute('SELECT id FROM corrective_actions ORDER BY id DESC').fetchone()['id']
        return nc_id,action_id

    def test_acao_reaberta_retorna_ocorrencia_para_tratamento(self):
        nc_id, action_id=self.cria_ocorrencia_e_acao()
        self.post(f'/acoes/{action_id}/status',{'status':'Concluída'})
        self.post(f'/ocorrencias/{nc_id}/status',{'status':'Aguardando verificação'})
        self.post(f'/acoes/{action_id}/status',{'status':'Em andamento'})
        with self.app.app_context():
            db=get_db()
            self.assertEqual(db.execute('SELECT status FROM nonconformities WHERE id=?',(nc_id,)).fetchone()['status'],'Em tratamento')
            self.assertEqual(db.execute('SELECT status FROM corrective_actions WHERE id=?',(action_id,)).fetchone()['status'],'Em andamento')
            history=db.execute("SELECT count(*) AS n FROM audit_history WHERE nc_id=? AND event='Retorno ao tratamento'",(nc_id,)).fetchone()['n']
            self.assertEqual(history,1)

    def test_reabrir_acao_pendente_tambem_retorna_ao_tratamento(self):
        nc_id,action_id=self.cria_ocorrencia_e_acao()
        self.post(f'/acoes/{action_id}/status',{'status':'Concluída'})
        self.post(f'/ocorrencias/{nc_id}/status',{'status':'Aguardando verificação'})
        self.post(f'/acoes/{action_id}/status',{'status':'Pendente'})
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT status FROM nonconformities WHERE id=?',(nc_id,)).fetchone()['status'],'Em tratamento')

    def test_nao_pode_encerrar_com_acao_em_andamento(self):
        nc_id,action_id=self.cria_ocorrencia_e_acao()
        self.post(f'/acoes/{action_id}/status',{'status':'Concluída'})
        self.post(f'/ocorrencias/{nc_id}/status',{'status':'Aguardando verificação'})
        self.post(f'/acoes/{action_id}/status',{'status':'Em andamento'})
        self.post(f'/ocorrencias/{nc_id}/verificar',{'verification_result':'Avaliação fictícia de eficácia com resultado positivo.'})
        with self.app.app_context():
            self.assertNotEqual(get_db().execute('SELECT status FROM nonconformities WHERE id=?',(nc_id,)).fetchone()['status'],'Encerrada')

    def test_repetir_mesmo_status_nao_gera_historico_duplicado(self):
        nc_id,action_id=self.cria_ocorrencia_e_acao()
        self.post(f'/acoes/{action_id}/status',{'status':'Em andamento'})
        with self.app.app_context():
            before=get_db().execute('SELECT count(*) AS n FROM audit_history WHERE nc_id=?',(nc_id,)).fetchone()['n']
        self.post(f'/acoes/{action_id}/status',{'status':'Em andamento'})
        with self.app.app_context():
            after=get_db().execute('SELECT count(*) AS n FROM audit_history WHERE nc_id=?',(nc_id,)).fetchone()['n']
        self.assertEqual(before,after)

if __name__=='__main__': unittest.main()
