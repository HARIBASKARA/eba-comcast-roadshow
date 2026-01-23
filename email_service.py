"""
Email service using HTTP API (works on Render)
Using Mailgun API - Free 100 emails/day to any address
"""
import requests
import os

# Get API key from environment variable (set in Render dashboard)
MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', 'sandbox-123.mailgun.org')

def send_email_http(to_email, subject, html_body, from_email='EBI Roadshow <mailgun@sandbox.mailgun.org>'):
    """
    Send email using Mailgun HTTP API (works on Render, bypasses SMTP blocks)
    
    Setup:
    1. Sign up at https://signup.mailgun.com/new/signup (free 100 emails/day)
    2. Get API key from dashboard (starts with 'key-')
    3. Add to Render Environment: 
       - MAILGUN_API_KEY = your_key
       - MAILGUN_DOMAIN = your_sandbox_domain (e.g., sandbox123.mailgun.org)
    """
    
    if not MAILGUN_API_KEY:
        print("Warning: MAILGUN_API_KEY not set. Skipping email.")
        return False
    
    try:
        response = requests.post(
            f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages',
            auth=('api', MAILGUN_API_KEY),
            data={
                'from': from_email,
                'to': to_email,
                'subject': subject,
                'html': html_body
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Email sent successfully to {to_email}")
            return True
        else:
            print(f"❌ Email failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        return False
