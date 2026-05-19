from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
class Contrato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    fornecedor = db.Column(db.String(200), nullable=False)
    numero_contrato = db.Column(db.String(100), unique=True)
    data_inicio = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Float)
    status = db.Column(db.String(50), default='Ativo')
    observacoes = db.Column(db.Text)
    email_notificacao = db.Column(db.String(120), nullable=False)
    dias_aviso = db.Column(db.Integer, default=30)
    ultimo_aviso_enviado = db.Column(db.Date)
    
    def dias_para_vencer(self):
        delta = self.data_vencimento - datetime.now().date()
        return delta.days
    
    def esta_vencido(self):
        return datetime.now().date() > self.data_vencimento
    
    def precisa_notificar(self):
        dias_restantes = self.dias_para_vencer()
        if self.esta_vencido():
            return True
        if dias_restantes <= self.dias_aviso:
            if not self.ultimo_aviso_enviado or self.ultimo_aviso_enviado < datetime.now().date():
                return True
        return False
