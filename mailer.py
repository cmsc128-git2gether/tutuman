# mailer.py is responsible for sending emails, such as password reset links.
import os
import smtplib
from email.message import EmailMessage

def send_reset_email(to_email, link):
    # Get the SMTP server address from the .env file.
    host = os.getenv("SMTP_HOST")
    if not host:
        # no SMTP configured: print the link so you can still test locally
        print(f"[DEV] Password reset link for {to_email}: {link}")
        return

    # Create an email message.
    msg = EmailMessage()
    
    # Set the email subject, sender, and recipient.
    msg["Subject"] = "TUTUMAN APP: Reset your password"
    msg["From"] = os.getenv("MAIL_SENDER")
    msg["To"] = to_email
    
    # Body of the email and the user is also informed that the link is valid for 30 minutes.
    # Addtnl: Plain-text version (fallback for email clients that don't show HTML).
    msg.set_content(
        "Hi,\n\n"
        "We received a request to reset the password for your Tutuman account.\n\n"
        f"Click the link below to choose a new password (valid for 30 minutes):\n{link}\n\n"
        "If you didn't ask for this, you can safely ignore this email. "
        "Your password won't change.\n\n"
        "- The Tutuman Devs"
    )

    # HTML version with a button.
    msg.add_alternative(f"""\
    <html>
    <body style="font-family: Arial, sans-serif; background:#f4f4f7; padding:24px;">
        <div style="max-width:480px; margin:auto; background:#ffffff; padding:32px; border-radius:8px;">
        <h2 style="margin-top:0; color:#4f46e5;">Reset your password</h2>
        <p style="color:#444; line-height:1.5;">
            We received a request to reset the password for your Tutuman account.
            Click the button below to choose a new one.
        </p>
        <p style="text-align:center; margin:28px 0;">
            <a href="{link}"
            style="background:#4f46e5; color:#ffffff; padding:12px 24px;
                    text-decoration:none; border-radius:6px; display:inline-block;">
            Reset password
            </a>
        </p>
        <p style="color:#666; font-size:13px; line-height:1.5;">
            This link is valid for 30 minutes. If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{link}" style="color:#4f46e5; word-break:break-all;">{link}</a>
        </p>
        <p style="color:#666; font-size:13px;">
            If you didn't ask for this, you can safely ignore this email. Your password won't change.
        </p>
        </div>
    </body>
    </html>
    """, subtype="html")
    
    # Try to connect to the SMTP server and send the email.
    try:
        port = int(os.getenv("SMTP_PORT", 587))
        print(f"[MAIL] Connecting to {host}:{port}")
        
        # Establish a connection to the SMTP server
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.ehlo() # Identify the application to the SMTP server.
            s.starttls() # Start TLS encryption to secure the email connection.
            s.ehlo() # Identify the application again after enabling encryption.
            
            # Log in to the email account using the credentials in the .env file
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            s.send_message(msg)
            
        print(f"[MAIL] Sent reset email to {to_email}")
    
    # Catch errors that occur while connecting or sending the email.
    except Exception as e:
        print(f"[MAIL ERROR] {type(e).__name__}: {e}")
        print(f"[DEV] Reset link for {to_email}: {link}")