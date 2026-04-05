import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from datetime import datetime
import os
import io
import random
import string
import re

# ==========================================
# CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="ระบบออกใบเสนอราคา",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ลงทะเบียนฟอนต์ภาษาไทย
FONT_MAIN = 'Helvetica'
if os.path.exists("Sarabun-Regular.ttf"):
    pdfmetrics.registerFont(TTFont('Sarabun', 'Sarabun-Regular.ttf'))
    FONT_MAIN = 'Sarabun'

BLUE_THEME_HEX = '#1D74E4'

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
ITEM_WIDTH = 300

# ==========================================
# HELPER FUNCTIONS
# ==========================================
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
        result = read(baht) + "บาท"
        result += (read(satang) + "สตางค์") if satang else "ถ้วน"
        return result
    except: return ""

def draw_thai_pdf(c, text, x, y, align='left'):
    """ฟังก์ชันวาดข้อความไทยพร้อมปรับระยะห่างเพื่อลดสระซ้อน"""
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(HexColor(BLUE_THEME_HEX))
    
    # เทคนิคปรับ CharSpace เล็กน้อยเพื่อลดการเบียดกันของสระ
    c.setCharSpace(0.3) 
    
    if align == 'center':
        c.drawCentredString(x, y, text)
    elif align == 'right':
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)
    
    # คืนค่าระยะห่างปกติ
    c.setCharSpace(0)

# ==========================================
# CSS CUSTOM (เน้นชิดหน้าจอสำหรับมือถือ)
# ==========================================
st.markdown(f"""
<style>
    /* ลด Padding ของหน้าจอหลักเพื่อให้เลื่อนน้อยลง */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}

    [data-testid="stSidebar"] {{display: none;}}
    .stButton>button {{width: 100%; border-radius: 8px; font-weight: bold;}}
    
    /* ซ่อนปุ่มเพิ่มลดในช่องตัวเลข */
    [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {{
        display: none !important;
    }}

    input[type=number] {{ -moz-appearance: textfield; }}
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button {{ -webkit-appearance: none; margin: 0; }}

    /* ปรับสีปุ่ม ลบ และ เพิ่ม */
    div:has(span#red-btn) + div button {{ background-color: #FF4B4B !important; color: white !important; }}
    div:has(span#green-btn) + div button {{ background-color: #28A745 !important; color: white !important; }}

    /* กรอบสีน้ำเงิน รายการที่... */
    .item-label {{
        background-color: #1E3A8A;
        color: white;
        padding: 5px 12px !important;
        border-radius: 6px;
        font-weight: bold;
        text-align: center;
        font-size: 15px !important;
        margin-bottom: 8px !important;
    }}

    /* ปรับหัวข้อให้เล็กลงและชิดกันมากขึ้น */
    .custom-header {{
        font-size: 18px !important;
        font-weight: bold !important;
        margin-top: 5px !important;
        margin-bottom: 5px !important;
        color: #FFFFFF;
    }}

    /* ลดระยะห่างระหว่างบล็อกข้อมูล */
    div[data-testid="stVerticalBlock"] {{
        gap: 0.3rem !important;
    }}

    div[data-testid="stBorderedContainer"] {{
        padding: 10px !important;
        margin-bottom: 5px !important;
    }}

    /* กรอบยอดรวมยาวเต็ม สูงเท่าช่องกรอก (42px) */
    .total-box-container {{
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        height: 42px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 10px !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# UI & LOGIC
# ==========================================
if "rows" not in st.session_state:
    st.session_state["rows"] = [0]
if "row_counter" not in st.session_state:
    st.session_state["row_counter"] = 1

def add_row():
    st.session_state["rows"].append(st.session_state["row_counter"])
    st.session_state["row_counter"] += 1

def remove_row(row_id):
    if len(st.session_state["rows"]) > 1:
        st.session_state["rows"].remove(row_id)

st.markdown('<p class="custom-header">📝 ออกใบเสนอราคา</p>', unsafe_allow_html=True)

with st.container(border=True):
    customer_select = st.selectbox(
        "ชื่อลูกค้า", 
        ["บริษัท รีไซเคิล เอ็นจิเนียริ่ง จำกัด", "บริษัท ซันเจียง เคมิคอล ไฟเบอร์ (ประเทศไทย) จำกัด", "UFM(THAILAND) CO.,LTD.", "สหกรณ์กองทุนสวนยางอำเภอบ่อทอง จำกัด", "ตัวเลือกอื่นๆ"],
        index=None, placeholder="เลือกหรือพิมพ์ชื่อลูกค้า..."
    )
    customer = st.text_input("ระบุชื่อลูกค้า", placeholder="พิมพ์ชื่อบริษัท...") if customer_select == "ตัวเลือกอื่นๆ" else (customer_select if customer_select else "")
    date_val = st.date_input("วันที่", value=datetime.now(), format="DD/MM/YYYY")

st.markdown('<p class="custom-header">📦 รายการสินค้า/บริการ</p>', unsafe_allow_html=True)
total_all = 0
data_rows = []

for i, row_id in enumerate(st.session_state["rows"]):
    with st.container(border=True):
        st.markdown(f'<div class="item-label">รายการที่ {i+1}</div>', unsafe_allow_html=True)
        item_name = st.text_input("ชื่อรายการ", key=f"n_{row_id}")
        c1, c2, c3 = st.columns([1, 1, 1.5])
        qty = c1.number_input("จำนวน", min_value=1, value=None, key=f"q_{row_id}")
        unit = c2.selectbox("หน่วย", ["ชุด", "ตัว", "ชิ้น", "อัน"], index=None, key=f"u_{row_id}")
        price = c3.number_input("ราคา/หน่วย", min_value=0.0, value=None, key=f"p_{row_id}")

        if qty and price:
            row_total = qty * price
            total_all += row_total
            data_rows.append({"item": item_name, "qty": qty, "unit": unit if unit else "", "price": price, "total": row_total})

        st.markdown('<span id="red-btn"></span>', unsafe_allow_html=True)
        st.button("ลบรายการ", key=f"del_{row_id}", on_click=remove_row, args=(row_id,))

st.markdown('<span id="green-btn"></span>', unsafe_allow_html=True)
st.button("➕ เพิ่มรายการใหม่", on_click=add_row)

note = st.text_input("หมายเหตุ", placeholder="ระบุเงื่อนไข...")

st.markdown(f"""
<div class="total-box-container">
    <h4 style='color: #1E3A8A; margin: 0;'>ยอดรวมทั้งสิ้น: <span style='color: #3380FF;'>{format_number(total_all)} บาท</span></h4>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PDF GENERATION
# ==========================================
def create_pdf():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    if os.path.exists("template.jpg"):
        c.drawImage("template.jpg", 0, 0, 595, 842)
    
    draw_thai_pdf(c, customer, X_NAME, Y_NAME)
    draw_thai_pdf(c, date_val.strftime("%d/%m/%Y"), X_DATE, Y_DATE)

    y = START_Y
    for i, r in enumerate(data_rows):
        draw_thai_pdf(c, str(i+1), X_NO, y, align='center')
        draw_thai_pdf(c, r['item'], X_ITEM, y)
        if r["qty"]: draw_thai_pdf(c, str(r["qty"]), X_QTY, y, align='center')
        if r["unit"]: draw_thai_pdf(c, r["unit"], X_UNIT, y, align='center')
        if r["price"]: draw_thai_pdf(c, format_number(r["price"]), X_PRICE, y, align='right')
        if r["total"]: draw_thai_pdf(c, format_number(r["total"]), X_TOTAL, y, align='right')
        y -= 20

    draw_thai_pdf(c, format_number(total_all), X_SUM, Y_SUM, align='right')
    draw_thai_pdf(c, thai_baht(total_all), X_SUM_TEXT - 250, Y_SUM_TEXT, align='right')
    if note: draw_thai_pdf(c, note, X_NOTE, Y_NOTE)
        
    c.save()
    buf.seek(0)
    return buf

# ==========================================
# DOWNLOAD
# ==========================================
if st.button("สร้าง PDF", type="primary"):
    pdf_buf = create_pdf()
    st.download_button(
        label="คลิกเพื่อโหลดไฟล์ PDF",
        data=pdf_buf.getvalue(),
        file_name=f"Quotation_{date_val.strftime('%d%m%y')}.pdf",
        mime="application/pdf"
    )
