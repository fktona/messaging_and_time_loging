from flask import Flask, request
from celery import Celery
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import re
from datetime import datetime
from config import Config

app = Flask(__name__)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'pyamqp://guest@localhost//'
app.config['CELERY_RESULT_BACKEND'] = 'rpc://'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def send_email(to_email):
    try:
        # SMTP configuration for Gmail
        smtp_server = 'smtp.gmail.com'
        smtp_port = 465
        smtp_username = Config.GMAIL
        smtp_password = Config.GMAIL_PASSWORD

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Create a MIMEText object to represent the email
        message = MIMEMultipart()
        message['From'] = smtp_username
        message['To'] = to_email
        message['Subject'] = 'Test Subject'
        body = 'This is a test email.'
        message.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server using SSL
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_email, message.as_string())

        return f"Email sent successfully to {to_email}"
    except Exception as e:
        print(f"Failed to send email: {e}")
        return f"Failed to send email to {to_email}: {e}"

def is_valid_email(email):
    # Simple email validation using regex
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

@app.route('/end')
def welcome():
    return "Welcome to the messaging system!"

@app.route('/', methods=['GET'])
def handle_request():
    sendmail = request.args.get('sendmail')
    talktome = request.args.get('talktome')
    if sendmail:
        if is_valid_email(sendmail):
            result = send_email.delay(sendmail)
            return f"Email to {sendmail} has been queued."
        else:
            return "Invalid email address provided."

    if talktome is not None:
        with open('/var/log/messaging_system.log', 'a') as log_file:
            log_file.write(f"Current time: {datetime.now()}\n")
        return "Logged current time."

    return "No valid parameters provided."

if __name__ == '__main__':
    app.run(debug=True)
