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
import base64

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

# ==========================================
# PWA & CSS CUSTOM
# ==========================================
manifest_json = """
{
  "name": "ระบบออกใบเสนอราคา",
  "short_name": "QuoteApp",
  "start_url": ".",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3380FF",
  "icons": [{"src": "icon-512x512.png", "sizes": "512x512", "type": "image/png"}]
}
"""
manifest_b64 = base64.b64encode(manifest_json.encode()).decode()

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
    div:has(span#red-btn) + div button:hover {{
        background-color: white !important;
        color: #FF4B4B !important;
    }}

    div:has(span#green-btn) + div button {{
        background-color: #28A745 !important;
        color: white !important;
        border: 1px solid #28A745 !important;
    }}
    div:has(span#green-btn) + div button:hover {{
        background-color: white !important;
        color: #28A745 !important;
    }}

    .item-label {{
        background-color: #1E3A8A;
        color: white;
        padding: 10px;
        border-radius: 6px;
        font-weight: bold;
        text-align: center;
        font-size: 16px;
        margin-bottom: 10px;
        margin-top: 5px;
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

    hr {{
        margin-top: 10px !important;
        margin-bottom: 10px !important;
    }}

    @media (max-width: 768px) {{
        div[data-testid="stHorizontalBlock"] {{
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 8px !important;
        }}
        div[data-testid="stHorizontalBlock"] > div {{
            min-width: 0 !important;
        }}
        div[data-testid="stHorizontalBlock"] label p {{
            font-size: 12px !important;
        }}
    }}
</style>
<link rel="manifest" href="data:application/json;base64,{manifest_b64}">
""", unsafe_allow_html=True)

# ==========================================
# UI MAIN & DEFENSIVE STATE LOGIC
# ==========================================
if "rows" not in st.session_state:
    st.session_state["rows"] = [0]
if "row_counter" not in st.session_state:
    st.session_state["row_counter"] = 1

def add_row():
    curr_rows = st.session_state.get("rows", [0])
    curr_counter = st.session_state.get("row_counter", 1)
    
    curr_rows.append(curr_counter)
    st.session_state["rows"] = curr_rows
    st.session_state["row_counter"] = curr_counter + 1

def remove_row(row_id):
    curr_rows = st.session_state.get("rows", [0])
    if row_id in curr_rows:
        curr_rows.remove(row_id)
    st.session_state["rows"] = curr_rows

st.markdown('<p class="custom-header">ระบบออกใบเสนอราคา</p>', unsafe_allow_html=True)

with st.container(border=True):
    customer_select = st.selectbox("ชื่อลูกค้า", [
        "",
        "บริษัท รีไซเคิล เอ็นจิเนียริ่ง จำกัด",
        "บริษัท ซันเจียง เคมิคอล ไฟเบอร์ (ประเทศไทย) จำกัด",
        "UFM(THAILAND) CO.,LTD.",
        "สหกรณ์กองทุนสวนยางอำเภอบ่อทอง จำกัด",
        "ตัวเลือกอื่นๆ"
    ])
    
    if customer_select == "ตัวเลือกอื่นๆ":
        customer = st.text_input("ระบุชื่อลูกค้า", placeholder="พิมพ์ชื่อบริษัท/ชื่อลูกค้าที่นี่...")
    else:
        customer = customer_select

    date_val = st.date_input("วันที่", value=datetime.now(), format="DD/MM/YYYY")
    date_str = date_val.strftime("%d/%m/%Y")

st.write("---")
st.markdown('<p class="custom-header">รายละเอียดใบเสนอราคา</p>', unsafe_allow_html=True)
total_all = 0
data_rows = []

active_rows = st.session_state.get("rows", [0])

for i, row_id in enumerate(active_rows):
    with st.container(border=True):
        st.markdown(f'<div class="item-label">รายการที่ {i+1}</div>', unsafe_allow_html=True)
        item_name = st.text_input("ชื่อรายการ", key=f"name_{row_id}", placeholder="ระบุรายละเอียดงานหรือสินค้า...")
        
        c1, c2, c3 = st.columns([1, 1.2, 1.5])
        qty = c1.number_input("จำนวน", min_value=1, value=None, step=1, format="%d", key=f"qty_{row_id}")
        unit = c2.selectbox("หน่วย", ["", "ชุด", "ตัว", "ชิ้น", "อัน"], key=f"unit_{row_id}")
        price = c3.number_input("ราคาต่อหน่วย", min_value=0.0, value=None, format="%g", key=f"price_{row_id}")

        total_row = 0
        if qty is not None and price is not None:
            total_row = qty * price
            
        if total_row > 0:
            st.info(f"ยอดรวมรายการนี้: **{format_number(total_row)}** บาท")
            total_all += total_row
            
            data_rows.append({"item": item_name, "qty": qty, "unit": unit, "price": price, "total": total_row})

        st.markdown('<span id="red-btn"></span>', unsafe_allow_html=True)
        st.button("ลบรายการนี้", key=f"del_{row_id}", on_click=remove_row, args=(row_id,))

st.markdown('<span id="green-btn"></span>', unsafe_allow_html=True)
st.button("เพิ่มรายการใหม่", on_click=add_row)

st.write("---")

# ปรับจุดที่ 1: เปลี่ยนจาก text_area เป็น text_input เพื่อให้ช่องเล็กลงเหมือนชื่อรายการ
note = st.text_input("หมายเหตุ", placeholder="ระบุเงื่อนไขเพิ่มเติม (ถ้ามี)")

# ปรับจุดที่ 2: ใช้ HTML ตีกรอบแบบประหยัดพื้นที่ เพื่อให้ช่องยอดรวมขอบเล็กลง
st.markdown(f"""
<div style='border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 8px; margin-top: 10px; margin-bottom: 10px; text-align: center;'>
    <h4 style='color: #1E3A8A; margin: 0; display: inline-block;'>ยอดรวมทั้งสิ้น: <span style='color: #3380FF;'>{format_number(total_all)} บาท</span></h4>
    <div style='color: #aaa; font-size: 14px; margin-top: 2px;'>({thai_baht(total_all)})</div>
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
    
    c.setFont(FONT_MAIN, 10)
    c.setFillColorRGB(*BLUE_THEME)
    
    c.drawString(X_NAME, Y_NAME, customer)
    c.drawString(X_DATE, Y_DATE, date_str)

    style = getSampleStyleSheet()["Normal"]
    style.fontName, style.fontSize, style.textColor, style.leading = FONT_MAIN, 10, BLUE_THEME, 14

    y = START_Y
    for i, r in enumerate(data_rows):
        c.drawCentredString(X_NO, y, str(i+1))
        p = Paragraph(r["item"], style)
        w, h = p.wrap(ITEM_WIDTH, 100)
        p.drawOn(c, X_ITEM, y - h + 10)
        if r["qty"]: c.drawCentredString(X_QTY, y, str(r["qty"]))
        if r["unit"]: c.drawCentredString(X_UNIT, y, r["unit"])
        if r["price"]: c.drawRightString(X_PRICE, y, format_number(r["price"]))
        if r["total"]: c.drawRightString(X_TOTAL, y, format_number(r["total"]))
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

st.write("")
if st.button("สร้าง PDF", type="primary"):
    if not customer:
        st.error("กรุณาระบุชื่อลูกค้าก่อนสร้าง PDF ครับ")
    elif total_all == 0:
        st.error("กรุณากรอกข้อมูลรายการและราคาให้ครบถ้วนครับ")
    else:
        final_pdf = create_pdf()
        pdf_bytes = final_pdf.getvalue()
        
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        st.success("สร้างใบเสนอราคาสำเร็จ! คุณสามารถดูและสั่งพิมพ์/บันทึกจากหน้าต่างด้านล่างได้เลยครับ")
        
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" style="border: none; border-radius: 8px;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        st.download_button(
            label="ดาวน์โหลดไฟล์ PDF เก็บไว้",
            data=pdf_bytes,
            file_name=f"ใบเสนอราคา_{customer}.pdf",
            mime="application/pdf"
        )
