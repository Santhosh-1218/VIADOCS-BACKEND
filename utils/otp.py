# backend/utils/otp.py
import random
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText

load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASS = os.getenv("EMAIL_PASS")

def generate_otp():
    """Generate a 4-digit OTP"""
    return str(random.randint(1000, 9999))

def send_otp_email(receiver_email, otp):
    """Send OTP via Gmail"""
    try:
        msg = MIMEText(f"Your Viadocs password reset OTP is: {otp}")
        msg["Subject"] = "Viadocs - Password Reset OTP"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print("❌ OTP Email Error:", e)
        return False
