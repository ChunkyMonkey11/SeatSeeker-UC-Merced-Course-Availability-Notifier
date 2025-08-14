import time
from ClassChecker import ClassChecker
import sqlite3
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
DATABASE_PATH = Path(__file__).parent / os.getenv('DATABASE_PATH', 'database.db')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))
ERROR_RETRY_INTERVAL = int(os.getenv('ERROR_RETRY_INTERVAL', '600'))

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_email_notification(email, crn):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        raise ValueError("Missing email configuration in environment variables. Please check your .env file.")
    
    msg = MIMEText(f"Good news! Course {crn} is now available!")
    msg['Subject'] = f"Course {crn} is Available!"
    msg['From'] = EMAIL_SENDER
    msg['To'] = email
    
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise

def check_availability():
    checker = ClassChecker()
    open_sections = checker.run()
    
    conn = get_db()
    current_time = datetime.utcnow().isoformat()
    
    try:
        # Get all subscriptions
        subscriptions = conn.execute('SELECT * FROM subscriptions').fetchall()
        
        # Check each subscription against open sections
        for sub in subscriptions:
            crn = sub['crn']
            email = sub['email']
            current_status = sub['status']
            
            if crn in open_sections:
                # Course is available
                if current_status != 'available':
                    try:
                        # Try to send email
                        send_email_notification(email, crn)
                        # If email sent successfully, delete the subscription
                        conn.execute('''
                            DELETE FROM subscriptions 
                            WHERE email = ? AND crn = ?
                        ''', (email, crn))
                    except Exception as e:
                        # If email fails, mark it as error
                        conn.execute('''
                            UPDATE subscriptions 
                            SET status = 'error', last_checked = ? 
                            WHERE email = ? AND crn = ?
                        ''', (current_time, email, crn))
                        print(f"Failed to send email for {crn} to {email}: {str(e)}")
            else:
                # Course is not available
                conn.execute('''
                    UPDATE subscriptions 
                    SET status = 'pending', last_checked = ? 
                    WHERE crn = ?
                ''', (current_time, crn))
        
        conn.commit()
    finally:
        conn.close()

def main():
    while True:
        try:
            check_availability()
            # Wait for configured interval before next check
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Error occurred: {e}")
            # Wait longer if there was an error
            time.sleep(ERROR_RETRY_INTERVAL)

if __name__ == "__main__":
    main()