from io import BytesIO
import os
from app.core.mail_conf import mail_conf
from app.db.models.orders import Orders
from fastapi_mail import FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import Settings
import boto3
import pdfkit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("index.html")

print("BASE_DIR", BASE_DIR)
print("TEMPLATE_DIR", TEMPLATE_DIR)
print("env", env)
settings = Settings()


async def order_email_sent(email_to, data):
    try:
        # Get today's date
        today = datetime.today()
        # Add 4 days
        next_date = today + timedelta(days=4)
        html_content = template.render(
            data=data,
            order_placed_date=next_date.strftime("%Y-%m-%d"),
            day_name=next_date.strftime("%A"),  # e.g., Saturday
        )

        message = MessageSchema(
            subject="Order Confirmation",
            recipients=[email_to],
            body=html_content,
            subtype=MessageType.html,  # or .plain for plain text
        )
        fm = FastMail(mail_conf)
        await fm.send_message(message)
    except Exception as error:
        print("error email", email_to, error)


# S3 Client
s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY,
)

PDF_KIT_OPTIONS = {
    "page-size": "A4",
    "margin-top": "0.0in",
    "margin-right": "0.2in",
    "margin-bottom": "0.0in",
    "margin-left": "0.2in",
    "minimum-font-size": "20",
}


def generate_pdf_and_upload_to_s3(
    db: Session, file_name="order_invoice", data={}, order_id=""
) -> str:
    """
    Generate a PDF from HTML, upload it to S3, and return the public URL.

    :param html_content: HTML string to convert to PDF
    :param file_name: Name of the file to save in S3
    :param data: Data to render in the HTML template
    :return: Public URL of the uploaded PDF
    """
    try:
        # Get today's date
        today = datetime.today()

        # Add 4 days
        next_date = today + timedelta(days=4)

        # Load the Jinja2 template
        html_content = template.render(
            data=data,
            order_placed_date=next_date.strftime("%Y-%m-%d"),
            day_name=next_date.strftime("%A"),  # e.g., Saturday
        )
        # Render the template with dynamic data
        # Generate PDF in memory
        pdf_data = pdfkit.from_string(html_content, False, options=PDF_KIT_OPTIONS)
        pdf_file = BytesIO(pdf_data)
        # Generate unique file name with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        s3_file_name = f"invoice/{file_name}_{timestamp}.pdf"
        # Upload PDF to S3
        s3_client.upload_fileobj(
            pdf_file,
            settings.S3_BUCKET_NAME,
            s3_file_name,
            ExtraArgs={"ContentType": "application/pdf"},
        )

        # Generate public URL
        s3_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_file_name}"
        print("s3_url", s3_url)
        # Optionally update payment details in the database
        # Step 1: Fetch the order
        order = db.query(Orders).filter(Orders.txn_id == order_id).first()
        # Step 2: Check if the order exists
        if not order:
            raise Exception("Order not found")
        # Step 3: Update invoice_id
        order.invoice = s3_url
        # Step 4: Commit the change
        db.commit()
        db.refresh(order)  # Optional: Refresh to get updated values
        # update_payment_receipt_details(db=db, payment_log_id=payment_id, payment_receipt_url=s3_url)
        return s3_url

    except Exception as e:
        print(f"Error generating and uploading PDF: {e}")
        raise
