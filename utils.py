import io
import base64
import qrcode
from datetime import datetime
from qrcode.image.pil import PilImage


# ---------------------------------------------------------
# Format Test Standard (3760 → AS/NZS 3760)
# ---------------------------------------------------------
def format_standard(code: str) -> str:
    """
    Converts a numeric standard code (e.g., '3760') into
    a fully formatted standard string: 'AS/NZS 3760'.
    """
    if not code:
        return ""
    return f"AS/NZS {code}"


# ---------------------------------------------------------
# Fuzzy search helper
# ---------------------------------------------------------
def fuzzy(q: str) -> str:
    return f"%{q}%"


def make_snippet(text: str, q: str, context: int = 80) -> str:
    if not text:
        return '—'
    idx = text.lower().find(q.lower())
    if idx == -1:
        return (text[:100] + '…') if len(text) > 100 else text
    start = max(0, idx - context // 2)
    end = min(len(text), idx + len(q) + context // 2)
    result = text[start:end]
    if start > 0:
        result = '…' + result
    if end < len(text):
        result = result + '…'
    return result


# ---------------------------------------------------------
# Suggested retest interval lookup
# ---------------------------------------------------------
def get_suggested_interval(class_type: str, supply_type: str):
    """
    Returns the recommended retest interval rule object
    based on class_type and supply_type.
    """
    from models import RetestRule  # local import to avoid circular dependency

    rule = RetestRule.query.filter_by(
        class_type=class_type,
        supply_type=supply_type
    ).first()

    if rule:
        return rule

    # fallback: ANY class, ANY supply
    return RetestRule.query.filter_by(
        class_type="ANY",
        supply_type="ANY"
    ).first()


# ---------------------------------------------------------
# Summarize test types for appliance detail page
# ---------------------------------------------------------
def summarize_test_types(tests):
    """
    Returns a dictionary summarizing test counts by standard.
    """
    summary = {}
    for t in tests:
        summary[t.test_standard] = summary.get(t.test_standard, 0) + 1
    return summary


# ---------------------------------------------------------
# QR Code generator for PDF exports
# ---------------------------------------------------------
def generate_qr_code(url: str) -> str:
    """
    Generates a base64 PNG QR code for embedding in PDFs.
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return encoded
