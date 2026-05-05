import io
import os
import tempfile

import qrcode
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions (before final 90° rotation).
# Height = 62mm tape printable width (696px ≈ 58mm).
# Width  = label length (~110mm).
CANVAS_W = 1300
CANVAS_H = 696

# Cord-wrap geometry.
# The cord zone is a VERTICAL band in the canvas.  After the final 90° CCW
# rotation the band becomes HORIZONTAL in the printed output, centred along
# the label length — so the label folds top-to-bottom around the cord.
#
#   CORD_GAP   — width of the vertical band (160px ≈ 14mm, fits ≤12mm cord)
#   CONTENT_W  — width of each content panel left/right of the band
CORD_GAP  = 160
CONTENT_W = (CANVAS_W - CORD_GAP) // 2   # 570px ≈ 48mm

QR_SIZE = 300   # fits comfortably in the 570×696 panel

_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    path = _FONT_BOLD if bold else _FONT_REG
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _fit(text: str, bold: bool, max_w: int, start: int) -> ImageFont.FreeTypeFont:
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    size  = start
    while size > 10:
        f = _font(bold, size)
        if probe.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        size -= 2
    return _font(bold, 10)


def _centered_text(draw: ImageDraw.ImageDraw, y: int, text: str,
                   font: ImageFont.FreeTypeFont, fill: str,
                   panel_w: int = CONTENT_W) -> int:
    """Draw text centred horizontally; return the y coordinate of the bottom edge."""
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (panel_w - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return draw.textbbox((x, y), text, font=font)[3]


def _dashed_vline(draw: ImageDraw.ImageDraw, x: int,
                  color: str, width: int = 2, dash: int = 14) -> None:
    y, on = 0, True
    while y < CANVAS_H:
        end = min(y + dash, CANVAS_H)
        if on:
            draw.line([(x, y), (x, end)], fill=color, width=width)
        y, on = end, not on


# ── Side A — Identity ─────────────────────────────────────────────────────────
# Shows asset number, description, and a large QR code.
# Printed at the BOTTOM of the physical label (this panel is pre-rotated 180°
# in the canvas so it reads correctly from the back face after folding).

def _side_a(test, config: dict, qr_img: Image.Image) -> Image.Image:
    panel = Image.new("RGB", (CONTENT_W, CANVAS_H), "white")
    draw  = ImageDraw.Draw(panel)
    max_w = CONTENT_W - 20

    y = 18

    # Asset number
    asset      = test.appliance.asset_number or ""
    asset_font = _fit(asset, True, max_w, 80)
    y = _centered_text(draw, y, asset, asset_font, "black") + 10

    # Description
    desc = test.appliance.description or ""
    if desc:
        desc_font = _fit(desc, False, max_w, 34)
        y = _centered_text(draw, y, desc, desc_font, "#333333") + 10

    # QR code — centred in the remaining vertical space
    qr_x = (CONTENT_W - QR_SIZE) // 2
    qr_y = y + max(0, (CANVAS_H - y - QR_SIZE - 10) // 2)
    panel.paste(qr_img.copy(), (qr_x, qr_y))
    y = qr_y + QR_SIZE + 8

    # Make / model (if present), small footer
    make = test.appliance.make_model or ""
    if make:
        make_font = _fit(make, False, max_w, 24)
        _centered_text(draw, min(y, CANVAS_H - 32), make, make_font, "#888888")

    return panel


# ── Side B — Results ──────────────────────────────────────────────────────────
# Shows PASS/FAIL, dates, standard, and tester.
# Printed at the TOP of the physical label — readable from the front face.

def _side_b(test, config: dict) -> Image.Image:
    panel  = Image.new("RGB", (CONTENT_W, CANVAS_H), "white")
    draw   = ImageDraw.Draw(panel)
    is_red = config.get("BROTHER_RED", "false").lower() == "true"
    max_w  = CONTENT_W - 20

    y = 20

    # PASS / FAIL — dominant
    result      = (test.overall_result or "").upper()
    result_font = _fit(result, True, max_w, 130)
    result_color = ("red" if is_red else "black") if result == "FAIL" else "black"
    y = _centered_text(draw, y, result, result_font, result_color) + 14

    # Test date and next due
    date_parts = []
    if test.test_date:
        date_parts.append(f"Tested: {test.test_date.strftime('%d/%m/%Y')}")
    if test.next_test_due:
        date_parts.append(f"Due: {test.next_test_due.strftime('%d/%m/%Y')}")
    if date_parts:
        date_font = _font(False, 30)
        y = _centered_text(draw, y, "  |  ".join(date_parts), date_font, "black") + 10

    # Standard
    if test.test_standard:
        std_font = _font(False, 28)
        y = _centered_text(draw, y, f"Tested to AS/NZS {test.test_standard}", std_font, "#333333") + 10

    # Tester + certificate
    if test.tester:
        tester_str = test.tester.full_name or ""
        if test.tester.certificate_number:
            tester_str += f" ({test.tester.certificate_number})"
        if tester_str:
            tester_font = _font(False, 26)
            _centered_text(draw, y, tester_str, tester_font, "#555555")

    return panel


# ── Main builder ──────────────────────────────────────────────────────────────

def build_label_image(test, config: dict) -> bytes:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")

    # QR code for Side A
    base_url = config.get("BASE_URL", "").rstrip("/")
    qr_url   = f"{base_url}/test/{test.id}" if base_url else f"/test/{test.id}"
    qr_img   = qrcode.make(qr_url).convert("RGB").resize((QR_SIZE, QR_SIZE))

    # ── Left panel: Side A, rotated 180° ─────────────────────────────────────
    # After the final CCW rotation this panel lands at the BOTTOM of the printed
    # label.  Pre-rotating 180° ensures it reads correctly from the back face
    # after the label is folded over the cord.
    img.paste(_side_a(test, config, qr_img).rotate(180), (0, 0))

    # ── Vertical cord zone ────────────────────────────────────────────────────
    cord_x1 = CONTENT_W               # 570
    cord_x2 = CONTENT_W + CORD_GAP    # 730
    draw = ImageDraw.Draw(img)
    draw.rectangle([cord_x1, 0, cord_x2, CANVAS_H], fill="#ebebeb")
    _dashed_vline(draw, cord_x1,     "#999999", width=2, dash=14)
    _dashed_vline(draw, cord_x2 - 1, "#999999", width=2, dash=14)

    # ── Right panel: Side B, normal orientation ───────────────────────────────
    # After the final CCW rotation this panel lands at the TOP of the printed
    # label — readable from the front face without any further rotation.
    img.paste(_side_b(test, config), (cord_x2, 0))

    # ── Final 90° CCW rotation ────────────────────────────────────────────────
    # Converts the 1300×696 canvas to the 696×1300 image the Brother QL expects.
    # The vertical cord zone (x=570..729) becomes a horizontal band at
    # y=570..729 — exactly centred in the 1300px label length.
    img = img.rotate(90, expand=True)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def print_label(img_bytes: bytes, config: dict) -> None:
    from brother_ql.backends.helpers import send
    from brother_ql.conversion import convert
    from brother_ql.raster import BrotherQLRaster

    qlr = BrotherQLRaster(config["BROTHER_MODEL"])
    qlr.exception_on_warning = True

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(img_bytes)
        tmp_path = tmp.name

    try:
        instructions = convert(
            qlr=qlr,
            images=[tmp_path],
            label=config.get("BROTHER_LABEL", "62"),
            rotate="auto",
            threshold=70.0,
            dither=False,
            compress=False,
            red=config.get("BROTHER_RED", "false").lower() == "true",
            dpi_600=False,
            hq=True,
            cut=True,
        )
        send(
            instructions=instructions,
            printer_identifier=config["BROTHER_PRINTER"],
            backend_identifier="network",
            blocking=True,
        )
    finally:
        os.unlink(tmp_path)
