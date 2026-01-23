"""
Email service using Brevo API (formerly Sendinblue)
Free: 300 emails/day, works on Render, NO domain verification needed!
"""
import requests
import os

# Get API key from environment
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
BREVO_FROM_EMAIL = os.environ.get('BREVO_FROM_EMAIL', 'Haribaskar_Arivazhagan@comcast.com')
BREVO_FROM_NAME = os.environ.get('BREVO_FROM_NAME', 'EBI Roadshow')

def send_email_http(to_email, subject, html_body, from_email=None):
    """
    Send email using Brevo API (works on Render, no SMTP needed!)
    
    EASY SETUP (2 minutes):
    1. Sign up FREE: https://app.brevo.com/account/register
    2. Go to: Settings → SMTP & API → API Keys → Create New
    3. Add to Render Environment:
       BREVO_API_KEY = xkeysib-your_key_here
       BREVO_FROM_EMAIL = Haribaskar_Arivazhagan@comcast.com
    
    That's it! 300 free emails/day, no domain verification required!
    """
    
    if not BREVO_API_KEY or BREVO_API_KEY == '':
        print("⚠️ BREVO_API_KEY not set. Email disabled.")
        print("👉 Setup: https://app.brevo.com/account/register")
        return False
    
    try:
        print(f"📧 Sending email to {to_email} via Brevo API...")
        
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': BREVO_API_KEY,
                'Content-Type': 'application/json'
            },
            json={
                'sender': {
                    'email': from_email or BREVO_FROM_EMAIL,
                    'name': BREVO_FROM_NAME
                },
                'to': [{'email': to_email}],
                'subject': subject,
                'htmlContent': html_body
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Email sent successfully to {to_email}")
            return True
        else:
            print(f"⚠️ Email failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️ Email failed (non-critical): {str(e)}")
        print("   App continues normally. Data saved to CSV.")
        return False
