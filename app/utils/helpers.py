import uuid
import datetime


def generate_order_id():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4()).split("-")[0].upper()  # Short unique string
    return f"ORD-{timestamp}-{random_part}"


def get_c_gst_s_gst(total_amount, setting_details):
    """
    Calculates CGST, SGST, and subtotal from the total amount.
    Assumes total_amount includes GST (split equally as CGST and SGST)
    if pricesWithTax is 'yes'. Returns a dict with:
    - subtotal
    - cgst
    - sgst
    - cgst_rate
    - sgst_rate
    """
    result = {
        "subtotal": round(total_amount, 2),
        "cgst": 0.0,
        "sgst": 0.0,
        "cgst_rate": 0.0,
        "sgst_rate": 0.0,
    }

    if getattr(setting_details, "pricesWithTax", "no") == "yes":
        gst_rate = getattr(setting_details, "taxRate", 0)  # e.g., 18
        gst_decimal = gst_rate / 100.0
        cgst_rate = sgst_rate = gst_decimal / 2

        subtotal = total_amount / (1 + gst_decimal)
        subtotal_rounded = round(subtotal, 2)

        # First calculate CGST
        cgst = round(subtotal_rounded * cgst_rate, 2)

        # Ensure total matches exactly by computing SGST as remainder
        sgst = round(total_amount - subtotal_rounded - cgst, 2)

        result = {
            "subtotal": subtotal_rounded,
            "cgst": cgst,
            "sgst": sgst,
            "cgst_rate": round(cgst_rate, 2),
            "sgst_rate": round(sgst_rate, 2),
        }

    return result
