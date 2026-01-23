from flask import Flask, render_template, request, jsonify, session
import csv
import os
from datetime import datetime
import secrets
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Email Configuration
# You can update these directly or use email_config.py
try:
    from email_config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, USE_SSL
except ImportError:
    # Default values if email_config.py doesn't exist
    EMAIL_SENDER = 'your-email@gmail.com'  # Update with your email
    EMAIL_PASSWORD = 'your-app-password'  # Update with your app password
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 465
    USE_SSL = True

# File paths
ENTRY_DATA_FILE = 'entry_data.csv'
TIME_TRACKING_DIR = 'time_tracking'

# Ensure directories exist
os.makedirs(TIME_TRACKING_DIR, exist_ok=True)

# Initialize CSV files if they don't exist
if not os.path.exists(ENTRY_DATA_FILE):
    with open(ENTRY_DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Employee ID', 'Name', 'Email', 'Entry Timestamp'])

# Project configuration
PROJECTS = {
    '1': {'name': 'Framework', 'estimated_time': '15 minutes'},
    '2': {'name': 'Solution', 'estimated_time': '15 minutes'},
    '3': {'name': 'Data Analytics Team', 'estimated_time': '15 minutes'},
    '4': {'name': 'Machine Learning Team', 'estimated_time': '15 minutes'},
    '5': {'name': 'Artificial Intelligence Team', 'estimated_time': '15 minutes'},
    '6': {'name': 'Market Team', 'estimated_time': '15 minutes'},
    '7': {'name': 'Email Campaign Team', 'estimated_time': '15 minutes'}
}

@app.route('/')
def index():
    """Welcome page with entry form"""
    return render_template('index.html')

@app.route('/submit-entry', methods=['POST'])
def submit_entry():
    """Handle employee entry data submission"""
    data = request.json
    employee_id = data.get('employee_id')
    name = data.get('name')
    email = data.get('email')
    
    if not all([employee_id, name, email]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'success': False, 'message': 'Invalid email format. Please enter a valid email address.'}), 400
    
    # Check for duplicate employee ID or email
    if os.path.exists(ENTRY_DATA_FILE):
        with open(ENTRY_DATA_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Employee ID'] == employee_id:
                    return jsonify({'success': False, 'message': 'This Employee ID has already been registered.'}), 400
                if row['Email'].lower() == email.lower():
                    return jsonify({'success': False, 'message': 'This Email ID has already been registered.'}), 400
    
    # Save to session
    session['employee_id'] = employee_id
    session['name'] = name
    session['email'] = email
    session['entry_time'] = datetime.now().isoformat()
    
    # Initialize project times tracking in session
    if 'project_times' not in session:
        session['project_times'] = {}
    
    # Log entry data to CSV
    entry_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ENTRY_DATA_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([employee_id, name, email, entry_timestamp])
    
    return jsonify({'success': True})

@app.route('/projects')
def projects():
    """Display all projects"""
    if 'employee_id' not in session:
        return render_template('index.html')
    
    # Get project times from session
    project_times = session.get('project_times', {})
    
    return render_template('projects.html', 
                         projects=PROJECTS,
                         employee_name=session.get('name'),
                         project_times=project_times)

@app.route('/project/<project_id>')
def project_detail(project_id):
    """Display individual project page"""
    if 'employee_id' not in session:
        return render_template('index.html')
    
    if project_id not in PROJECTS:
        return "Project not found", 404
    
    project = PROJECTS[project_id]
    return render_template('project_detail.html', 
                         project_id=project_id,
                         project=project)

@app.route('/start-project/<project_id>', methods=['POST'])
def start_project(project_id):
    """Record start time when QR is scanned at project"""
    if 'employee_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    if project_id not in PROJECTS:
        return jsonify({'success': False, 'message': 'Invalid project'}), 400
    
    # Record start time
    start_time = datetime.now().isoformat()
    if 'project_start_times' not in session:
        session['project_start_times'] = {}
    
    session['project_start_times'][project_id] = start_time
    session.modified = True
    
    return jsonify({'success': True, 'start_time': start_time})

@app.route('/end-project/<project_id>', methods=['POST'])
def end_project(project_id):
    """Calculate time spent when user returns to main menu"""
    if 'employee_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    if project_id not in PROJECTS:
        return jsonify({'success': False, 'message': 'Invalid project'}), 400
    
    # Get start time
    if 'project_start_times' not in session or project_id not in session['project_start_times']:
        return jsonify({'success': False, 'message': 'Project not started'}), 400
    
    start_time = datetime.fromisoformat(session['project_start_times'][project_id])
    end_time = datetime.now()
    time_spent = (end_time - start_time).total_seconds() / 60  # Convert to minutes
    
    # Store time spent
    if 'project_times' not in session:
        session['project_times'] = {}
    
    session['project_times'][project_id] = round(time_spent, 2)
    session.modified = True
    
    # Save to CSV file for this employee
    save_time_tracking(session['employee_id'], project_id, time_spent)
    
    return jsonify({
        'success': True, 
        'time_spent': round(time_spent, 2),
        'project_name': PROJECTS[project_id]['name']
    })

def save_time_tracking(employee_id, project_id, time_spent):
    """Save time tracking data to employee-specific CSV file"""
    file_path = os.path.join(TIME_TRACKING_DIR, f'{employee_id}_time_tracking.csv')
    
    # Check if file exists
    file_exists = os.path.exists(file_path)
    
    # Read existing data if file exists
    project_data = {}
    if file_exists:
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                project_data = row
                break
    
    # Update project time
    project_key = f'Module {project_id} (minutes)'
    project_data['Employee ID'] = employee_id
    project_data[project_key] = time_spent
    
    # Write updated data
    fieldnames = ['Employee ID'] + [f'Module {i} (minutes)' for i in range(1, 8)]
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(project_data)

@app.route('/get-session-data')
def get_session_data():
    """Get current session data for debugging"""
    return jsonify({
        'employee_id': session.get('employee_id'),
        'name': session.get('name'),
        'project_times': session.get('project_times', {})
    })

def send_summary_email(employee_name, employee_email, employee_id, entry_time, project_times):
    """Send summary email to the employee after logout"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Thank You for Visiting EBI Comcast Roadshow!'
        msg['From'] = EMAIL_SENDER
        msg['To'] = employee_email
        
        # Format entry time
        entry_datetime = datetime.fromisoformat(entry_time)
        formatted_entry_time = entry_datetime.strftime('%B %d, %Y at %I:%M %p')
        
        # Create beautiful email body with modern design
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .email-wrapper {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px 20px;
                    min-height: 100vh;
                }}
                .email-container {{
                    max-width: 650px;
                    margin: 0 auto;
                    background: #ffffff;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                }}
                .header {{
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    padding: 50px 30px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 32px;
                    font-weight: 700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    font-size: 18px;
                    opacity: 0.95;
                }}
                .content {{
                    padding: 40px 35px;
                    background: #ffffff;
                }}
                .greeting {{
                    font-size: 24px;
                    color: #1e3c72;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}
                .entry-info {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 12px;
                    margin: 25px 0;
                    text-align: center;
                }}
                .entry-info p {{
                    margin: 5px 0;
                    font-size: 16px;
                }}
                .section-title {{
                    font-size: 22px;
                    color: #1e3c72;
                    margin: 30px 0 20px 0;
                    font-weight: 700;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }}
                .modules-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    border-radius: 10px;
                    overflow: hidden;
                }}
                .modules-table thead {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .modules-table th {{
                    padding: 18px 15px;
                    text-align: left;
                    font-weight: 700;
                    font-size: 15px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .modules-table tbody tr {{
                    border-bottom: 1px solid #e0e0e0;
                    transition: background-color 0.3s;
                }}
                .modules-table tbody tr:hover {{
                    background-color: #f8f9fa;
                }}
                .modules-table tbody tr:last-child {{
                    border-bottom: none;
                }}
                .modules-table td {{
                    padding: 16px 15px;
                    color: #333;
                    font-size: 15px;
                }}
                .module-name {{
                    font-weight: 600;
                    color: #1e3c72;
                }}
                .time-spent {{
                    font-family: 'Courier New', monospace;
                    color: #764ba2;
                    font-weight: 600;
                }}
                .no-visits {{
                    text-align: center;
                    padding: 30px;
                    color: #999;
                    font-style: italic;
                    background: #f8f9fa;
                    border-radius: 10px;
                }}
                .thank-you {{
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 12px;
                    margin: 30px 0 20px 0;
                    text-align: center;
                    font-size: 18px;
                    font-weight: 600;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }}
                .footer strong {{
                    color: #1e3c72;
                    font-size: 18px;
                }}
                .footer p {{
                    margin: 8px 0;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="email-container">
                    <div class="header">
                        <h1>🚀 Thanks for Visiting EBI Comcast Roadshow</h1>
                        <p>We Appreciate Your Time and Interest</p>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">Hi {employee_name},</div>
                        
                        <div class="entry-info">
                            <p><strong>📅 You entered the roadshow at:</strong></p>
                            <p style="font-size: 18px; margin-top: 8px;">{formatted_entry_time}</p>
                            <p style="margin-top: 10px; font-size: 14px; opacity: 0.9;">Employee ID: {employee_id}</p>
                        </div>
                        
                        <div class="section-title">📊 Modules Visited</div>
        """
        
        if project_times:
            html_body += """
                        <table class="modules-table">
                            <thead>
                                <tr>
                                    <th>Module Name</th>
                                    <th>Time Spent</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for project_id, time_spent in project_times.items():
                project_name = PROJECTS.get(project_id, {}).get('name', f'Module {project_id}')
                
                # Format time spent
                minutes = int(time_spent)
                seconds = int((time_spent % 1) * 60)
                
                if minutes > 0:
                    time_str = f"{minutes}m {seconds}s"
                else:
                    time_str = f"{seconds}s"
                
                html_body += f"""
                                <tr>
                                    <td class="module-name">📍 {project_name}</td>
                                    <td class="time-spent">{time_str}</td>
                                </tr>
                """
            
            html_body += """
                            </tbody>
                        </table>
            """
        else:
            html_body += """
                        <div class="no-visits">
                            You browsed our teams but didn't visit any specific modules yet.
                        </div>
            """
        
        html_body += """
                        <div class="thank-you">
                            🙏 Thank You for Your Time!<br>
                            <span style="font-size: 16px; font-weight: 400; margin-top: 8px; display: block;">
                                We hope you gained valuable insights into our innovative solutions.
                            </span>
                        </div>
                        
                        <p style="color: #666; font-size: 15px; line-height: 1.6; margin-top: 25px;">
                            If you have any questions or would like to learn more about our teams and solutions, 
                            please don't hesitate to reach out to us.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p><strong>EBI Comcast</strong></p>
                        <p>Driving Innovation Forward 🚀</p>
                        <p style="margin-top: 15px; font-size: 12px; color: #999;">
                            © 2026 EBI Comcast. All rights reserved.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email using SSL or TLS based on config
        if USE_SSL:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@app.route('/logout', methods=['POST'])
def logout():
    """Handle logout and send summary email"""
    try:
        # Get session data before clearing
        employee_name = session.get('name', 'Guest')
        employee_email = session.get('email')
        employee_id = session.get('employee_id')
        entry_time = session.get('entry_time')
        project_times = session.get('project_times', {})
        
        # Send email if we have an email address (with timeout to prevent hanging)
        email_sent = False
        if employee_email and employee_id and entry_time:
            try:
                email_sent = send_summary_email(employee_name, employee_email, employee_id, entry_time, project_times)
            except Exception as email_error:
                print(f"Email sending failed (non-critical): {str(email_error)}")
                email_sent = False
        
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True,
            'email_sent': email_sent,
            'message': 'Logged out successfully' + (' - Email sent!' if email_sent else '')
        })
    except Exception as e:
        # Clear session anyway
        session.clear()
        return jsonify({
            'success': False,
            'message': f'Logout completed but error occurred: {str(e)}'
        })

@app.route('/get-project-times')
def get_project_times():
    """Get project times for leaderboard sorted by duration"""
    project_times = session.get('project_times', {})
    
    times_list = []
    for project_id, minutes in project_times.items():
        # project_id is already a string from session
        if project_id in PROJECTS:
            project_name = PROJECTS[project_id]['name']
            
            # Convert minutes to formatted time string
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            secs = int((minutes % 1) * 60)
            
            if hours > 0:
                time_str = f"{hours}h {mins}m {secs}s"
            elif mins > 0:
                time_str = f"{mins}m {secs}s"
            else:
                time_str = f"{secs}s"
            
            times_list.append({
                'project_id': project_id,
                'project_name': project_name,
                'time_spent': time_str,
                'duration': minutes  # For sorting
            })
    
    return jsonify({'times': times_list})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
