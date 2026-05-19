import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_from = os.getenv('EMAIL_FROM')
        self.email_password = os.getenv('EMAIL_PASSWORD')
    
    def enviar_alerta_vencimento(self, contrato, destinatario):
        try:
            dias_restantes = contrato.dias_para_vencer()
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'⚠️ ALERTA: Contrato {contrato.numero_contrato}'
            msg['From'] = self.email_from
            msg['To'] = destinatario
            
            if contrato.esta_vencido():
                status = f'VENCIDO há {abs(dias_restantes)} dias'
            else:
                status = f'Vence em {dias_restantes} dias'
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2>🔔 Alerta de Vencimento de Contrato</h2>
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px;">
                  <p><strong>Contrato:</strong> {contrato.nome}</p>
                  <p><strong>Número:</strong> {contrato.numero_contrato}</p>
                  <p><strong>Fornecedor:</strong> {contrato.fornecedor}</p>
                  <p><strong>Data de Vencimento:</strong> {contrato.data_vencimento.strftime('%d/%m/%Y')}</p>
                  <p><strong>Status:</strong> {status}</p>
                  <p><strong>Valor:</strong> R$ {contrato.valor:,.2f}</p>
                </div>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Email enviado para {destinatario}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
            return False
