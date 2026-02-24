"""Logging configuration for the application."""

import logging
import os
from email.utils import formataddr
from logging.handlers import RotatingFileHandler, SMTPHandler
from pathlib import Path
from typing import Sequence


class SmtpHandler(SMTPHandler):
    """ """

    def __init__(
        self,
        mailhost: tuple[str, int],
        from_addr: str,
        toaddrs: Sequence[str],
        subject: str,
        credentials: tuple[str, str] | None = None,
        use_tls: bool = False,
        use_ssl: bool = False,
        timeout: float = 10.0,
    ):
        super().__init__(
            mailhost,
            from_addr,
            list(toaddrs),
            subject,
            credentials=credentials,
            secure=() if use_tls else None,
        )
        self._use_tls = use_tls
        self._use_ssl = use_ssl
        self._timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        import smtplib

        try:
            port = self.mailport
            if self._use_ssl:
                smtp = smtplib.SMTP_SSL(self.mailhost, port, timeout=self._timeout)
            else:
                smtp = smtplib.SMTP(self.mailhost, port, timeout=self._timeout)

            with smtp:
                if self.username:
                    smtp.login(self.username, self.password)

                msg = self.format(record)
                smtp.sendmail(self.fromaddr, self.toaddrs, msg)
        except Exception:
            self.handleError(record)


def setup_logging(mail_config=None):
    """Configure logging to output to file/console, plus dedicated auth log + optional email alerts."""
    # Put logs in the project root (next to app.log) regardless of current working directory.
    project_root = Path(__file__).resolve().parents[2]
    app_log_path = project_root / "app.log"
    auth_log_path = project_root / "auth.log"

    # Base logging: console + general app file
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(app_log_path, maxBytes=5_000_000, backupCount=3),
            logging.StreamHandler(),
        ],
        force=True,
    )

    # Dedicated auth logger -> auth.log only (no double logging into app.log/console)
    auth_handler = RotatingFileHandler(auth_log_path, maxBytes=5_000_000, backupCount=3)
    auth_handler.setLevel(logging.INFO)
    auth_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    auth_logger = logging.getLogger("auth")
    auth_logger.setLevel(logging.INFO)
    auth_logger.handlers = [auth_handler]
    auth_logger.propagate = False

    # Optional: email alerts for auth warnings/errors
    if mail_config is not None:
        # NOTE: if you want a different recipient, add it to config and use it here.
        to_adders = [mail_config.sender_email]

        from_addr = mail_config.sender_email
        if getattr(mail_config, "sender", None):
            from_addr = formataddr((mail_config.sender, mail_config.sender_email))

        credentials = None
        if mail_config.username and mail_config.password:
            credentials = (mail_config.username, mail_config.password)

        app_env = os.getenv("APP_ENV", "development")
        if app_env != "development":

            mail_handler = SmtpHandler(
                mailhost=(mail_config.host, mail_config.port),
                from_addr=from_addr,
                toaddrs=to_adders,
                subject="[WarriorFit] Auth warning/error",
                credentials=credentials,
                use_tls=bool(mail_config.use_tls),
                use_ssl=bool(mail_config.use_ssl),
            )
            mail_handler.setLevel(logging.WARNING)
            mail_handler.setFormatter(
                logging.Formatter(
                    "From: %(name)s\n"
                    "Level: %(levelname)s\n"
                    "Time: %(asctime)s\n\n"
                    "%(message)s"
                )
            )

            # Only auth warnings+ trigger email
            auth_logger.addHandler(mail_handler)
