import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from datetime import datetime, timedelta

INVOICE_DIR = os.getenv("INVOICE_STORAGE_PATH", "./invoices")
os.makedirs(INVOICE_DIR, exist_ok=True)

# Store details
STORE_NAME = "Dhanvan-SageAI Pharmacy"
STORE_ADDRESS = "Swargate, Pune, Maharashtra 411042"
STORE_PHONE = "+91 98765 43210"
STORE_EMAIL = "support@dhanvan-sage.ai"
STORE_GSTIN = "27AABCD1234E1Z5"

# Default medicine prices (for demo)
DEFAULT_PRICES = {
    "azee": 85.00, "azee 250": 85.00, "azithromycin": 85.00,
    "pacimal": 25.00, "pacimal 650": 25.00, "paracetamol": 18.00,
    "mijpan dsr": 120.00, "migpan dsr": 120.00,
    "levosiz m": 55.00, "levoflox": 55.00, "levoflox m": 55.00,
    "ascoril d": 95.00, "ascoril d plus": 110.00,
    "alegra 120": 145.00, "alegra": 145.00,
    "wysolone": 35.00, "wysolone 10": 35.00,
    "pacimol 650": 22.00, "pacimol": 22.00,
    "ibuprofen": 30.00, "lisinopril": 65.00, "amlodipine": 45.00,
    "amoxicillin": 60.00, "cetirizine": 20.00, "omeprazole": 40.00,
    "metformin": 35.00, "atorvastatin": 75.00,
}

def get_medicine_price(name: str) -> float:
    """Get a realistic price for a medicine, fallback to estimate."""
    lower = name.lower().strip()
    if lower in DEFAULT_PRICES:
        return DEFAULT_PRICES[lower]
    # Try partial match
    for key, price in DEFAULT_PRICES.items():
        if key in lower or lower in key:
            return price
    # Default price for unknown medicines
    return 50.00


async def generate_invoice_pdf(order: dict, pharmacist_name: str = "System Auto-Approval", license_num: str = "PHAR-123456"):
    """Generate a single-item invoice (backward compatible)."""
    # Assign price if missing
    if not order.get("unit_price") or order["unit_price"] == 0:
        order["unit_price"] = get_medicine_price(order.get("medicine_name", ""))
        order["total_price"] = order["unit_price"] * order.get("quantity", 1)
    
    items = [{
        "name": order.get("medicine_name", "N/A"),
        "dosage": order.get("dosage_frequency", "As prescribed"),
        "quantity": order.get("quantity", 1),
        "unit_price": float(order.get("unit_price", 0)),
    }]
    return await _generate_pdf(order, items, pharmacist_name, license_num)


async def generate_consolidated_invoice(orders: list, patient_info: dict, rx_info: dict, pharmacist_name: str = "Dhanvan AI Pipeline", license_num: str = "AI-001"):
    """Generate a SINGLE consolidated invoice for ALL prescription medicines."""
    invoice_id = f"RX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    combined_order = {
        "order_id": invoice_id,
        "invoice_id": invoice_id,
        "patient_name": patient_info.get("name", "N/A"),
        "patient_id": patient_info.get("patient_id", "N/A"),
        "doctor_name": rx_info.get("doctor_name", "N/A"),
        "prescription_image_url": rx_info.get("image_url"),
        "purchase_date": datetime.now(),
        "delivery_address": patient_info.get("address", {}),
    }
    
    items = []
    for o in orders:
        price = get_medicine_price(o.get("medicine", o.get("medicine_name", "")))
        items.append({
            "name": o.get("medicine", o.get("medicine_name", "N/A")),
            "dosage": o.get("dosage_frequency", o.get("frequency", "As prescribed")),
            "quantity": o.get("quantity", 1),
            "unit_price": price,
        })
    
    path = await _generate_pdf(combined_order, items, pharmacist_name, license_num)
    return path, invoice_id


async def _generate_pdf(order: dict, items: list, pharmacist_name: str, license_num: str):
    """Core PDF generation with multi-item support."""
    invoice_id = order.get("invoice_id", order.get("order_id", "INV-000"))
    file_path = os.path.join(INVOICE_DIR, f"{invoice_id}.pdf")
    
    width, height = A4
    c = canvas.Canvas(file_path, pagesize=A4)
    
    # Colors
    PRIMARY = colors.HexColor("#1a5c4c")
    ACCENT = colors.HexColor("#2d8b73")
    LIGHT_BG = colors.HexColor("#f0f7f5")
    DARK_TEXT = colors.HexColor("#1a1a1a")
    GRAY_TEXT = colors.HexColor("#666666")
    
    y = height - 40
    
    # ═══════════ HEADER BANNER ═══════════
    c.setFillColor(PRIMARY)
    c.rect(0, y - 60, width, 70, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, y - 25, STORE_NAME)
    c.setFont("Helvetica", 8)
    c.drawString(40, y - 42, f"{STORE_ADDRESS}  |  {STORE_PHONE}  |  {STORE_EMAIL}")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 40, y - 20, "TAX INVOICE")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 40, y - 35, f"# INV-{invoice_id}")
    c.drawRightString(width - 40, y - 48, f"GSTIN: {STORE_GSTIN}")
    
    y -= 80
    
    # ═══════════ DATE & ORDER INFO ═══════════
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 10)
    
    purchase_date = order.get("purchase_date")
    if isinstance(purchase_date, datetime):
        date_str = purchase_date.strftime("%d %b %Y, %I:%M %p")
    else:
        date_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    
    c.drawString(40, y, f"Date: {date_str}")
    c.drawRightString(width - 40, y, f"Order ID: {order.get('order_id', invoice_id)}")
    
    y -= 30
    
    # ═══════════ PATIENT & PRESCRIPTION (Two Columns) ═══════════
    box_h = 80
    half_w = (width - 90) / 2
    
    # Left: Patient
    c.setFillColor(LIGHT_BG)
    c.roundRect(35, y - box_h, half_w, box_h + 5, 6, fill=True, stroke=False)
    
    # Right: Prescription
    c.roundRect(45 + half_w, y - box_h, half_w, box_h + 5, 6, fill=True, stroke=False)
    
    col_l = 45
    col_r = 55 + half_w
    
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(col_l, y - 5, "Patient Details")
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica", 9)
    c.drawString(col_l, y - 22, f"Name: {order.get('patient_name', 'N/A')}")
    c.drawString(col_l, y - 36, f"Patient ID: {order.get('patient_id', 'N/A')}")
    addr = order.get("delivery_address", {})
    if isinstance(addr, dict) and addr.get("street"):
        c.drawString(col_l, y - 50, f"Address: {addr.get('street', '')}, {addr.get('city', '')}")
        c.drawString(col_l, y - 64, f"         {addr.get('postal_code', '')} {addr.get('country', '')}")
    else:
        c.drawString(col_l, y - 50, "Address: Shivaji Chawk, Latur")
    
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(col_r, y - 5, "Prescription Info")
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica", 9)
    c.drawString(col_r, y - 22, f"Doctor: {order.get('doctor_name') or 'Dr. Harsh Kale'}")
    rx_ref = order.get("prescription_image_url")
    c.drawString(col_r, y - 36, f"Rx Ref: {rx_ref if rx_ref else 'Verified ' + date_str.split(',')[0]}")
    c.drawString(col_r, y - 50, f"Total Items: {len(items)}")
    
    y -= box_h + 20
    
    # ═══════════ ITEMS TABLE ═══════════
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Medicines Ordered")
    y -= 15
    
    # Build table
    table_data = [["#", "Medicine Name", "Dosage/Frequency", "Qty", "Unit Price (₹)", "Total (₹)"]]
    grand_total = 0.0
    
    for idx, item in enumerate(items, 1):
        qty = int(item.get("quantity", 1))
        unit_p = float(item.get("unit_price", 0))
        total_p = unit_p * qty
        grand_total += total_p
        
        table_data.append([
            str(idx),
            str(item.get("name", "N/A")),
            str(item.get("dosage", "As prescribed")),
            str(qty),
            f"{unit_p:.2f}",
            f"{total_p:.2f}"
        ])
    
    col_widths = [25, 160, 110, 35, 85, 80]
    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        # Alternate row colors
        *[('BACKGROUND', (0, i), (-1, i), colors.white) for i in range(2, len(table_data), 2)],
    ]))
    
    table_h = len(table_data) * 22
    tbl.wrapOn(c, width, height)
    tbl.drawOn(c, 40, y - table_h)
    
    y -= table_h + 20
    
    # ═══════════ TOTALS BOX ═══════════
    tax = grand_total * 0.05
    final_total = grand_total + tax
    
    c.setFillColor(LIGHT_BG)
    c.roundRect(width - 250, y - 65, 210, 70, 6, fill=True, stroke=False)
    
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 100, y - 8, "Subtotal:")
    c.drawRightString(width - 50, y - 8, f"₹{grand_total:.2f}")
    c.drawRightString(width - 100, y - 24, "Tax (GST 5%):")
    c.drawRightString(width - 50, y - 24, f"₹{tax:.2f}")
    
    c.setStrokeColor(PRIMARY)
    c.line(width - 245, y - 35, width - 45, y - 35)
    
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(PRIMARY)
    c.drawRightString(width - 100, y - 52, "Grand Total:")
    c.drawRightString(width - 50, y - 52, f"₹{final_total:.2f}")
    
    y -= 85
    
    # ═══════════ PAYMENT & DELIVERY ═══════════
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica", 9)
    payment = order.get("payment_info", {})
    if isinstance(payment, dict) and payment:
        c.drawString(40, y, f"Payment: {payment.get('method', 'Cash').title()} ({payment.get('status', 'pending').title()})")
    else:
        c.drawString(40, y, "Payment: Cash on Delivery")
    
    est_deliv = datetime.now() + timedelta(days=2)
    c.drawString(40, y - 15, f"Estimated Delivery: {est_deliv.strftime('%d %b %Y')}")
    
    y -= 45
    
    # ═══════════ PHARMACIST APPROVAL ═══════════
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.line(40, y, width - 40, y)
    y -= 25
    
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Approved By")
    c.setFont("Helvetica", 9)
    c.drawString(40, y - 15, f"Pharmacist: {pharmacist_name}")
    c.drawString(40, y - 30, f"License No: {license_num}")
    
    c.setStrokeColor(GRAY_TEXT)
    c.setDash(2, 2)
    c.line(width - 200, y - 30, width - 50, y - 30)
    c.setDash()
    c.setFillColor(GRAY_TEXT)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width - 125, y - 42, "Authorized Signature")
    
    # ═══════════ FOOTER ═══════════
    c.setFillColor(PRIMARY)
    c.rect(0, 0, width, 35, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, 18, f"{STORE_NAME}  |  {STORE_ADDRESS}  |  {STORE_PHONE}")
    c.drawCentredString(width / 2, 8, "This is a computer-generated invoice. No signature is required for orders under ₹5000.")
    
    c.save()
    return file_path
