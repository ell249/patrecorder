import io
import os
import tempfile

import qrcode
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions (before final 90° rotation).
# Height = 62mm tape printable width (696px ≈ 58mm).
# Width  = label length (~90mm).
CANVAS_W = 1063
CANVAS_H = 696

# Cord-wrap geometry.
# The cord zone is a VERTICAL band in the canvas.  After the final 90° CCW
# rotation the band becomes HORIZONTAL in the printed output, centred along
# the label length — so the label folds top-to-bottom around the cord.
#
#   CORD_GAP   — width of the vertical band (160px ≈ 14mm, fits ≤12mm cord)
#   CONTENT_W  — width of each content panel left/right of the band
CORD_GAP    = 160
CORD_MARGIN = 40                                              # white space each side of the grey zone
CONTENT_W   = (CANVAS_W - CORD_GAP - 2 * CORD_MARGIN) // 2  # 411px ≈ 35mm
HALF_H      = CANVAS_H // 2                                  # 348px — height of each label strip

QR_SIZE = 280   # fits in the 348px-wide portrait panel (34px margin per side)

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


def _dashed_hline(draw: ImageDraw.ImageDraw, y: int,
                  color: str, width: int = 1, dash: int = 10) -> None:
    x, on = 0, True
    while x < CANVAS_W:
        end = min(x + dash, CANVAS_W)
        if on:
            draw.line([(x, y), (end, y)], fill=color, width=width)
        x, on = end, not on


def _std_lines(code: str) -> list:
    return {
        "3760": ["Inspected & Tested to", "AS/NZS 3760"],
        "5761": ["Second-hand Equipment", "Inspected & Tested to AS/NZS 5761"],
        "5762": ["Repaired, Tested &", "Inspected to AS/NZS 5762"],
    }.get(code, [f"Tested to AS/NZS {code}"])


def _cord_zone_img(text: str) -> Image.Image:
    """Return a 160×HALF_H image with centred text, ready to paste at (cord_x1, strip_y)."""
    work = Image.new("RGB", (HALF_H, CORD_GAP), "#ebebeb")
    draw = ImageDraw.Draw(work)
    font = _fit(text, True, HALF_H - 20, 28)
    bbox = draw.textbbox((0, 0), text, font=font)
    y    = max(0, (CORD_GAP - (bbox[3] - bbox[1])) // 2)
    _centered_text(draw, y, text, font, "#555555", HALF_H)
    return work.rotate(-90, expand=True)  # 90° CW → 160×HALF_H


# ── Side A — Identity ─────────────────────────────────────────────────────────
# Shows asset number, description, and a large QR code.
# Printed at the BOTTOM of the physical label (this panel is pre-rotated 180°
# in the canvas so it reads correctly from the back face after folding).

def _side_a(test, config: dict, qr_img: Image.Image) -> Image.Image:
    # Draw on a portrait surface (HALF_H × CONTENT_W = 348×570), rotate 90° CCW → 570×348.
    # Combined with the 180° pre-rotation and final 90° CCW canvas rotation the net
    # result is readable text from the back face after folding.
    panel = Image.new("RGB", (HALF_H, CONTENT_W), "white")
    draw  = ImageDraw.Draw(panel)
    max_w = HALF_H - 20
    pw    = HALF_H

    y = 14

    # Asset number
    asset      = test.appliance.asset_number or ""
    asset_font = _fit(asset, True, max_w, 60)
    y = _centered_text(draw, y, asset, asset_font, "black", pw) + 8

    # Description
    desc = test.appliance.description or ""
    if desc:
        desc_font = _fit(desc, False, max_w, 30)
        y = _centered_text(draw, y, desc, desc_font, "#333333", pw) + 8

    # QR code — centred in the remaining vertical space
    qr_x = (HALF_H - QR_SIZE) // 2
    qr_y = y + max(0, (CONTENT_W - y - QR_SIZE - 10) // 2)
    panel.paste(qr_img.copy(), (qr_x, qr_y))
    y = qr_y + QR_SIZE + 6

    # Make / model (if present), small footer
    make = test.appliance.make_model or ""
    if make:
        make_font = _fit(make, False, max_w, 20)
        _centered_text(draw, min(y, CONTENT_W - 26), make, make_font, "#888888", pw)

    return panel.rotate(90, expand=True)  # 90° CCW → 570×348


# ── Side B — Results ──────────────────────────────────────────────────────────
# Shows PASS/FAIL, dates, standard, and tester.
# Printed at the TOP of the physical label — readable from the front face.

def _side_b(test, config: dict) -> Image.Image:
    # Draw on a portrait surface (HALF_H × CONTENT_W = 348×530), rotate 90° CW → 530×348.
    # Combined with the final 90° CCW canvas rotation the net result is readable
    # text from the front face.
    panel  = Image.new("RGB", (HALF_H, CONTENT_W), "white")
    draw   = ImageDraw.Draw(panel)
    is_red = config.get("BROTHER_RED", "false").lower() == "true"
    max_w  = HALF_H - 20
    pw     = HALF_H

    y = 16

    # PASS / FAIL — dominant
    result      = (test.overall_result or "").upper()
    result_font = _fit(result, True, max_w, 120)
    result_color = ("red" if is_red else "black") if result == "FAIL" else "black"
    y = _centered_text(draw, y, result, result_font, result_color, pw) + 12

    # Test date — own line
    if test.test_date:
        s = f"Tested: {test.test_date.strftime('%d/%m/%Y')}"
        y = _centered_text(draw, y, s, _fit(s, False, max_w, 32), "black", pw) + 8

    # Next due — own line
    if test.next_test_due:
        s = f"Due: {test.next_test_due.strftime('%d/%m/%Y')}"
        y = _centered_text(draw, y, s, _fit(s, False, max_w, 32), "black", pw) + 8

    # Standard — potentially two lines
    if test.test_standard:
        for line in _std_lines(test.test_standard):
            y = _centered_text(draw, y, line, _fit(line, False, max_w, 26), "#333333", pw) + 6

    # Safety reminder
    s = "Check dates for your safety"
    y = _centered_text(draw, y, s, _fit(s, False, max_w, 22), "#444444", pw) + 8

    # Tester name and certificate on separate lines
    if test.tester:
        if test.tester.full_name:
            s = test.tester.full_name
            y = _centered_text(draw, y, s, _fit(s, False, max_w, 26), "#555555", pw) + 6
        if test.tester.certificate_number:
            s = test.tester.certificate_number
            y = _centered_text(draw, y, s, _fit(s, False, max_w, 24), "#888888", pw) + 6

    # OUT OF SERVICE — FAIL only, fills remaining space
    if result == "FAIL":
        s         = "OUT OF SERVICE"
        oos_font  = _fit(s, True, max_w, 60)
        oos_color = "red" if is_red else "black"
        _centered_text(draw, y + 8, s, oos_font, oos_color, pw)

    return panel.rotate(-90, expand=True)  # 90° CW → 530×348


# ── Main builder ──────────────────────────────────────────────────────────────

def build_label_image(test, config: dict) -> bytes:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")

    # QR code for Side A (shared by both copies)
    base_url = config.get("BASE_URL", "").rstrip("/")
    qr_url   = f"{base_url}/test/{test.id}" if base_url else f"/test/{test.id}"
    qr_img   = qrcode.make(qr_url).convert("RGB").resize((QR_SIZE, QR_SIZE))

    side_a = _side_a(test, config, qr_img)  # 570×348
    side_b = _side_b(test, config)           # 570×348

    # Grey zone sits between the two white margins
    cord_x1 = CONTENT_W + CORD_MARGIN            # start of grey zone
    cord_x2 = CONTENT_W + CORD_MARGIN + CORD_GAP # end of grey zone
    draw = ImageDraw.Draw(img)

    # ── Two label strips — left=CABLE, right=APPLIANCE ───────────────────────
    cord_labels = ["--- CABLE ---", "--- APPLIANCE ---"]
    for i, strip_y in enumerate((0, HALF_H)):
        img.paste(side_a.rotate(180), (0, strip_y))
        draw.rectangle([cord_x1, strip_y, cord_x2, strip_y + HALF_H - 1], fill="#ebebeb")
        img.paste(side_b.rotate(180) if i == 0 else side_b, (cord_x2 + CORD_MARGIN, strip_y))
        img.paste(_cord_zone_img(cord_labels[i]), (cord_x1, strip_y))

    # ── Cord zone borders (full height, shared by both strips) ────────────────
    _dashed_vline(draw, cord_x1,     "#999999", width=2, dash=14)
    _dashed_vline(draw, cord_x2 - 1, "#999999", width=2, dash=14)

    # ── Horizontal cut line between the two labels ─────────────────────────────
    # After the final 90° CCW rotation this becomes a vertical cut line at
    # x=348 — exactly down the middle of the 696px tape width.
    _dashed_hline(draw, HALF_H, "#999999", width=2, dash=10)

    # ── Final 90° CCW rotation ────────────────────────────────────────────────
    # Converts the 1300×696 canvas to the 696×1300 image the Brother QL expects.
    # The vertical cord zone becomes a horizontal band centred in the label length;
    # the horizontal cut line becomes a vertical line down the centre of the tape.
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
