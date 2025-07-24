#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate guest QR landing pages and a result CSV/XLSX with public links."""

from __future__ import annotations
import pandas as pd
from pathlib import Path
from urllib.parse import urljoin
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image

# ─────────── CONFIG ──────────────────────────────────────────────────────
INPUT_FILE  = Path("data") / "guests.csv"      
OUTPUT_DIR  = Path("output") / "guest_pages"
QR_DIR      = OUTPUT_DIR / "qr"

RESULT_CSV  = OUTPUT_DIR / "result.csv"
RESULT_XLSX = OUTPUT_DIR / "result.xlsx"    

BASE_URL = "https://shady-mo20.github.io/qr/" 

# ─────────── HTML TEMPLATE ───────────────────────────────────────────────
CARD_TEMPLATE = """
<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <title>{name}</title>
  </head>
  <body class='bg-light d-flex justify-content-center align-items-center vh-100'>
    <div class='card shadow-sm' style='width: 22rem;'>
      <img src='qr/{qr_filename}' class='card-img-top p-3' alt='QR code'
           style='border-radius:8px;box-shadow:0 0.5rem 1rem rgba(0,0,0,0.15);'>
      <div class='card-body text-center'>
        <h4 class='card-title'>{name}</h4>
        <h6 class='card-subtitle mb-2 text-muted'>Guest ID #{guest_id}</h6>
        <p class='card-text'><a href='tel:{phone_link}'>{phone_display}</a></p>
        <a href='https://wa.me/{phone_link}' class='btn btn-success'>Chat on WhatsApp</a>
      </div>
    </div>
  </body>
</html>
"""

# ─────────── HELPERS ─────────────────────────────────────────────────────
def clean_phone(phone: str) -> str:
    """Strip +, spaces, dashes, parentheses from phone number."""
    return (
        phone.replace("+", "")
             .replace("-", "")
             .replace(" ", "")
             .replace("(", "")
             .replace(")", "")
    )

def make_qr(data: str, outfile: Path) -> None:
    """Create a high‑quality coloured QR code PNG (600×600)."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="#128C7E", back_color="white")
    img = img.resize((600, 600), Image.LANCZOS)
    img.save(outfile)

# ─────────── CORE LOGIC ──────────────────────────────────────────────────
def generate_pages(df: pd.DataFrame) -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    QR_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for idx, row in df.iterrows():
        name  = str(row["Name"]).strip()
        phone = str(row["phone"]).strip()
        phone_clean = clean_phone(phone)
        wa_link = f"https://wa.me/{phone_clean}"

        # ---- QR content: identity + WhatsApp -----------------------------
        qr_content = (
            f"Guest ID: {idx + 1}\n"
            f"Name: {name}\n"
            f"Phone: {phone}\n"
            f"WhatsApp: {wa_link}"
        )
        qr_filename = f"guest_{idx + 1}.png"
        make_qr(qr_content, QR_DIR / qr_filename)

        # ---- HTML page ----------------------------------------------------
        html_filename = f"guest_{idx + 1}.html"
        (OUTPUT_DIR / html_filename).write_text(
            CARD_TEMPLATE.format(
                name=name,
                guest_id=idx + 1,
                phone_link=phone_clean,
                phone_display=phone,
                qr_filename=qr_filename,
            ),
            encoding="utf-8",
        )

        # ---- public link for CSV -----------------------------------------
        public_link = urljoin(BASE_URL, html_filename)

        rows.append({
            "phone": phone,
            "name":  name,
            "Param1": public_link,
        })

    return pd.DataFrame(rows)

def main() -> None:
    df_in  = pd.read_csv(INPUT_FILE)
    df_out = generate_pages(df_in)
    df_out.to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
    df_out.to_excel(RESULT_XLSX, index=False)
    print(f"✅ Generated {len(df_out)} pages  →  {OUTPUT_DIR}")
    print(f"📝 Result file with public links →  {RESULT_CSV}")

if __name__ == "__main__":
    main()