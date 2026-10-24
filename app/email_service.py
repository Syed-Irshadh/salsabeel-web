import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_password_reset_email(to_email: str, code: str) -> dict:
    """
    Sends a 6-digit password reset verification code to the recipient's email address.
    Supports HTTP REST APIs (Resend, Brevo) for 100% resilience on serverless platforms (Vercel/AWS),
    falling back to Gmail SMTP (ports 465/587) for local development and dedicated servers.
    """
    from_name = os.getenv("SMTP_FROM_NAME", "Salsabeel Academy")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", os.getenv("SMTP_EMAIL", "")).strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip().replace(" ", "")

    text_content = f"""Assalamu Alaikum,

You requested to reset your password for your Salsabeel Academy account.

Your 6-digit verification code is: {code}

This code will expire in 15 minutes. If you did not request this change, please ignore this email.

With regards,
Salsabeel Academy
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Password Reset Code</title>
</head>
<body style="font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; background-color: #f8faf9; margin: 0; padding: 30px; color: #04272c;">
    <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid rgba(196, 152, 81, 0.3); overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
        <div style="background: #04272c; padding: 24px; text-align: center; border-bottom: 2px solid #c49851;">
            <h2 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 700;">
                Salsabeel <span style="color: #dfb76c;">Academy</span>
            </h2>
            <p style="color: #dfb76c; margin: 4px 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 2px;">
                Traditional Islamic Sciences
            </p>
        </div>
        <div style="padding: 32px 28px;">
            <p style="font-size: 15px; line-height: 1.6; margin-top: 0; color: #334155;">
                <strong>Assalamu Alaikum,</strong>
            </p>
            <p style="font-size: 14px; line-height: 1.6; color: #475569;">
                We received a request to reset the password associated with your account. Use the following 6-digit verification code to complete your password update:
            </p>
            <div style="text-align: center; margin: 28px 0;">
                <div style="display: inline-block; background: #f0fdf9; border: 2px dashed #08535c; border-radius: 12px; padding: 14px 28px;">
                    <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #08535c; font-family: monospace;">
                        {code}
                    </span>
                </div>
            </div>
            <p style="font-size: 12px; line-height: 1.5; color: #64748b; margin-bottom: 0;">
                ⏱️ This code is valid for <strong>15 minutes</strong>. If you did not request a password reset, no further action is required and your account remains secure.
            </p>
        </div>
        <div style="background: #f8faf9; padding: 16px 24px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8;">
            &copy; 2026 Salsabeel Academy · Dedicated to Classical Islamic Knowledge
        </div>
    </div>
</body>
</html>"""

    # 1. High-Reliability HTTP REST API (Resend / Brevo) - Bypasses cloud SMTP socket blocks
    resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
    if resend_api_key:
        try:
            import requests
            r = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": os.getenv("RESEND_FROM", f"{from_name} <onboarding@resend.dev>"),
                    "to": [to_email],
                    "subject": f"{code} is your Salsabeel Academy Password Reset Code",
                    "html": html_content
                },
                timeout=10
            )
            if r.status_code in [200, 201]:
                return {
                    "delivered": True,
                    "dev_mode": False,
                    "message": "Verification code sent to your email successfully via Resend."
                }
            else:
                print(f"Notice: Resend API HTTP {r.status_code}: {r.text}")
        except Exception as re_err:
            print(f"Notice: Resend API dispatch error: {re_err}")

    brevo_api_key = os.getenv("BREVO_API_KEY", "").strip()
    if brevo_api_key:
        try:
            import requests
            sender_email = os.getenv("BREVO_SENDER_EMAIL", os.getenv("SMTP_USER", "salsabeelacademy2025@gmail.com"))
            r = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": brevo_api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={
                    "sender": {"name": from_name, "email": sender_email},
                    "to": [{"email": to_email}],
                    "subject": f"{code} is your Salsabeel Academy Password Reset Code",
                    "htmlContent": html_content
                },
                timeout=10
            )
            if r.status_code in [200, 201]:
                return {
                    "delivered": True,
                    "dev_mode": False,
                    "message": "Verification code sent to your email successfully via Brevo."
                }
            else:
                print(f"Notice: Brevo API HTTP {r.status_code}: {r.text}")
        except Exception as br_err:
            print(f"Notice: Brevo API dispatch error: {br_err}")

    # If SMTP credentials are not provided, print to server console for local testing
    if not smtp_user or not smtp_password:
        print(f"\n=======================================================")
        print(f" [EMAIL DISPATCH NOTICE - SALSABEEL ACADEMY]")
        print(f" Recipient: {to_email}")
        print(f" Verification Code: {code}")
        print(f" Notice: SMTP credentials not set in .env. Code logged above.")
        print(f"=======================================================\n")
        return {
            "delivered": False,
            "dev_mode": True,
            "code": code,
            "message": "Verification code generated and logged to server console (SMTP not configured)."
        }

    # 2. Standard SMTP Dispatch (Works on localhost & dedicated servers)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{code} is your Salsabeel Academy Password Reset Code"
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email
    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        # If port 465 or on serverless cloud, prefer direct SSL
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, 465, timeout=12)
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
            server.quit()
        else:
            try:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())
                server.quit()
            except Exception as starttls_err:
                # Fallback to direct SSL on port 465 (resilient on Vercel / AWS Lambda where STARTTLS socket drops)
                print(f"Notice: Port {smtp_port} STARTTLS issue ({starttls_err}), retrying with direct SSL (port 465)...")
                server = smtplib.SMTP_SSL(smtp_host, 465, timeout=12)
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())
                server.quit()
        return {
            "delivered": True,
            "dev_mode": False,
            "message": "Verification code sent to your email successfully."
        }
    except Exception as e:
        print(f"SMTP error while sending reset code to {to_email}: {e}")
        return {
            "delivered": False,
            "dev_mode": False,
            "error": str(e),
            "code": code,
            "message": f"Could not deliver email: {e}"
        }
