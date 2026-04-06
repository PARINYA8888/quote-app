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
# ==========================
st.set_page_config(
    page_title="ระบบออกใบเสนอราคาโรงกลึงช่างมนญบ่อทอง",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ลงทะเบียนฟอนต์ภาษาไทย
FONT_MAIN = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if os.path.exists("Sarabun-Regular.ttf"):
    pdfmetrics.registerFont(TTFont('Sarabun', 'Sarabun-Regular.ttf'))
    FONT_MAIN = 'Sarabun'

if os.path.exists("Sarabun-Bold.ttf"):
    pdfmetrics.registerFont(TTFont('Sarabun-Bold', 'Sarabun-Bold.ttf'))
    FONT_BOLD = 'Sarabun-Bold'
else:
    FONT_BOLD = FONT_MAIN

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
ITEM_WIDTH, NOTE_WIDTH = 300, 275

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

def draw_thai_text(c, text, x, y, align='left', bold=False):
    c.setFont(FONT_BOLD if bold else FONT_MAIN, 10)
    c.setFillColor(HexColor(BLUE_THEME_HEX))
    
    if align == 'center':
        c.drawCentredString(x, y, text)
    elif align == 'right':
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)

# ==========================================
# CSS CUSTOM
# ==========================================
st.markdown(f"""
<style>
    [data-testid="stSidebar"] {{display: none;}}
    .stButton>button {{width: 100%; border-radius: 8px; font-weight: bold; transition: 0.3s;}}
    
    [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {{
        display: none !important;
    }}
    
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button {{ 
        -webkit-appearance: none; 
        margin: 0; 
    }}
    input[type=number] {{
        -moz-appearance: textfield;
    }}

    div:has(span#red-btn) + div button {{
        background-color: #FF4B4B !important;
        color: white !important;
        border: 1px solid #FF4B4B !important;
    }}

    div:has(span#green-btn) + div button {{
        background-color: #28A745 !important;
        color: white !important;
        border: 1px solid #28A745 !important;
    }}

    .item-label {{
        background-color: #1E3A8A;
        color: white;
        padding: 5px 12px !important;
        border-radius: 6px;
        font-weight: bold;
        text-align: center;
        font-size: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
    }}

    .custom-header {{
        font-size: 20px !important;
        font-weight: bold !important;
        margin-top: 20px !important;
        margin-bottom: 10px !important;
        color: #FFFFFF;
    }}

    .block-container {{
        padding-top: 3.5rem !important;
        padding-bottom: 1rem !important;
    }}

    div[data-testid="stVerticalBlock"] {{
        gap: 0.5rem !important;
    }}

    div[data-testid="stBorderedContainer"] {{
        padding: 12px !important;
        margin-bottom: 0px !important;
    }}

    .total-box-container {{
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        height: 55px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 15px 0px !important;
        background-color: rgba(29, 116, 228, 0.05);
    }}

    /* ล็อกให้คอลัมน์อยู่บรรทัดเดียวกันบนจอมือถือ พร้อมสั่งให้แบ่งพื้นที่กันไม่ให้ล้นจอ */
    @media screen and (max-width: 768px) {{
        div[data-testid="stHorizontalBlock"] {{
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.3rem !important; /* ลดช่องไฟลงนิดนึง */
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
            width: 100% !important; 
            flex: 1 1 0% !important; /* บังคับให้แบ่งความกว้างกันเท่าๆ กัน */
            min-width: 0 !important; /* ป้องกันไม่ให้กล่องขยายเกินพื้นที่ที่กำหนด */
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# UI MAIN & STATE LOGIC
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

st.markdown('<p class="custom-header">ระบบออกใบเสนอราคา</p>', unsafe_allow_html=True)

with st.container(border=True):
    customer_select = st.selectbox(
        "ชื่อลูกค้า", 
        [
            "บริษัท รีไซเคิล เอ็นจิเนียริ่ง จำกัด",
            "บริษัท ซันเจียง เคมิคอล ไฟเบอร์ (ประเทศไทย) จำกัด",
            "UFM(THAILAND) CO.,LTD.",
            "สหกรณ์กองทุนสวนยางอำเภอบ่อทอง จำกัด",
            "ECHO TOOLS CORPORATION(THAILAND) CO., LTD.",
            "DSG Advanced Material (Thailand) Co., Ltd.",
            "ตัวเลือกอื่นๆ"
        ],
        index=None,
        placeholder="เลือกชื่อลูกค้าหรือพิมพ์ใหม่..."
    )
    
    if customer_select == "ตัวเลือกอื่นๆ":
        customer = st.text_input("ระบุชื่อลูกค้า", placeholder="พิมพ์ชื่อบริษัท/ชื่อลูกค้าที่นี่...")
    else:
        customer = customer_select if customer_select else ""

    date_val = st.date_input("วันที่", value=datetime.now(), format="DD/MM/YYYY")
    date_str = date_val.strftime("%d/%m/%Y")

st.write("---")
st.markdown('<p class="custom-header">รายละเอียดใบเสนอราคา</p>', unsafe_allow_html=True)
total_all = 0
data_rows = []

for i, row_id in enumerate(st.session_state["rows"]):
    with st.container(border=True):
        st.markdown(f'<div class="item-label">รายการที่ {i+1}</div>', unsafe_allow_html=True)
        item_name = st.text_input("ชื่อรายการ", key=f"name_{row_id}", placeholder="ระบุรายละเอียดงานหรือสินค้า...")
        
        c1, c2, c3 = st.columns([1, 1.2, 1.5])
        qty = c1.number_input("จำนวน", min_value=1, value=None, step=1, format="%d", key=f"qty_{row_id}")
        unit = c2.selectbox("หน่วย", ["ชุด", "ตัว", "ชิ้น", "อัน"], index=None, placeholder="เลือกหน่วย", key=f"unit_{row_id}")
        price = c3.number_input("ราคาต่อหน่วย", min_value=0.0, value=None, format="%g", key=f"price_{row_id}")

        if qty is not None and price is not None:
            total_row = qty * price
            total_all += total_row
            data_rows.append({"item": item_name, "qty": qty, "unit": unit if unit else "", "price": price, "total": total_row})

        st.markdown('<span id="red-btn"></span>', unsafe_allow_html=True)
        st.button("ลบรายการนี้", key=f"del_{row_id}", on_click=remove_row, args=(row_id,))

st.markdown('<span id="green-btn"></span>', unsafe_allow_html=True)
st.button("เพิ่มรายการใหม่", on_click=add_row)

st.write("---")
note = st.text_input("หมายเหตุ", placeholder="ระบุเงื่อนไขเพิ่มเติม (ถ้ามี)")

st.markdown(f"""
<div class="total-box-container">
    <h3 style='color: #1E3A8A; margin: 0; font-size: 22px;'>ยอดรวมทั้งสิ้น: <span style='color: #3380FF;'>{format_number(total_all)} บาท</span></h3>
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
    
    draw_thai_text(c, customer, X_NAME, Y_NAME, bold=False)
    draw_thai_text(c, date_str, X_DATE, Y_DATE, bold=False)

    y = START_Y
    for i, r in enumerate(data_rows):
        draw_thai_text(c, str(i+1), X_NO, y, align='center', bold=False)
        draw_thai_text(c, r['item'], X_ITEM, y, bold=False)
        if r["qty"]: draw_thai_text(c, str(r["qty"]), X_QTY, y, align='center', bold=False)
        if r["unit"]: draw_thai_text(c, r["unit"], X_UNIT, y, align='center', bold=False)
        if r["price"]: draw_thai_text(c, format_number(r["price"]), X_PRICE, y, align='right', bold=False)
        if r["total"]: draw_thai_text(c, format_number(r["total"]), X_TOTAL, y, align='right', bold=False)
        y -= 20

    draw_thai_text(c, format_number(total_all), X_SUM, Y_SUM, align='right', bold=False)
    draw_thai_text(c, thai_baht(total_all), X_SUM_TEXT - 250, Y_SUM_TEXT, align='right', bold=False)
    if note:
        draw_thai_text(c, note, X_NOTE, Y_NOTE, bold=False)
        
    c.save()
    buf.seek(0)
    return buf

# ==========================================
# DOWNLOAD & TRIGGER ACTION
# ==========================================
st.write("")
if st.button("สร้าง PDF", type="primary"):
    final_pdf = create_pdf()
    pdf_bytes = final_pdf.getvalue()
    
    clean_customer = re.sub(r'[\\/*?:"<>|]', '', customer) if customer else "ทั่วไป"
    date_file = date_val.strftime("%d-%m-%Y")
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    
    file_name = f"ใบเสนอราคา_{clean_customer}_{date_file}_{random_str}.pdf"
    
    st.download_button(
        label="ดาวน์โหลดไฟล์ PDF",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf"
    )
