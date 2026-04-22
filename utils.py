import io
import qrcode
from datetime import datetime
from sqlalchemy import or_

from app import db
from models import Appliance, RetestRule

# ---------------------------------------------------------
# Asset Number Prefixes
# ---------------------------------------------------------

ASSET_PREFIXES = {
    "PORTABLE": "P",
    "FIXED": "F",
    "CONSTRUCTION": "C",
    "OTHER": "A",   # fallback prefix
}

# ---------------------------------------------------------
# Asset Number Generator
# ---------------------------------------------------------

def generate_asset_number(supply_type="OTHER"):
    """
    Generate a unique asset number based on:
    - Prefix (based on supply type)
    - Timestamp (YYMMDD-HHMMSS)
    - Optional sequential suffix if collision occurs
    """
    prefix = ASSET_PREFIXES.get(supply_type.upper(), "A")
    base = prefix + datetime.now().strftime("%y%m%d-%H%M%S")

    # Check for collisions
    exists = Appliance.query.filter_by(asset_number=base).first()
    if not exists:
        return base

    # If collision, append sequential suffix
    suffix = 1
    while True:
        candidate = f"{base}-{suffix}"
        if not Appliance.query.filter_by(asset_number=candidate).first():
            return candidate
        suffix += 1

# ---------------------------------------------------------
# Fuzzy Search Helper
# ---------------------------------------------------------

def fuzzy(term):
    """
    Converts a search term into a fuzzy SQL LIKE pattern.
    Example:
        'ketle' -> '%k%e%t%l%e%'
    """
    return "%" + "%".join(term.lower()) + "%"

# ---------------------------------------------------------
# Retest Interval Logic
# ---------------------------------------------------------

def get_suggested_interval(class_type, supply_type):
    """
    Returns the best matching retest rule based on:
    - Appliance class
    - Supply type
    Falls back to ANY rules if no exact match exists.
    """
    rule = RetestRule.query.filter_by(
        class_type=class_type,
        supply_type=supply_type
    ).first()

    if rule:
        return rule

    # Try class ANY
    rule = RetestRule.query.filter_by(
        class_type="ANY",
        supply_type=supply_type
    ).first()

    if rule:
        return rule

    # Try supply ANY
    rule = RetestRule.query.filter_by(
        class_type=class_type,
        supply_type="ANY"
    ).first()

    if rule:
        return rule

    # Final fallback
    return RetestRule.query.filter_by(
        class_type="ANY",
        supply_type="ANY"
    ).first()

# ---------------------------------------------------------
# Test Summary Helper
# ---------------------------------------------------------

def summarize_test_types(tests):
    """
    Returns a summary of test types for display on appliance detail page.
    Example:
        {'3760': 5, '5761': 2}
    """
    summary = {}
    for t in tests:
        summary[t.test_standard] = summary.get(t.test_standard, 0) + 1
    return summary

# ---------------------------------------------------------
# QR Code Generator
# ---------------------------------------------------------

def generate_qr_code(url):
    """
    Generates a QR code PNG as a base64-encoded string for embedding in PDFs.
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
