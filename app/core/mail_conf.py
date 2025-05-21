import os
from fastapi_mail import ConnectionConfig

mail_conf = ConnectionConfig(
    MAIL_USERNAME="Support@joyfulsurprises.in",
    MAIL_PASSWORD="Laptop@#!38489",
    MAIL_FROM="Support@joyfulsurprises.in",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.office365.com",
    MAIL_STARTTLS=True,  # Use this instead of MAIL_TLS
    MAIL_SSL_TLS=False,  # Use this instead of MAIL_SSL
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=os.path.join(
        os.path.dirname(__file__), "email_templates"
    ),  # 👈 Add this
)
