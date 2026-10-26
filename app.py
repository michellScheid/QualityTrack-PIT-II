"""QualityTrack MVP - aplicação acadêmica demonstrativa de gestão de qualidade.

Arquitetura simplificada MVC:
- Model: schema.sql e storage.py
- Controller: rotas e validação neste arquivo
- View: templates/ e static/
"""
import hmac
import os
import re
import secrets
from datetime import date, datetime
from functools import wraps
from pathlib import Path

import click
from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from storage import close_db, get_db, init_db, query, record_history

ORIGINS = ('Interna', 'Fornecedor', 'Cliente', 'Auditoria')
SEVERITIES = ('Baixa', 'Média', 'Alta', 'Crítica')
NC_STATUSES = ('Aberta', 'Em análise', 'Em tratamento', 'Aguardando verificação', 'Encerrada')
ACTION_STATUSES = ('Pendente', 'Em andamento', 'Concluída')
ROLES = ('admin', 'analista', 'gestor', 'consulta')


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('QT_SECRET_KEY') or secrets.token_hex(32),
        DATABASE=os.getenv('QT_DATABASE') or str(Path(__file__).with_name('qualitytrack.sqlite3')),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    app.teardown_appcontext(close_db)

    @app.before_request
    def load_user():
        g.user = query('SELECT * FROM users WHERE id=? AND active=1', (session['user_id'],), one=True) if session.get('user_id') else None
        if g.user is None and session.get('user_id'):
            session.clear()
        if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            expected = session.get('csrf_token', '')
            provided = request.form.get('csrf_token', '')
            if not expected or not hmac.compare_digest(expected, provided):
                abort(400, 'Formulário expirado. Recarregue a página e tente novamente.')

    @app.context_processor
    def globals_for_templates():
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        return {'csrf_token': session['csrf_token'], 'user': g.get('user'), 'today': date.today().isoformat()}

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def handle_client_error(error):
        return render_template('error.html', description=getattr(error,'description','Erro de solicitação.')), error.code

    def login_required(view):
        @wraps(view)
        def inner(*args, **kwargs):
            if not g.user:
                return redirect(url_for('login'))
            return view(*args, **kwargs)
        return inner

    def require_roles(*allowed):
        def wrapper(view):
            @wraps(view)
            @login_required
            def inner(*args, **kwargs):
                if g.user['role'] not in allowed:
                    abort(403, 'Sem permissão para essa operação.')
                return view(*args, **kwargs)
            return inner
        return wrapper

    def valid_user(user_id):
        return query('SELECT id FROM users WHERE id=? AND active=1', (user_id,), one=True)

    def safe_date(value):
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            return None

    @app.route('/login', methods=['GET','POST'])
    def login():
        if g.user:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            email = request.form.get('email','').strip().lower()
            password = request.form.get('password','')
            u = query('SELECT * FROM users WHERE email=? AND active=1', (email,), one=True)
            if u and check_password_hash(u['password_hash'], password):
                session.clear()
                session['user_id'] = u['id']
                session['csrf_token'] = secrets.token_urlsafe(32)
                return redirect(url_for('dashboard'))
            flash('E-mail ou senha inválidos.', 'error')
        return render_template('login.html')

    @app.post('/logout')
    @login_required
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    @login_required
    def dashboard():
        db = get_db()
        stats = dict(db.execute("""
            SELECT COUNT(*) AS total,
            SUM(CASE WHEN status <> 'Encerrada' THEN 1 ELSE 0 END) AS abertas,
            SUM(CASE WHEN status = 'Encerrada' THEN 1 ELSE 0 END) AS encerradas
            FROM nonconformities
        """).fetchone())
        actions = query('SELECT due_date,completed_at,status FROM corrective_actions')
        concluded = [a for a in actions if a['status']=='Concluída']
        ontime = sum(bool(a['completed_at'] and a['completed_at'][:10] <= a['due_date']) for a in concluded)
        stats['ontime_pct'] = round(100*ontime/len(concluded),1) if concluded else None
        closed = query("SELECT created_at,closed_at FROM nonconformities WHERE status='Encerrada' AND closed_at IS NOT NULL")
        intervals = [(datetime.fromisoformat(c['closed_at'])-datetime.fromisoformat(c['created_at'])).total_seconds()/86400 for c in closed]
        stats['mean_days'] = round(sum(intervals)/len(intervals),1) if intervals else None
        stats['overdue'] = sum(a['status']!='Concluída' and a['due_date']<date.today().isoformat() for a in actions)
        by_status = query('SELECT status, COUNT(*) AS total FROM nonconformities GROUP BY status ORDER BY total DESC')
        recent = query('''SELECT n.*, s.name AS sector_name, u.name AS owner_name FROM nonconformities n
                         JOIN sectors s ON s.id=n.sector_id JOIN users u ON u.id=n.assigned_user_id
                         ORDER BY n.id DESC LIMIT 7''')
        return render_template('dashboard.html', stats=stats, by_status=by_status, recent=recent)

    @app.get('/ocorrencias')
    @login_required
    def nc_list():
        filters = {'status':request.args.get('status',''), 'sector':request.args.get('sector','')}
        sql = '''SELECT n.*, s.name AS sector_name, u.name AS owner_name FROM nonconformities n
                 JOIN sectors s ON s.id=n.sector_id JOIN users u ON u.id=n.assigned_user_id WHERE 1=1'''
        args=[]
        if filters['status'] in NC_STATUSES:
            sql += ' AND n.status=?'; args.append(filters['status'])
        if filters['sector'].isdigit():
            sql += ' AND n.sector_id=?'; args.append(int(filters['sector']))
        sql += ' ORDER BY n.id DESC'
        return render_template('nc_list.html', items=query(sql,args), statuses=NC_STATUSES,
                               sectors=query('SELECT * FROM sectors ORDER BY name'), filters=filters)

    @app.route('/ocorrencias/nova', methods=['GET','POST'])
    @require_roles('admin','analista','gestor')
    def nc_create():
        if request.method=='POST':
            title = request.form.get('title','').strip()
            description = request.form.get('description','').strip()
            sector_id = request.form.get('sector_id','')
            assigned_id = request.form.get('assigned_user_id','')
            origin = request.form.get('origin','')
            severity = request.form.get('severity','')
            valid_sector = sector_id.isdigit() and query('SELECT id FROM sectors WHERE id=?',(sector_id,),one=True)
            valid_assigned = assigned_id.isdigit() and valid_user(assigned_id)
            if not (3<=len(title)<=120 and 10<=len(description)<=3000 and valid_sector
                    and valid_assigned and origin in ORIGINS and severity in SEVERITIES):
                flash('Confira os campos obrigatórios, descrições e classificações.','error')
            else:
                db=get_db()
                cur=db.execute('''INSERT INTO nonconformities (title,description,sector_id,origin,severity,assigned_user_id,created_by)
                                  VALUES (?,?,?,?,?,?,?)''',(title,description,int(sector_id),origin,severity,int(assigned_id),g.user['id']))
                record_history(cur.lastrowid,g.user['id'],'Criação','Ocorrência registrada')
                db.commit()
                flash('Não conformidade registrada com sucesso.','success')
                return redirect(url_for('nc_detail',nc_id=cur.lastrowid))
        return render_template('nc_form.html', origins=ORIGINS, severities=SEVERITIES,
                              sectors=query('SELECT * FROM sectors ORDER BY name'),
                              users=query('SELECT id,name FROM users WHERE active=1 ORDER BY name'), editing=False)

    @app.get('/ocorrencias/<int:nc_id>')
    @login_required
    def nc_detail(nc_id):
        nc=query('''SELECT n.*,s.name AS sector_name, u.name AS owner_name FROM nonconformities n
                    JOIN sectors s ON s.id=n.sector_id JOIN users u ON u.id=n.assigned_user_id WHERE n.id=?''',(nc_id,),one=True)
        if not nc: abort(404)
        actions=query('''SELECT a.*,u.name AS owner_name FROM corrective_actions a JOIN users u ON u.id=a.assigned_user_id
                         WHERE a.nc_id=? ORDER BY a.id DESC''',(nc_id,))
        history=query('''SELECT h.*,u.name AS actor_name FROM audit_history h JOIN users u ON u.id=h.actor_id
                         WHERE h.nc_id=? ORDER BY h.id DESC''',(nc_id,))
        return render_template('nc_detail.html',nc=nc,actions=actions,history=history,
                               users=query('SELECT id,name FROM users WHERE active=1 ORDER BY name'),
                               action_statuses=ACTION_STATUSES, status_values=NC_STATUSES)

    @app.route('/ocorrencias/<int:nc_id>/editar', methods=['GET','POST'])
    @require_roles('admin','analista','gestor')
    def nc_edit(nc_id):
        nc=query('SELECT * FROM nonconformities WHERE id=?',(nc_id,),one=True)
        if not nc: abort(404)
        if nc['status']=='Encerrada':
            abort(403,'Ocorrência encerrada não pode ser editada.')
        if request.method=='POST':
            title=request.form.get('title','').strip()
            description=request.form.get('description','').strip()
            sector_id=request.form.get('sector_id','')
            assigned_id=request.form.get('assigned_user_id','')
            origin=request.form.get('origin','')
            severity=request.form.get('severity','')
            root_cause=request.form.get('root_cause','').strip()
            if (not 3<=len(title)<=120 or not 10<=len(description)<=3000 or len(root_cause)>3000
                or not sector_id.isdigit() or not query('SELECT id FROM sectors WHERE id=?',(sector_id,),one=True)
                or not assigned_id.isdigit() or not valid_user(assigned_id)
                or origin not in ORIGINS or severity not in SEVERITIES):
                flash('Confira os valores preenchidos.','error')
            else:
                db=get_db()
                db.execute('''UPDATE nonconformities SET title=?,description=?,sector_id=?,origin=?,severity=?,assigned_user_id=?,
                              root_cause=?,updated_at=datetime('now') WHERE id=?''',
                           (title,description,int(sector_id),origin,severity,int(assigned_id),root_cause,nc_id))
                record_history(nc_id,g.user['id'],'Edição','Campos da ocorrência atualizados')
                db.commit()
                flash('Ocorrência atualizada.','success')
                return redirect(url_for('nc_detail',nc_id=nc_id))
        return render_template('nc_form.html',nc=nc,origins=ORIGINS,severities=SEVERITIES,
                              sectors=query('SELECT * FROM sectors ORDER BY name'),
                              users=query('SELECT id,name FROM users WHERE active=1 ORDER BY name'), editing=True)

    @app.post('/ocorrencias/<int:nc_id>/acao')
    @require_roles('admin','analista','gestor')
    def action_create(nc_id):
        nc=query('SELECT * FROM nonconformities WHERE id=?',(nc_id,),one=True)
        if not nc: abort(404)
        if nc['status']=='Encerrada': abort(403,'Ocorrência encerrada.')
        desc=request.form.get('description','').strip()
        assigned_id=request.form.get('assigned_user_id','')
        due=request.form.get('due_date','')
        if not (5<=len(desc)<=2000 and assigned_id.isdigit() and valid_user(assigned_id) and safe_date(due)):
            flash('Preencha descrição, responsável e prazo válidos.','error')
        else:
            db=get_db()
            db.execute('INSERT INTO corrective_actions(nc_id,description,assigned_user_id,due_date) VALUES (?,?,?,?)',
                       (nc_id,desc,int(assigned_id),due))
            db.execute("UPDATE nonconformities SET status='Em tratamento',updated_at=datetime('now') WHERE id=?",(nc_id,))
            record_history(nc_id,g.user['id'],'Plano de ação','Nova ação corretiva cadastrada')
            db.commit()
            flash('Ação adicionada.','success')
        return redirect(url_for('nc_detail',nc_id=nc_id))

    @app.post('/acoes/<int:action_id>/status')
    @require_roles('admin','analista','gestor')
    def action_update(action_id):
        a=query('''SELECT a.*,n.status AS nc_status FROM corrective_actions a
                   JOIN nonconformities n ON n.id=a.nc_id WHERE a.id=?''',(action_id,),one=True)
        if not a: abort(404)
        if a['nc_status']=='Encerrada': abort(403)
        status=request.form.get('status','')
        if status not in ACTION_STATUSES:
            abort(400,'Status inválido.')
        if status == a['status']:
            flash('Nenhuma alteração realizada: a ação já está nesse status.', 'success')
            return redirect(url_for('nc_detail', nc_id=a['nc_id']))
        db=get_db()
        completed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status=='Concluída' else None
        db.execute('UPDATE corrective_actions SET status=?,completed_at=? WHERE id=?',(status,completed_at,action_id))
        record_history(a['nc_id'],g.user['id'],'Atualização da ação',f'Ação #{action_id} atualizada para {status}')
        # QT-001: se uma ação for reaberta após o envio à verificação,
        # a ocorrência precisa retornar ao tratamento no mesmo commit.
        if a['nc_status']=='Aguardando verificação' and status!='Concluída':
            db.execute("UPDATE nonconformities SET status='Em tratamento',updated_at=datetime('now') WHERE id=?",(a['nc_id'],))
            record_history(a['nc_id'],g.user['id'],'Retorno ao tratamento',
                           f'Ação #{action_id} reaberta; ocorrência voltou para Em tratamento')
        db.commit()
        flash('Status da ação atualizado.','success')
        return redirect(url_for('nc_detail',nc_id=a['nc_id']))

    @app.post('/ocorrencias/<int:nc_id>/status')
    @require_roles('admin','analista','gestor')
    def nc_update_status(nc_id):
        nc=query('SELECT * FROM nonconformities WHERE id=?',(nc_id,),one=True)
        if not nc: abort(404)
        if nc['status']=='Encerrada': abort(403)
        new_status=request.form.get('status','')
        if new_status not in NC_STATUSES or new_status=='Encerrada':
            abort(400,'Status inválido para essa operação.')
        if new_status == nc['status']:
            flash('Nenhuma alteração realizada: a ocorrência já está nesse status.', 'success')
            return redirect(url_for('nc_detail', nc_id=nc_id))
        if new_status=='Aguardando verificação':
            count=query('SELECT COUNT(*) AS n FROM corrective_actions WHERE nc_id=?',(nc_id,),one=True)['n']
            pending=query("SELECT COUNT(*) AS n FROM corrective_actions WHERE nc_id=? AND status<>'Concluída'",(nc_id,),one=True)['n']
            if count==0 or pending:
                flash('Conclua todas as ações antes de solicitar a verificação.','error')
                return redirect(url_for('nc_detail',nc_id=nc_id))
        db=get_db()
        db.execute("UPDATE nonconformities SET status=?,updated_at=datetime('now') WHERE id=?",(new_status,nc_id))
        record_history(nc_id,g.user['id'],'Mudança de status',f'Novo status: {new_status}')
        db.commit()
        flash('Situação atualizada.','success')
        return redirect(url_for('nc_detail',nc_id=nc_id))

    @app.post('/ocorrencias/<int:nc_id>/verificar')
    @require_roles('admin','gestor')
    def verify_close(nc_id):
        nc=query('SELECT * FROM nonconformities WHERE id=?',(nc_id,),one=True)
        if not nc: abort(404)
        if nc['status']!='Aguardando verificação':
            flash('A ocorrência deve estar aguardando verificação.','error')
            return redirect(url_for('nc_detail',nc_id=nc_id))
        result=request.form.get('verification_result','').strip()
        if not 10<=len(result)<=2000:
            flash('Descreva a avaliação de eficácia (mínimo de 10 caracteres).','error')
            return redirect(url_for('nc_detail',nc_id=nc_id))
        pending=query("SELECT COUNT(*) AS n FROM corrective_actions WHERE nc_id=? AND status<>'Concluída'",(nc_id,),one=True)['n']
        count=query('SELECT COUNT(*) AS n FROM corrective_actions WHERE nc_id=?',(nc_id,),one=True)['n']
        if count==0 or pending:
            flash('É necessário concluir todas as ações.','error')
            return redirect(url_for('nc_detail',nc_id=nc_id))
        db=get_db()
        db.execute('''UPDATE nonconformities SET status='Encerrada',verification_result=?,verifier_id=?,
                      closed_at=datetime('now'),updated_at=datetime('now') WHERE id=?''',(result,g.user['id'],nc_id))
        record_history(nc_id,g.user['id'],'Encerramento','Eficácia registrada; ocorrência encerrada')
        db.commit()
        flash('Não conformidade encerrada.','success')
        return redirect(url_for('nc_detail',nc_id=nc_id))

    @app.route('/usuarios',methods=['GET','POST'])
    @require_roles('admin')
    def users():
        if request.method=='POST':
            name=request.form.get('name','').strip()
            email=request.form.get('email','').strip().lower()
            password=request.form.get('password','')
            role=request.form.get('role','')
            if not (2<=len(name)<=100 and re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email)
                    and len(password)>=10 and role in ROLES):
                flash('Nome, e-mail, senha (mínimo 10 caracteres) e perfil obrigatórios.','error')
            else:
                try:
                    get_db().execute('''INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)''',
                                     (name,email,generate_password_hash(password),role))
                    get_db().commit()
                    flash('Usuário cadastrado.','success')
                except __import__('sqlite3').IntegrityError:
                    get_db().rollback()
                    flash('E-mail já cadastrado.','error')
        return render_template('users.html',users=query('SELECT id,name,email,role,active FROM users ORDER BY id'),roles=ROLES)

    @app.cli.command('init-admin')
    @click.option('--name',prompt='Nome do administrador')
    @click.option('--email',prompt='E-mail do administrador')
    @click.password_option('--password',confirmation_prompt=True)
    def init_admin(name,email,password):
        """Inicializa as tabelas e cria o primeiro administrador."""
        if len(password)<10 or len(name.strip())<2 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email.strip()):
            raise click.ClickException('Confira nome, e-mail e senha (mínimo 10 caracteres).')
        init_db()
        try:
            get_db().execute('INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,?)',
                             (name.strip(),email.strip().lower(),generate_password_hash(password),'admin'))
            get_db().commit()
        except __import__('sqlite3').IntegrityError:
            raise click.ClickException('Este e-mail já está cadastrado.')
        click.echo('Administrador cadastrado. Use flask --app app run para iniciar.')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
