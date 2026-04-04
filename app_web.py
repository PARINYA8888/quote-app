import streamlit as st
import json
import os
import io
import base64
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="ใบเสนอราคา", layout="centered")

if os.path.exists("Sarabun-Regular.ttf"):
    pdfmetrics.registerFont(TTFont("Sarabun", "Sarabun-Regular.ttf"))
    FONT = "Sarabun"
else:
    FONT = "Helvetica"

# ======================
# POSITION (ตรง 100%)
# ======================
X_NAME, Y_NAME = 82, 696.3
X_DATE, Y_DATE = 455, 696.3
X_NO, X_ITEM, X_QTY, X_UNIT, X_PRICE, X_TOTAL = 29, 60, 389, 432.2, 513.6, 580
START_Y = 600
X_SUM, Y_SUM = 580, 191
X_SUM_TEXT, Y_SUM_TEXT = 830, 170
X_NOTE, Y_NOTE = 85, 192
ITEM_WIDTH, NOTE_WIDTH = 300, 275

# ======================
# FUNCTIONS
# ======================
def format_number(n):
    try:
        return f"{float(n):,.2f}"
    except:
        return ""

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

        return read(baht) + "บาท" + (read(satang) + "สตางค์" if satang else "ถ้วน")
    except:
        return ""

# ======================
# HISTORY
# ======================
def load_history():
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(data):
    history = load_history()
    history.insert(0, data)
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history[:20], f, ensure_ascii=False, indent=2)

# ======================
# UI
# ======================
st.title("📄 ระบบใบเสนอราคา")

customer = st.text_input("ชื่อลูกค้า")
date_val = st.date_input("วันที่", value=datetime.now())
date_str = date_val.strftime("%d/%m/%Y")

# rows
if "rows" not in st.session_state:
    st.session_state.rows = [0]

def add_row():
    st.session_state.rows.append(len(st.session_state.rows))

def remove_row(i):
    st.session_state.rows.remove(i)

total_all = 0
data_rows = []

st.write("### รายการ")

for i in st.session_state.rows:
    with st.container(border=True):
        item = st.text_input("รายการ", key=f"item{i}")
        c1, c2, c3 = st.columns(3)

        qty = c1.text_input("จำนวน", key=f"qty{i}")
        unit = c2.selectbox("หน่วย", ["", "ชุด", "ชิ้น", "ตัว", "อัน"], key=f"unit{i}")
        price = c3.text_input("ราคา", key=f"price{i}")

        try:
            total = float(qty) * float(price) if qty and price else 0
        except:
            total = 0

        if total > 0:
            st.write(f"รวม: {format_number(total)} บาท")
            total_all += total
            data_rows.append({
                "item": item,
                "qty": qty,
                "unit": unit,
                "price": price,
                "total": total
            })

        st.button("❌ ลบ", key=f"del{i}", on_click=remove_row, args=(i,))

st.button("➕ เพิ่มรายการ", on_click=add_row)

note = st.text_area("หมายเหตุ")

st.markdown(f"## 💰 {format_number(total_all)} บาท")
st.markdown(f"({thai_baht(total_all)})")

# ======================
# PDF
# ======================
def create_pdf():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    if os.path.exists("template.jpg"):
        c.drawImage("template.jpg", 0, 0, 595, 842)

    c.setFont(FONT, 10)
    c.setFillColorRGB(0.2, 0.5, 1)

    c.drawString(X_NAME, Y_NAME, customer)
    c.drawString(X_DATE, Y_DATE, date_str)

    style = getSampleStyleSheet()["Normal"]
    style.fontName = FONT
    style.fontSize = 10

    y = START_Y
    for i, r in enumerate(data_rows):
        c.drawCentredString(X_NO, y, str(i+1))
        p = Paragraph(r["item"], style)
        w, h = p.wrap(ITEM_WIDTH, 100)
        p.drawOn(c, X_ITEM, y - h + 10)

        if r["qty"]:
            c.drawCentredString(X_QTY, y, r["qty"])
        if r["unit"]:
            c.drawCentredString(X_UNIT, y, r["unit"])
        if r["price"]:
            c.drawRightString(X_PRICE, y, format_number(r["price"]))
        if r["total"]:
            c.drawRightString(X_TOTAL, y, format_number(r["total"]))

        y -= max(h, 20)

    c.drawRightString(X_SUM, Y_SUM, format_number(total_all))
    c.drawRightString(X_SUM_TEXT - 250, Y_SUM_TEXT, thai_baht(total_all))

    if note:
        pn = Paragraph(note, style)
        wn, hn = pn.wrap(NOTE_WIDTH, 100)
        pn.drawOn(c, X_NOTE, Y_NOTE - hn + 10)

    c.save()
    buf.seek(0)
    return buf

# ======================
# GENERATE
# ======================
if st.button("📄 สร้าง PDF"):
    if not customer:
        st.warning("กรอกชื่อลูกค้า")
    else:
        pdf = create_pdf()

        # save history
        save_history({
            "customer": customer,
            "date": date_str,
            "total": format_number(total_all)
        })

        st.success("สร้างสำเร็จ")

        # preview
        b64 = base64.b64encode(pdf.read()).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>',
            unsafe_allow_html=True
        )

        pdf.seek(0)
        st.download_button("📥 ดาวน์โหลด PDF", pdf, file_name=f"ใบเสนอราคา_{customer}.pdf")

# ======================
# HISTORY SHOW
# ======================
st.write("---")
st.write("📜 ประวัติใบเสนอราคา")

for h in load_history():
    st.write(f"{h['date']} | {h['customer']} | {h['total']} บาท")
