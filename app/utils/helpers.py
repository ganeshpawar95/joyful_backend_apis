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
        total_gst = (gst_rate / 100) * total_amount
        subtotal = int(total_amount) - total_gst
        # Ensure total matches exactly by computing SGST as remainder
        result = {
            "subtotal": subtotal,
            "cgst": total_gst / 2,
            "sgst": total_gst / 2,
            "cgst_rate": int(gst_rate / 2),
            "sgst_rate": int(gst_rate / 2),
        }

    return result


def format_amount(amount):
    try:
        if amount == 0:
            return 0
        return "{:,}".format(int(amount))
    except:
        return 0
