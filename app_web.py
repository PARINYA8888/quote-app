import streamlit as st
from datetime import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import base64

st.set_page_config(page_title="ใบเสนอราคา", layout="wide")

BASE_DIR = os.path.dirname(__file__)
pdfmetrics.registerFont(TTFont('Sarabun', os.path.join(BASE_DIR, 'Sarabun-Regular.ttf')))

# ===== ตำแหน่ง =====
X_NAME, Y_NAME = 82, 696.3
X_DATE, Y_DATE = 455, 696.3
X_NO, X_ITEM, X_QTY, X_UNIT, X_PRICE, X_TOTAL = 29, 60, 389, 432.2, 513.6, 580
START_Y = 600
X_SUM, Y_SUM = 580, 191
X_SUM_TEXT, Y_SUM_TEXT = 830, 170
X_NOTE, Y_NOTE = 85, 192
ITEM_WIDTH, NOTE_WIDTH = 300, 275

customer_list = [
    "บริษัท รีไซเคิล เอ็นจิเนียริ่ง จำกัด",
    "บริษัท ซันเจียง เคมิคอล ไฟเบอร์ (ประเทศไทย) จำกัด",
    "UFM(THAILAND) CO.,LTD.",
    "สหกรณ์กองทุนสวนยางอำเภอบ่อทอง จำกัด"
]

unit_list = ["ชุด", "ชิ้น", "ตัว", "อัน"]

def format_number(n): return f"{n:,.2f}"

def thai_baht(num):
    num = float(num)
    baht = int(num)
    satang = int(round((num - baht) * 100))
    units = ["", "หนึ่ง","สอง","สาม","สี่","ห้า","หก","เจ็ด","แปด","เก้า"]
    pos = ["","สิบ","ร้อย","พัน","หมื่น","แสน","ล้าน"]

    def read(n):
        s=""; n=str(n)[::-1]
        for i,d in enumerate(n):
            d=int(d)
            if d!=0:
                if i==1 and d==1: s="สิบ"+s
                elif i==1 and d==2: s="ยี่สิบ"+s
                elif i==0 and d==1 and len(n)>1: s="เอ็ด"+s
                else: s=units[d]+pos[i]+s
        return s

    txt = read(baht)+"บาท"
    return txt+"ถ้วน" if satang==0 else txt+read(satang)+"สตางค์"

# ===== session =====
if "rows" not in st.session_state:
    st.session_state.rows = [{}]

if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

st.title("📄 ใบเสนอราคา")

name = st.selectbox("ลูกค้า", [""]+customer_list)
custom = st.text_input("หรือพิมพ์เอง")
if custom: name = custom

date = st.text_input("วันที่", value=datetime.now().strftime("%d/%m/%Y"))

total_all = 0

# ===== rows =====
for i in range(len(st.session_state.rows)):
    cols = st.columns([1,4,1,1,2,2,1])

    cols[0].write(i+1)
    item = cols[1].text_input("รายการ", key=f"item{i}")

    # ✅ ไม่มีค่าเริ่มต้น
    qty = cols[2].number_input(
        "จำนวน",
        key=f"qty{i}",
        value=None,
        placeholder="กรอก",
        format="%.0f"
    ) or 0

    unit = cols[3].selectbox("หน่วย", unit_list, key=f"unit{i}")

    price = cols[4].number_input(
        "ราคา",
        key=f"price{i}",
        value=None,
        placeholder="กรอก",
        format="%.2f"
    ) or 0

    total = qty * price
    total_all += total

    cols[5].write(format_number(total))

    if cols[6].button("❌", key=f"del{i}"):
        st.session_state.rows.pop(i)
        st.rerun()

if st.button("➕ เพิ่มรายการ"):
    st.session_state.rows.append({})
    st.rerun()

st.markdown("---")
st.write("💰 รวม:", format_number(total_all))
st.write("🧾", thai_baht(total_all))

note = st.text_input("หมายเหตุ")

# ===== CREATE PDF =====
if st.button("📄 สร้าง PDF"):

    filename = f"ใบเสนอราคา_{name}_{date.replace('/','-')}.pdf"
    path = os.path.join(BASE_DIR, filename)

    c = canvas.Canvas(path, pagesize=A4)

    template = os.path.join(BASE_DIR, "template.jpg")
    if os.path.exists(template):
        c.drawImage(template, 0, 0, 595, 842)

    c.setFont("Sarabun", 10)
    c.setFillColorRGB(0.2,0.5,1)

    c.drawString(X_NAME, Y_NAME, name)
    c.drawString(X_DATE, Y_DATE, date)

    style = getSampleStyleSheet()["Normal"]
    style.fontName = "Sarabun"
    style.fontSize = 10
    style.textColor = colors.Color(0.2,0.5,1)

    y = START_Y

    for i in range(len(st.session_state.rows)):
        item = st.session_state.get(f"item{i}", "")
        if not item: continue

        qty = st.session_state.get(f"qty{i}", 0) or 0
        unit = st.session_state.get(f"unit{i}", "")
        price = st.session_state.get(f"price{i}", 0) or 0
        total = qty * price

        p = Paragraph(item, style)
        w,h = p.wrap(ITEM_WIDTH,100)
        p.drawOn(c, X_ITEM, y-h+10)

        c.drawCentredString(X_NO, y, str(i+1))
        if qty: c.drawCentredString(X_QTY, y, str(int(qty)))
        if unit: c.drawCentredString(X_UNIT, y, unit)
        if price: c.drawRightString(X_PRICE, y, format_number(price))
        if total: c.drawRightString(X_TOTAL, y, format_number(total))

        y -= max(h,20)

    c.drawRightString(X_SUM, Y_SUM, format_number(total_all))
    c.drawRightString(X_SUM_TEXT-250, Y_SUM_TEXT, thai_baht(total_all))
    c.drawString(X_NOTE, Y_NOTE, note)

    c.save()

    # ===== โหลด PDF เข้า memory =====
    with open(path, "rb") as f:
        st.session_state.pdf_data = f.read()

# ===== SHOW PDF ทันที =====
if st.session_state.pdf_data:
    b64 = base64.b64encode(st.session_state.pdf_data).decode()

    st.subheader("📄 Preview")
    st.markdown(f"""
        <iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <a href="data:application/pdf;base64,{b64}" target="_blank">
        👉 เปิดเต็มหน้าจอ
    </a>
    """, unsafe_allow_html=True)
