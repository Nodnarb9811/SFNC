"""Send the daily report by email over SMTP (stdlib only)."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from .config import EmailConfig


def send_email(cfg: EmailConfig, subject: str, text_body: str, html_body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.from_addr
    msg["To"] = cfg.to_addr
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    if cfg.security == "ssl":
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, context=context) as server:
            server.login(cfg.smtp_user, cfg.smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
            server.ehlo()
            if cfg.security == "tls":
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if cfg.smtp_user:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.send_message(msg)
