import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def send_email(to: str, subject: str, html_body: str) -> None:
    """Send an email via SMTP. If SMTP is not configured, print to console."""
    if not settings.SMTP_HOST:
        print(f"[DEV EMAIL] To: {to}")
        print(f"[DEV EMAIL] Subject: {subject}")
        print(f"[DEV EMAIL] Body:\n{html_body}")
        print("[DEV EMAIL] ────────────────────────")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    if settings.SMTP_USE_SSL:
        # Port 465 — implicit SSL (SMTPS)
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    elif settings.SMTP_USE_TLS:
        # Port 587 — STARTTLS
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    else:
        # No encryption (dev/Mailpit)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)


def send_password_reset_email(to: str, full_name: str, reset_token: str) -> None:
    """Send a password reset email with a link containing the token."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    safe_name = html.escape(full_name)
    html_body = f"""\
<html>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Password Reset</h2>
  <p>Hi {safe_name},</p>
  <p>We received a request to reset your password. Click the link below to set a new password:</p>
  <p style="margin: 24px 0;">
    <a href="{reset_url}"
       style="background-color: #2563eb; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
      Reset Password
    </a>
  </p>
  <p>This link will expire in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.</p>
  <p>If you didn't request this, you can safely ignore this email.</p>
  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
  <p style="color: #6b7280; font-size: 12px;">Klepak Scores</p>
</body>
</html>"""
    send_email(to, "Password Reset - Klepak Scores", html_body)


def send_invitation_email(to: str, role: str, raw_token: str) -> None:
    """Send an evaluator invitation email with a setup link."""
    setup_url = f"{settings.FRONTEND_URL}/setup-account?token={raw_token}"
    role_label = html.escape(
        "Evaluator" if role == "EVALUATOR" else role.replace("_", " ").title()
    )
    html = f"""\
<html>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>You've Been Invited!</h2>
  <p>You've been invited to join Klepak Scores as an <strong>{role_label}</strong>.</p>
  <p>Click the link below to set up your account:</p>
  <p style="margin: 24px 0;">
    <a href="{setup_url}"
       style="background-color: #2563eb; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
      Set Up Account
    </a>
  </p>
  <p>This link will expire in {settings.INVITATION_EXPIRE_DAYS} days.</p>
  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
  <p style="color: #6b7280; font-size: 12px;">Klepak Scores</p>
</body>
</html>"""
    send_email(to, f"You're invited to Klepak Scores as {role_label}", html)


def send_onboarding_email(to: str, raw_token: str) -> None:
    """Send the super admin onboarding email with a setup link."""
    setup_url = f"{settings.FRONTEND_URL}/setup-account?token={raw_token}"
    html = f"""\
<html>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Welcome to Klepak Scores!</h2>
  <p>You've been designated as the <strong>Super Admin</strong> for Klepak Scores.</p>
  <p>Click the link below to set up your account with your name and password:</p>
  <p style="margin: 24px 0;">
    <a href="{setup_url}"
       style="background-color: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
      Set Up Your Account
    </a>
  </p>
  <p>This link will expire in {settings.BOOTSTRAP_TOKEN_EXPIRE_HOURS} hours.</p>
  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
  <p style="color: #6b7280; font-size: 12px;">Klepak Scores</p>
</body>
</html>"""
    send_email(to, "Set Up Your Super Admin Account - Klepak Scores", html)
