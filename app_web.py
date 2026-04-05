import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import HexColor
from datetime import datetime
import os, io, random, string, re

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="ระบบใบเสนอราคา", layout="centered")

FONT_MAIN = "Helvetica"

if os.path.exists("Sarabun-Regular.ttf"):
    pdfmetrics.registerFont(TTFont("Sarabun", "Sarabun-Regular.ttf"))
    FONT_MAIN = "Sarabun"

BLUE = "#1D74E4"

# =========================
# PDF POSITION
# =========================
X_NAME, Y_NAME = 82, 696.3
X_DATE, Y_DATE = 455, 696.3
X_NO, X_ITEM, X_QTY, X_UNIT, X_PRICE, X_TOTAL = 29, 60, 389, 432.2, 513.6, 580
START_Y = 600
X_SUM, Y_SUM = 580, 191
X_SUM_TEXT, Y_SUM_TEXT = 830, 170
X_NOTE, Y_NOTE = 85, 192

ITEM_WIDTH = 300

# =========================
# STYLE PDF
# =========================
styles = getSampleStyleSheet()
style_thai = styles["Normal"]
style_thai.fontName = FONT_MAIN
style_thai.fontSize = 10
style_thai.textColor = HexColor(BLUE)
style_thai.leading = 14

# =========================
# FUNCTION
# =========================
def format_number(n):
    try: return f"{float(n):,.2f}"
    except: return ""

def thai_baht(num):
    try:
        num = float(num)
        baht, satang = int(num), int(round((num - int(num)) * 100))
        units = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
        pos = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]

        def read(n):
            s, n_str = "", str(n)[::-1]
            for i, d in enumerate(n_str):
                d = int(d)
                if d != 0:
                    if i == 1 and d == 1: s = "สิบ" + s
                    elif i == 1 and d == 2: s = "ยี่สิบ" + s
                    elif i == 0 and d == 1 and len(n_str) > 1: s = "เอ็ด" + s
                    else: s = units[d] + pos[i] + s
            return s

        result = read(baht) + "บาท"
        result += (read(satang) + "สตางค์") if satang else "ถ้วน"
        return result
    except:
        return ""

# =========================
# CSS (บีบ UI ให้แน่น)
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0.5rem !important;
}
div[data-testid="stVerticalBlock"] {
    gap: 0.3rem !important;
}
div[data-testid="stBorderedContainer"] {
    padding: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# UI
# =========================
st.title("ระบบใบเสนอราคา")

customer = st.text_input("ชื่อลูกค้า")
date_val = st.date_input("วันที่", datetime.now())
date_str = date_val.strftime("%d/%m/%Y")

rows = st.session_state.get("rows", [{}])

if st.button("➕ เพิ่มรายการ"):
    rows.append({})
    st.session_state["rows"] = rows

total_all = 0
data_rows = []

for i, row in enumerate(rows):
    st.markdown(f"### รายการ {i+1}")

    item = st.text_input("รายการ", key=f"item{i}")
    c1, c2, c3 = st.columns(3)

    qty = c1.text_input("จำนวน", key=f"qty{i}")
    unit = c2.selectbox("หน่วย", ["", "ชิ้น", "ชุด", "ตัว"], key=f"unit{i}")
    price = c3.text_input("ราคา", key=f"price{i}")

    try:
        total = float(qty) * float(price)
        total_all += total
        data_rows.append({"item": item, "qty": qty, "unit": unit, "price": price, "total": total})
        st.write(f"รวม: {format_number(total)}")
    except:
        pass

st.write("---")
st.subheader(f"รวมทั้งหมด: {format_number(total_all)}")
st.write(thai_baht(total_all))

# =========================
# PDF
# =========================
def create_pdf():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    if os.path.exists("template.jpg"):
        c.drawImage("template.jpg", 0, 0, 595, 842)

    # ใช้ Paragraph แก้สระลอย
    Paragraph(customer, style_thai).drawOn(c, X_NAME, Y_NAME)
    Paragraph(date_str, style_thai).drawOn(c, X_DATE, Y_DATE)

    y = START_Y

    for i, r in enumerate(data_rows):
        Paragraph(str(i+1), style_thai).drawOn(c, X_NO, y)
        Paragraph(r["item"], style_thai).wrapOn(c, ITEM_WIDTH, 100)
        Paragraph(r["item"], style_thai).drawOn(c, X_ITEM, y)

        if r["qty"]:
            Paragraph(str(r["qty"]), style_thai).drawOn(c, X_QTY, y)
        if r["unit"]:
            Paragraph(r["unit"], style_thai).drawOn(c, X_UNIT, y)
        if r["price"]:
            Paragraph(format_number(r["price"]), style_thai).drawOn(c, X_PRICE, y)
        if r["total"]:
            Paragraph(format_number(r["total"]), style_thai).drawOn(c, X_TOTAL, y)

        y -= 20

    Paragraph(format_number(total_all), style_thai).drawOn(c, X_SUM, Y_SUM)
    Paragraph(thai_baht(total_all), style_thai).drawOn(c, X_SUM_TEXT - 250, Y_SUM_TEXT)

    c.save()
    buf.seek(0)
    return buf

# =========================
# BUTTON
# =========================
if st.button("📄 สร้าง PDF"):
    pdf = create_pdf()
    st.download_button("ดาวน์โหลด PDF", pdf, file_name="quotation.pdf")
