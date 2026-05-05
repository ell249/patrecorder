import os
import re
import socket

from flask import (
    Blueprint, current_app, flash, jsonify,
    redirect, request, url_for,
)

bp = Blueprint("printer", __name__)

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")


# ─────────────────────────────────────────────────────────────
# POST /printer  — save settings to config.py + reload in-process
# ─────────────────────────────────────────────────────────────

@bp.route("/printer", methods=["POST"])
def save():
    fields = {
        "BROTHER_PRINTER": request.form.get("brother_printer", "").strip(),
        "BROTHER_MODEL":   request.form.get("brother_model", "").strip(),
        "BROTHER_LABEL":   request.form.get("brother_label", "62").strip(),
        "BROTHER_RED":     request.form.get("brother_red", "false").strip(),
        "BASE_URL":        request.form.get("base_url", "").strip(),
    }

    try:
        _write_config(fields)
    except Exception as exc:
        flash(f"Could not write config.py: {exc}", "danger")
        return redirect(url_for("setup.status"))

    for key, value in fields.items():
        current_app.config[key] = value

    flash("Printer settings saved.", "success")
    return redirect(url_for("setup.status"))


# ─────────────────────────────────────────────────────────────
# POST /printer/discover  — mDNS/Bonjour scan (~3 s)
# ─────────────────────────────────────────────────────────────

@bp.route("/printer/discover", methods=["POST"])
def discover():
    try:
        from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    except ImportError:
        return jsonify({"error": "zeroconf package not installed"}), 500

    import time
    import socket as _socket

    class _Listener(ServiceListener):
        def __init__(self):
            self.found = []

        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if not info or not info.addresses:
                return
            try:
                ip = _socket.inet_ntoa(info.addresses[0])
            except Exception:
                return
            self.found.append({
                "address": f"tcp://{ip}",
                "name": info.server.rstrip(".") if info.server else ip,
            })

        def remove_service(self, *_):
            pass

        def update_service(self, *_):
            pass

    listener = _Listener()
    zc = Zeroconf()
    try:
        ServiceBrowser(zc, "_pdl-datastream._tcp.local.", listener)
        ServiceBrowser(zc, "_printer._tcp.local.", listener)
        time.sleep(3)
    finally:
        zc.close()

    seen, results = set(), []
    for p in listener.found:
        if p["address"] not in seen:
            seen.add(p["address"])
            results.append(p)

    return jsonify(results)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def check_printer(app) -> dict:
    addr  = app.config.get("BROTHER_PRINTER", "")
    model = app.config.get("BROTHER_MODEL", "")
    result = {"address": addr, "model": model, "reachable": False, "error": None}

    if not addr:
        result["error"] = "Not configured"
        return result

    try:
        raw = addr.replace("tcp://", "").replace("//", "")
        host, _, port_str = raw.partition(":")
        port = int(port_str) if port_str else 9100
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        rc = sock.connect_ex((host, port))
        sock.close()
        result["reachable"] = rc == 0
        if rc != 0:
            result["error"] = f"TCP connect to {host}:{port} failed (code {rc})"
    except Exception as exc:
        result["error"] = str(exc)

    return result


def _write_config(fields: dict) -> None:
    with open(_CONFIG_PATH, "r") as f:
        content = f.read()

    for key, value in fields.items():
        # Match: KEY = os.environ.get("...", "old_value")
        new = re.sub(
            rf'({key}\s*=\s*os\.environ\.get\s*\([^,]+,\s*")[^"]*(")',
            rf'\g<1>{value}\2',
            content,
        )
        if new == content:
            # Match: KEY = "old_value"
            new = re.sub(rf'({key}\s*=\s*")[^"]*(")', rf'\g<1>{value}\2', content)
        content = new

    with open(_CONFIG_PATH, "w") as f:
        f.write(content)
