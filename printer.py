import csv
import io
import ipaddress
import os
import re
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# POST /printer/discover  — TCP port 9100 subnet scan
# ─────────────────────────────────────────────────────────────

@bp.route("/printer/discover", methods=["POST"])
def discover():
    body   = request.get_json(silent=True) or {}
    subnet = (body.get("subnet") or "").strip()

    candidates: set[str] = set()

    if subnet:
        try:
            candidates.update(_scan_subnet(subnet))
        except ValueError:
            return jsonify({"error": "Invalid subnet — use CIDR notation, e.g. 192.168.1.0/24"}), 400

    if not candidates:
        return jsonify([])

    results = []
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {pool.submit(_fetch_printer_info, ip): ip for ip in candidates}
        for future in as_completed(futures):
            info = future.result()
            if info:
                ip = futures[future]
                results.append({
                    "address":  f"tcp://{ip}",
                    "name":     info["name"],
                    "model":    info["model"],
                    "serial":   info["serial"],
                    "firmware": info["firmware"],
                })

    return jsonify(results)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _scan_subnet(cidr: str) -> list[str]:
    net = ipaddress.ip_network(cidr, strict=False)
    if net.num_addresses > 65536:
        raise ValueError("Subnet too large (max /16)")

    def _probe(ip):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            rc = s.connect_ex((str(ip), 9100))
            s.close()
            return str(ip) if rc == 0 else None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=100) as pool:
        return [ip for ip in pool.map(_probe, net.hosts()) if ip is not None]


def _fetch_printer_info(ip: str) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://{ip}/etc/mnt_info.csv", timeout=2) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        row = next(csv.DictReader(io.StringIO(text)))
        return {
            "model":    row["Model Name"].strip(),
            "name":     row["Node Name"].strip(),
            "serial":   row["Serial No."].strip(),
            "firmware": row["Firmware Version"].strip(),
        }
    except Exception:
        return None


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
