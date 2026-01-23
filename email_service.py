"""
Email service using HTTP API (works on Render)
Using Resend.com - Free 100 emails/day
"""
import requests
import os

# Get API key from environment variable (set in Render dashboard)
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

def send_email_http(to_email, subject, html_body, from_email='onboarding@resend.dev'):
    """
    Send email using Resend HTTP API (works on Render, bypasses SMTP blocks)
    
    Setup:
    1. Sign up at https://resend.com (free 100 emails/day)
    2. Get API key from dashboard
    3. Add to Render: Environment → RESEND_API_KEY = your_key
    """
    
    if not RESEND_API_KEY:
        print("Warning: RESEND_API_KEY not set. Skipping email.")
        return False
    
    try:
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': from_email,
                'to': [to_email],
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
