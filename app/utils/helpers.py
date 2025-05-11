import uuid
import datetime

def generate_order_id():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = str(uuid.uuid4()).split('-')[0].upper()  # Short unique string
    return f"ORD-{timestamp}-{random_part}"
