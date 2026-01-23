"""
Email service using Resend HTTP API (works on Render - no SMTP blocks!)
Resend: Free 3,000 emails/month, 100/day - SIMPLEST setup ever
"""
import requests
import os

# Get API key from environment
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')

def send_email_http(to_email, subject, html_body, from_email=None):
    """
    Send email using Resend HTTP API (works perfectly on Render!)
    
    SUPER SIMPLE SETUP (1 minute):
    1. Go to https://resend.com/signup (sign up free)
    2. Get API key from dashboard (starts with 're_')
    3. Add to Render Environment:
       RESEND_API_KEY = re_your_key_here
    
    That's it! No email verification needed for testing.
    """
    
    if not RESEND_API_KEY or RESEND_API_KEY == '':
        print("⚠️ RESEND_API_KEY not set. Skipping email.")
        print("👉 Quick setup: https://resend.com/signup → Get API key → Add to Render Environment")
        return False
    
    try:
        print(f"📧 Sending email to {to_email} via Resend API...")
        
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': from_email or RESEND_FROM_EMAIL,
                'to': [to_email],
                'subject': subject,
                'html': html_body
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
        print("   App continues normally without email.")
        return False
