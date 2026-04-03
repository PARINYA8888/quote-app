import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os
import io

# ==========================================
# CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="ระบบออกใบเสนอราคา",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ลงทะเบียนฟอนต์ภาษาไทย
if os.path.exists("Sarabun-Regular.ttf"):
    pdfmetrics.registerFont(TTFont('Sarabun', 'Sarabun-Regular.ttf'))
    FONT_MAIN = 'Sarabun'
else:
    FONT_MAIN = 'Helvetica'

# โทนสีหลัก (สีฟ้า)
BLUE_THEME = (0.2, 0.5, 1)

# ==========================================
# PDF POSITIONS
# ==========================================
X_NAME, Y_NAME = 82, 696.3
X_DATE, Y_DATE = 455, 696.3
X_NO, X_ITEM, X_QTY, X_UNIT, X_PRICE, X_TOTAL = 29, 60, 389, 432.2, 513.6, 580
START_Y = 600
X_SUM, Y_SUM = 580, 191
X_SUM_TEXT = 830
Y_SUM_TEXT = 170
X_NOTE, Y_NOTE = 85, 192
ITEM_WIDTH, NOTE_WIDTH = 300, 275

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def format_number(n):
    try:
        return f"{float(n):,.2f}"
    except (ValueError, TypeError):
        return ""

def thai_baht(num):
    try:
        num = float(num)
        baht = int(num)
        satang = int(round((num - baht) * 100))

        units = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
        pos = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]

        def read(n):
            s = ""
            n_str = str(n)[::-1]
            for i, d in enumerate(n_str):
                d = int(d)
                if d != 0:
                    if i == 1 and d == 1: s = "สิบ" + s
                    elif i == 1 and d == 2: s = "ยี่สิบ" + s
                    elif i == 0 and d == 1 and len(n_str) > 1: s = "เอ็ด" + s
                    else: s = units[d] + pos[i] + s
            return s

        result = read(baht) + "บาท"
        if satang == 0:
            result += "ถ้วน"
        else:
            result += read(satang) + "สตางค์"
        return result
    except:
        return ""

# ==========================================
# PWA CONFIG & CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    /* ซ่อน Sidebar และปรับขอบ */
    [data-testid="stSidebar"] {display: none;}
    .main .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    
    /* ปรับแต่งปุ่มให้ดูทันสมัย */
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold;}
    
    /* ปรับแต่งกล่องรายการ */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
        border-radius: 8px;
    }
    
    /* สไตล์แถบหัวข้อรายการให้ดูเด่นชัด */
    .item-header {
        background-color: #3380FF;
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 12px;
        text-align: center;
    }
    
    .total-text {
        color: #3380FF;
        font-size: 16px;
        font-weight: bold;
        margin-top: 8px;
    }
</style>

<link rel="manifest" href="data:application/json;base64,ewogICJuYW1lIjogItC50LHQsdC50LHQstC90LHQstC40LHQpSIsCiAgInNob3J0X25hbWUiOiAiUXVvdGUiLAogICJzdGFydF91cmwiOiAiLi8iLAogICJkaXNwbGF5IjogInN0YW5kYWxvbmUiLAogICJiYWNrZ3JvdW5kX2NvbG9yIjogIiNmZmZmZmYiLAogICJ0aGVtZV9jb2xvciI6ICIjMzMzMzMzIiwogICJpY29ucyI6IFsKICAgIHsKICAgICAgInNyYyI6ICJodHRwczovL2ltZzIuc3RyZWFtbGl0LmlvL2ljb24ucG5nIiwgCiAgICAgICJzaXplcyI6ICI1MTJ4NTEyIiwKICAgICAgInR5cGUiOiAiaW1hZ2UvcG5nIg    ogICAgfQogIF0KfQ==">
""", unsafe_allow_html=True)

# ==========================================
# UI MAIN
# ==========================================
st.markdown("### ระบบออกใบเสนอราคา")

col_h1, col_h2 = st.columns(2)
with col_h1:
    customer = st.selectbox("เลือกชื่อลูกค้า", [
        "",
        "บริษัท รีไซเคิล เอ็นจิเนียริ่ง จำกัด",
        "บริษัท ซันเจียง เคมิคอล ไฟเบอร์ (ประเทศไทย) จำกัด",
        "UFM(THAILAND) CO.,LTD.",
        "สหกรณ์กองทุนสวนยางอำเภอบ่อทอง จำกัด"
    ])
    
    # ปรับรูปแบบวันที่เป็น DD/MM/YYYY ใน UI
    date = st.date_input("วันที่", value=datetime.now(), format="DD/MM/YYYY")
    date_str = date.strftime("%d/%m/%Y")

# ==========================================
# ITEM MANAGEMENT
# ==========================================
if "rows" not in st.session_state:
    st.session_state.rows = [{}]

def add_row():
    st.session_state.rows.append({})

def remove_row(index):
    st.session_state.rows.pop(index)

st.markdown("---")
st.markdown("#### รายการสินค้าและบริการ")

total_sum = 0
data_rows = []

for i, row in enumerate(st.session_state.rows):
    with st.container(border=True):
        # แถบหัวข้อรายการที่เด่นชัดขึ้น
        st.markdown(f"<div class='item-header'>รายการที่ {i+1}</div>", unsafe_allow_html=True)
        
        item = st.text_input("ชื่อรายการ", key=f"item{i}", placeholder="พิมพ์ชื่อรายการ...")
        
        c1, c2, c3 = st.columns([1, 1, 1.2])
        qty = c1.text_input("จำนวน", key=f"qty{i}")
        unit = c2.selectbox("หน่วย", ["", "ชุด", "ชิ้น", "ตัว", "อัน"], key=f"unit{i}", index=0)
        price = c3.text_input("ราคาต่อหน่วย", key=f"price{i}")

        try:
            q = float(qty) if qty else 0
            p = float(price) if price else 0
            total = q * p
        except ValueError:
            total = 0

        if total > 0:
            st.markdown(f"<div class='total-text'>รวมเงินรายการนี้: {format_number(total)} บาท</div>", unsafe_allow_html=True)
            total_sum += total
            
            data_rows.append({
                "item": item,
                "qty": qty,
                "unit": unit,
                "price": price,
                "total": total
            })
            
        # ปุ่มลบรายการ (เว้นระยะห่างด้านบนเล็กน้อยให้กดง่าย)
        st.write("")
        if st.button("ลบรายการนี้", key=f"del{i}"):
            remove_row(i)
            st.rerun()

st.write("")
st.button("เพิ่มแถวรายการใหม่", on_click=add_row, type="secondary")

# ==========================================
# SUMMARY
# ==========================================
st.markdown("---")
st.markdown("#### สรุปยอดเงิน")

note = st.text_area("หมายเหตุ (เช่น รวมค่าวัสดุ, เครดิต 30 วัน)", placeholder="ระบุเงื่อนไขเพิ่มเติม (ถ้ามี)...")

st.divider()
st.markdown(f"<h3 style='text-align: center; color: #3380FF;'>รวมเป็นเงินทั้งสิ้น: {format_number(total_sum)} บาท</h3>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; font-size: 16px;'>({thai_baht(total_sum)})</p>", unsafe_allow_html=True)
st.divider()

# ==========================================
# PDF GENERATION
# ==========================================
def generate_pdf_buffer():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    if os.path.exists("template.jpg"):
        c.drawImage("template.jpg", 0, 0, 595, 842)

    if FONT_MAIN != 'Helvetica':
        c.setFont(FONT_MAIN, 10)
    else:
        c.setFont("Helvetica", 10)
        
    c.setFillColorRGB(*BLUE_THEME)

    c.drawString(X_NAME, Y_NAME, customer)
    c.drawString(X_DATE, Y_DATE, date_str)

    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = FONT_MAIN
    style.fontSize = 10
    style.textColor = BLUE_THEME
    style.leading = 14

    y = START_Y

    for i, r in enumerate(data_rows):
        if not r["item"]: continue
        
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

    c.drawRightString(X_SUM, Y_SUM, format_number(total_sum))
    c.drawRightString(X_SUM_TEXT - 250, Y_SUM_TEXT, thai_baht(total_sum))

    if note:
        p_note = Paragraph(note, style)
        wn, hn = p_note.wrap(NOTE_WIDTH, 100)
        p_note.drawOn(c, X_NOTE, Y_NOTE - hn + 10)

    c.save()
    buffer.seek(0)
    return buffer

if st.button("สร้างไฟล์ PDF", type="primary"):
    if not customer:
        st.error("กรุณาเลือกชื่อลูกค้าก่อนสร้างเอกสาร")
    elif total_sum == 0:
        st.error("กรุณากรอกรายการสินค้าอย่างน้อย 1 รายการ")
    else:
        with st.spinner('กำลังประมวลผล...'):
            pdf_data = generate_pdf_buffer()
            
            st.success("สร้างเอกสารสำเร็จ กรุณากดปุ่มด้านล่างเพื่อแชร์ไฟล์")
            st.download_button(
                label="กดที่นี่เพื่อแชร์ไฟล์ PDF",
                data=pdf_data,
                file_name=f"Quotation_{customer}_{date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
