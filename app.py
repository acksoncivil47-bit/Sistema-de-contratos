from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Contrato
from email_sender import EmailSender
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-temporaria-change-me')

database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///contratos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

email_sender = EmailSender()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def verificar_contratos():
    with app.app_context():
        try:
            contratos = Contrato.query.filter_by(status='Ativo').all()
            for contrato in contratos:
                if contrato.precisa_notificar():
                    email_sender.enviar_alerta_vencimento(contrato, contrato.email_notificacao)
                    contrato.ultimo_aviso_enviado = datetime.now().date()
            db.session.commit()
            print(f"✅ Verificação executada em {datetime.now()}")
        except Exception as e:
            print(f"❌ Erro: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=verificar_contratos, trigger="interval", hours=6)
scheduler.start()

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_contratos = Contrato.query.count()
    contratos_ativos = Contrato.query.filter_by(status='Ativo').count()
    
    contratos_vencidos = Contrato.query.filter(
        Contrato.data_vencimento < datetime.now().date(),
        Contrato.status == 'Ativo'
    ).all()
    
    contratos_a_vencer = Contrato.query.filter(
        Contrato.data_vencimento >= datetime.now().date(),
        Contrato.status == 'Ativo'
    ).order_by(Contrato.data_vencimento).all()
    
    contratos_a_vencer = [c for c in contratos_a_vencer if c.dias_para_vencer() <= 30]
    
    return render_template('dashboard.html',
                         total_contratos=total_contratos,
                         contratos_ativos=contratos_ativos,
                         contratos_vencidos=contratos_vencidos,
                         contratos_a_vencer=contratos_a_vencer)

@app.route('/contratos')
@login_required
def listar_contratos():
    contratos = Contrato.query.order_by(Contrato.data_vencimento).all()
    return render_template('contratos.html', contratos=contratos)

@app.route('/contratos/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_contrato():
    if request.method == 'POST':
        try:
            contrato = Contrato(
                nome=request.form['nome'],
                fornecedor=request.form['fornecedor'],
                numero_contrato=request.form['numero_contrato'],
                data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d'),
                data_vencimento=datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d'),
                valor=float(request.form['valor']),
                email_notificacao=request.form['email_notificacao'],
                dias_aviso=int(request.form.get('dias_aviso', 30)),
                observacoes=request.form.get('observacoes', '')
            )
            db.session.add(contrato)
            db.session.commit()
            flash('Contrato adicionado com sucesso!', 'success')
            return redirect(url_for('listar_contratos'))
        except Exception as e:
            flash(f'Erro: {str(e)}', 'danger')
    
    return render_template('add_contrato.html')

@app.route('/contratos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            contrato.nome = request.form['nome']
            contrato.fornecedor = request.form['fornecedor']
            contrato.numero_contrato = request.form['numero_contrato']
            contrato.data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d')
            contrato.data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d')
            contrato.valor = float(request.form['valor'])
            contrato.email_notificacao = request.form['email_notificacao']
            contrato.dias_aviso = int(request.form.get('dias_aviso', 30))
            contrato.status = request.form['status']
            contrato.observacoes = request.form.get('observacoes', '')
            
            db.session.commit()
            flash('Contrato atualizado!', 'success')
            return redirect(url_for('listar_contratos'))
        except Exception as e:
            flash(f'Erro: {str(e)}', 'danger')
    
    return render_template('add_contrato.html', contrato=contrato)

@app.route('/contratos/deletar/<int:id>')
@login_required
def deletar_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    db.session.delete(contrato)
    db.session.commit()
    flash('Contrato deletado!', 'success')
    return redirect(url_for('listar_contratos'))

@app.route('/contratos/testar-email/<int:id>')
@login_required
def testar_email(id):
    contrato = Contrato.query.get_or_404(id)
    if email_sender.enviar_alerta_vencimento(contrato, contrato.email_notificacao):
        flash('Email enviado!', 'success')
    else:
        flash('Erro ao enviar email', 'danger')
    return redirect(url_for('listar_contratos'))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if Usuario.query.first():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        admin = Usuario(
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            email=request.form['email']
        )
        db.session.add(admin)
        db.session.commit()
        flash('Admin criado! Faça login', 'success')
        return redirect(url_for('login'))
    
    return render_template('setup.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
