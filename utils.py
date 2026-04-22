import base64
from io import BytesIO
import qrcode
from sqlalchemy import or_
from app import db
from models import RetestRule

def generate_qr_code(url: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"

def fuzzy(term: str) -> str:
    if not term:
        return "%"
    return "%" + "%".join(term) + "%"

def get_suggested_interval(class_type: str, supply_type: str):
    if not class_type:
        class_type = "ANY"
    if not supply_type:
        supply_type = "ANY"
    class_type = class_type.upper().strip()
    supply_type = supply_type.upper().strip()

    rule = (
        RetestRule.query
        .filter(
            or_(RetestRule.class_type == class_type, RetestRule.class_type == "ANY"),
            or_(RetestRule.supply_type == supply_type, RetestRule.supply_type == "ANY")
        )
        .order_by(RetestRule.priority.desc())
        .first()
    )
    return rule

def summarize_test_types(tests):
    summary = {}
    for t in tests:
        std = t.test_standard or "3760"
        if std not in summary:
            summary[std] = {"count": 0, "latest": t.test_date}
        summary[std]["count"] += 1
        if t.test_date > summary[std]["latest"]:
            summary[std]["latest"] = t.test_date
    return summary
