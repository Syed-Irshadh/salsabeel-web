import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_password_reset_email(to_email: str, code: str) -> dict:
    """
    Sends a 6-digit password reset verification code to the recipient's email address.
    If SMTP credentials are not configured in .env, prints code to server logs for testing.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", os.getenv("SMTP_EMAIL", "salsabeelacademy2025@gmail.com")).strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "umcb dtva ydxc nsjz").strip().replace(" ", "")
    from_name = os.getenv("SMTP_FROM_NAME", "Salsabeel Academy")

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

    # Construct HTML & plain text email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{code} is your Salsabeel Academy Password Reset Code"
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email

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

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
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
