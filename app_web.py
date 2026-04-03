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
# PWA & CSS CUSTOM (ปรับปุ่มลบเป็นสีแดง)
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
    .stButton>button {{width: 100%; border-radius: 8px; font-weight: bold;}}
    
    /* สไตล์ปุ่มสีแดงสำหรับ "ลบรายการ" */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] .stButton>button {{
        background-color: #FF4B4B;
        color: white;
        border: none;
    }}
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] .stButton>button:hover {{
        background-color: #D32F2F;
        color: white;
    }}

    /* แถบรายการที่ 1 ชัดเจน */
    .item-label {{
        background-color: #1E3A8A;
        color: white;
        padding: 10px;
        border-radius: 8px 8px 0px 0px;
        font-weight: bold;
        text-align: center;
        font-size: 18px;
    }}
</style>
<link rel="manifest" href="data:application/json;base64,{manifest_b64}">
""", unsafe_allow_html=True)

# ==========================================
# UI MAIN
# ==========================================
st.title("ระบบออกใบเสนอราคา")

with st.container(border=True):
    customer = st.selectbox("ชื่อลูกค้า", [
        "",
        "บริษัท รีไซเคิล เอ็นจิเนียริ่ง จำกัด",
        "บริษัท ซันเจียง เคมิคอล ไฟเบอร์ (ประเทศไทย) จำกัด",
        "UFM(THAILAND) CO.,LTD.",
        "สหกรณ์กองทุนสวนยางอำเภอบ่อทอง จำกัด"
    ])
    # วันที่รูปแบบ 03/04/2026
    date_val = st.date_input("วันที่", value=datetime.now(), format="DD/MM/YYYY")
    date_str = date_val.strftime("%d/%m/%Y")

if "rows" not in st.session_state:
    st.session_state.rows = [0]  # เก็บเป็น ID ของแถว

if "row_counter" not in st.session_state:
    st.session_state.row_counter = 1

def add_row():
    st.session_state.rows.append(st.session_state.row_counter)
    st.session_state.row_counter += 1

def remove_row(row_id):
    st.session_state.rows.remove(row_id)

st.write("---")
total_all = 0
data_rows = []

# แสดงรายการสินค้า
for i, row_id in enumerate(st.session_state.rows):
    st.markdown(f'<div class="item-label">รายการที่ {i+1}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        item_name = st.text_input("ชื่อรายการ", key=f"name_{row_id}", placeholder="ระบุรายละเอียด...")
        
        c1, c2, c3 = st.columns([1, 1, 1.2])
        qty = c1.text_input("จำนวน", key=f"qty_{row_id}")
        unit = c2.selectbox("หน่วย", ["", "ชุด", "ชิ้น", "ตัว", "อัน"], key=f"unit_{row_id}")
        price = c3.text_input("ราคาต่อหน่วย", key=f"price_{row_id}")

        try:
            total_row = float(qty) * float(price) if qty and price else 0
        except:
            total_row = 0
            
        if total_row > 0:
            st.write(f"**รวมเงินรายการนี้: {format_number(total_row)} บาท**")
            total_all += total_row
            data_rows.append({"item": item_name, "qty": qty, "unit": unit, "price": price, "total": total_row})

        # ปุ่มลบสีแดง
        st.button("ลบรายการนี้", key=f"del_{row_id}", on_click=remove_row, args=(row_id,))
    st.write("")

# ปุ่มเพิ่มรายการสีปกติ
st.button("เพิ่มรายการใหม่", on_click=add_row)

st.write("---")
note = st.text_area("หมายเหตุ")

st.markdown(f"<h2 style='text-align: center; color: #3380FF;'>ยอดรวมทั้งสิ้น: {format_number(total_all)} บาท</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>({thai_baht(total_all)})</p>", unsafe_allow_html=True)

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

if st.button("สร้างและแชร์ PDF", type="primary"):
    if not customer:
        st.error("กรุณาเลือกชื่อลูกค้า")
    elif total_all == 0:
        st.error("กรุณากรอกข้อมูลรายการ")
    else:
        final_pdf = create_pdf()
        st.download_button(
            label="กดที่นี่เพื่อโหลด/ส่งไฟล์ PDF",
            data=final_pdf,
            file_name=f"ใบเสนอราคา_{customer}.pdf",
            mime="application/pdf"
        )
