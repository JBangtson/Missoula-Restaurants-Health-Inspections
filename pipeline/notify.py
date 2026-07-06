"""
Gmail alert for Critical / High violations found in new inspections.

Uses smtplib with a Gmail App Password (Settings → Security → App passwords).
Env vars: GMAIL_SENDER, GMAIL_APP_PASSWORD, ALERT_RECIPIENT
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from storage import Storage

ALERTS_LOG_PATH = "alerts/log/{date}.json"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def should_notify(classified: list[dict]) -> bool:
    return any(
        v.get("classification", {}).get("severity") in ("Critical", "High")
        for insp in classified
        for v in insp.get("violations", [])
    )


def send_alert(classified: list[dict], date_str: str):
    if not all(os.environ.get(k) for k in ("GMAIL_SENDER", "GMAIL_APP_PASSWORD", "ALERT_RECIPIENT")):
        print("Notify: Gmail not configured, skipping email (set GMAIL_SENDER, GMAIL_APP_PASSWORD, ALERT_RECIPIENT)")
        return

    critical_high = [
        {
            "place_id": insp.get("place_id", ""),
            "date": insp.get("date", ""),
            "type": insp.get("type", ""),
            "violations": [
                v for v in insp.get("violations", [])
                if v.get("classification", {}).get("severity") in ("Critical", "High")
            ],
        }
        for insp in classified
        if any(
            v.get("classification", {}).get("severity") in ("Critical", "High")
            for v in insp.get("violations", [])
        )
    ]

    subject = f"[Missoula Food Safety] {len(critical_high)} inspection(s) with Critical/High violations — {date_str}"
    body = _build_email_body(critical_high, date_str)

    sender = os.environ["GMAIL_SENDER"]
    recipient = os.environ["ALERT_RECIPIENT"]
    password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Notify: alert sent to {recipient} ({len(critical_high)} inspection(s))")


def log_alert(storage: Storage, classified: list[dict], date_str: str):
    path = ALERTS_LOG_PATH.format(date=date_str)
    storage.write_json(path, classified)
    print(f"Notify: alert logged to {path}")


def _build_email_body(inspections: list[dict], date_str: str) -> str:
    lines = [f"Missoula Food Safety Alert — {date_str}", "=" * 50, ""]
    for insp in inspections:
        lines.append(f"Place ID: {insp['place_id']}")
        lines.append(f"Date: {insp['date']}  Type: {insp['type']}")
        lines.append("Violations:")
        for v in insp["violations"]:
            sev = v.get("classification", {}).get("severity", "?")
            reasoning = v.get("classification", {}).get("reasoning", "")
            lines.append(f"  [{sev}] {v.get('code', '')} — {v.get('description', '')}")
            lines.append(f"    {reasoning}")
        lines.append("")
    return "\n".join(lines)
