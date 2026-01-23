"""
Simple email service using Gmail SMTP
Works locally. On Render, emails may not send due to SMTP port blocks, but app continues normally.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Get config from environment or use defaults
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'hbaskar1@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'hrgq dsue jzsz zhod')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))

def send_email_http(to_email, subject, html_body, from_email=None):
    """
    Send email using Gmail SMTP
    
    Works locally with your Gmail credentials.
    On Render: Add these to Environment variables for it to work:
    - EMAIL_SENDER = your-email@gmail.com
    - EMAIL_PASSWORD = your-app-password
    
    If email fails (e.g., on Render free tier), app continues normally.
    """
    
    if not EMAIL_PASSWORD or EMAIL_PASSWORD == '':
        print("⚠️ Email password not configured. Skipping email.")
        return False
    
    try:
        print(f"📧 Attempting to send email to {to_email}...")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email or EMAIL_SENDER
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Use SSL connection
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
            
    except Exception as e:
        print(f"⚠️ Email failed (non-critical): {str(e)}")
        print("   App continues normally without email.")
        return False
