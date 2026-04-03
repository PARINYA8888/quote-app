import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import tempfile, base64, os

st.set_page_config(page_title="ใบเสนอราคา", layout="centered")

pdfmetrics.registerFont(TTFont('Sarabun', 'Sarabun-Regular.ttf'))

# ======================
# ตำแหน่ง (FIX ตรง 100%)
# ======================
X_NAME, Y_NAME = 82, 696.3
X_DATE, Y_DATE = 455, 696.3
X_NO, X_ITEM, X_QTY, X_UNIT, X_PRICE, X_TOTAL = 29, 60, 389, 432.2, 513.6, 580
START_Y = 600
X_SUM, Y_SUM = 580, 191
X_SUM_TEXT, Y_SUM_TEXT = 830, 170   # 🔥 ใช้ค่าเดิม
X_NOTE, Y_NOTE = 85, 192
ITEM_WIDTH, NOTE_WIDTH = 300, 275

BLUE = (0.2, 0.5, 1)

# ======================
# ฟังก์ชัน
# ======================
def format_number(n):
    try: return f"{float(n):,.2f}"
    except: return ""

def thai_baht(num):
    try:
        num = float(num)
        baht = int(num)
        satang = int(round((num - baht) * 100))

        units = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
        pos = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]

        def read(n):
            s = ""
            n = str(n)[::-1]
            for i, d in enumerate(n):
                d = int(d)
                if d != 0:
                    if i == 1 and d == 1: s = "สิบ" + s
                    elif i == 1 and d == 2: s = "ยี่สิบ" + s
                    elif i == 0 and d == 1 and len(n) > 1: s = "เอ็ด" + s
                    else: s = units[d] + pos[i] + s
            return s

        result = read(baht) + "บาท"
        result += read(satang) + "สตางค์" if satang else "ถ้วน"
        return result
    except: return ""

# ======================
# UI มือถือ
# ======================
st.markdown("## 📄 ใบเสนอราคา")

customer = st.selectbox("ลูกค้า", [
    "",
    "บริษัท รีไซเคิล เอ็นจิเนียริ่ง จำกัด",
    "บริษัท ซันเจียง เคมิคอล ไฟเบอร์ (ประเทศไทย) จำกัด",
    "UFM(THAILAND) CO.,LTD.",
    "สหกรณ์กองทุนสวนยางอำเภอบ่อทอง จำกัด"
])

date = st.text_input("วันที่", value=datetime.now().strftime("%d/%m/%Y"))

# ======================
# ROWS
# ======================
if "rows" not in st.session_state:
    st.session_state.rows = [{}]

def add_row():
    st.session_state.rows.append({})

def remove_row(i):
    st.session_state.rows.pop(i)

st.markdown("### 🧾 รายการ")

total_sum = 0
data_rows = []

for i, row in enumerate(st.session_state.rows):
    st.markdown(f"#### รายการที่ {i+1}")

    item = st.text_input("ชื่อรายการ", key=f"item{i}")

    col1, col2, col3 = st.columns(3)
    qty = col1.text_input("จำนวน", key=f"qty{i}")
    unit = col2.selectbox("หน่วย", ["", "ชุด", "ชิ้น", "ตัว", "อัน"], key=f"unit{i}")
    price = col3.text_input("ราคา", key=f"price{i}")

    # ✅ แสดง unit ทันที
    if unit:
        st.caption(f"หน่วย: {unit}")

    try:
        q = float(qty) if qty else 0
        p = float(price) if price else 0
        total = q * p
    except:
        total = 0

    st.write("💰 รวม:", format_number(total))

    if total:
        total_sum += total
        data_rows.append({
            "item": item,
            "qty": qty,
            "unit": unit,
            "price": price,
            "total": total
        })

    if st.button("❌ ลบรายการ", key=f"del{i}"):
        remove_row(i)
        st.rerun()

st.button("➕ เพิ่มรายการ", on_click=add_row)

# ======================
# สรุป
# ======================
st.markdown("---")

st.write("### 💵 รวมเงิน")
st.write(format_number(total_sum))
st.write("### 🔤 ตัวอักษร")
st.write(thai_baht(total_sum))

note = st.text_area("หมายเหตุ")

# ======================
# PDF
# ======================
def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)

    if os.path.exists("template.jpg"):
        c.drawImage("template.jpg", 0, 0, 595, 842)

    c.setFont("Sarabun", 10)
    c.setFillColorRGB(*BLUE)

    c.drawString(X_NAME, Y_NAME, customer)
    c.drawString(X_DATE, Y_DATE, date)

    style = getSampleStyleSheet()["Normal"]
    style.fontName = "Sarabun"
    style.fontSize = 10
    style.textColor = BLUE
    style.leading = 14

    y = START_Y

    for i, r in enumerate(data_rows):
        p = Paragraph(r["item"], style)
        w, h = p.wrap(ITEM_WIDTH, 100)

        p.drawOn(c, X_ITEM, y - h + 10)
        c.drawCentredString(X_NO, y, str(i+1))

        if r["qty"]:
            c.drawCentredString(X_QTY, y, r["qty"])
        if r["unit"]:
            c.drawCentredString(X_UNIT, y, r["unit"])
        if r["price"]:
            c.drawRightString(X_PRICE, y, format_number(r["price"]))
        if r["total"]:
            c.drawRightString(X_TOTAL, y, format_number(r["total"]))

        y -= max(h, 20)

    c.drawRightString(X_SUM, Y_SUM, format_number(total_sum))

    # 🔥 FIX ตรงเป๊ะ
    c.drawRightString(X_SUM_TEXT - 250, Y_SUM_TEXT, thai_baht(total_sum))

    if note:
        p = Paragraph(note, style)
        w, h = p.wrap(NOTE_WIDTH, 100)
        p.drawOn(c, X_NOTE, Y_NOTE - h + 10)

    c.save()
    return tmp.name

# ======================
# Preview PDF
# ======================
if st.button("📄 สร้างใบเสนอราคา"):
    pdf_file = generate_pdf()

    with open(pdf_file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <iframe src="data:application/pdf;base64,{base64_pdf}"
    width="100%" height="900px"></iframe>
    """, unsafe_allow_html=True)
