import time
from ClassChecker import ClassChecker
import sqlite3
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText

DATABASE_PATH = Path(__file__).parent / 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_email_notification(email, crn):
    # Configure your email settings
    sender_email = "seatseaker@gmail.com"
    sender_password = "mmwwjaltepnuwykg"
    
    msg = MIMEText(f"Good news! Course {crn} is now available!")
    msg['Subject'] = f"Course {crn} is Available!"
    msg['From'] = sender_email
    msg['To'] = email
    
    # Send email (you'll need to configure this with your email provider)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)

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
            # Wait for 5 minutes before next check
            time.sleep(300)  # 300 seconds = 5 minutes
        except Exception as e:
            print(f"Error occurred: {e}")
            # Wait a bit longer if there was an error
            time.sleep(600)  # 10 minutes

if __name__ == "__main__":
    main()