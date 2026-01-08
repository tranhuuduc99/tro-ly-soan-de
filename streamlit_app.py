import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO
import PyPDF2

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Ra Đề", page_icon="🏫", layout="wide")

# --- 3 KEY CỦA BẠN (Đã tích hợp) ---
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# --- HÀM GỌI AI TRỰC TIẾP (KHÔNG CẦN THƯ VIỆN GOOGLE) ---
def call_gemini_smart(prompt):
    # Dùng model Flash cho nhanh
    url_base = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    # Cấu hình để AI không từ chối trả lời (Chống kiểm duyệt gắt)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    headers = {'Content-Type': 'application/json'}

    # Vòng lặp thử Key
    for key in API_KEYS:
        try:
            full_url = f"{url_base}?key={key}"
            response = requests.post(full_url, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429: # Quá tải
                continue 
            else: # Lỗi khác
                print(f"Key lỗi: {response.text}")
                continue
        except Exception:
            continue
            
    return "⚠️ LỖI MẠNG: Đã thử tất cả các kênh nhưng không kết nối được. Vui lòng kiểm tra Wifi."

# --- HÀM XỬ LÝ FILE ---
def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            return "".join([page.extract_text() or "" for page in reader.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        return ""
    except: return "Lỗi đọc file."

def create_word(content, topic):
    doc = Document()
    doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    doc.add_paragraph(f'ĐỀ KIỂM TRA: {topic.upper()}')
    doc.add_paragraph("Họ tên: ................................................. Lớp: ............")
    doc.add_paragraph("-" * 60)
    doc.add_paragraph(content)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #004d99;'>🏫 HỆ THỐNG HỖ TRỢ RA ĐỀ THI</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: grey;'>© Bản quyền thuộc về trường PTDTBT THCS Mùn Chung</div>", unsafe_allow_html=True)
st.markdown("---")

# Menu Mobile
if st.session_state.get('check_mobile', True):
    st.info("💡 Lưu ý: Trên điện thoại, bấm mũi tên `>` góc trái trên để mở menu.")
    st.session_state['check_mobile'] = False

with st.sidebar:
    st.header("Cấu hình")
    st.success("Trạng thái: Đã kết nối (Direct Mode)")

# Tabs
tab1, tab2, tab3 = st.tabs(["⚡ Soạn Nhanh", "📂 Từ File", "📥 Tải Về"])

# Tab 1: Soạn Nhanh
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        topic = st.text_input("Chủ đề:", "Lịch sử Điện Biên Phủ")
        grade = st.selectbox("Khối lớp:", ["6", "7", "8", "9"])
    with c2:
        num = st.slider("Số câu:", 5, 30, 10)
        hard = st.select_slider("Độ khó:", ["Nhận biết", "Thông hiểu", "Vận dụng"])
    
    if st.button("🚀 SOẠN ĐỀ NGAY", use_container_width=True):
        prompt = f"Đóng vai giáo viên lớp {grade}. Soạn {num} câu trắc nghiệm về '{topic}'. Độ khó: {hard}. Có đáp án chi tiết cuối bài."
        with st.spinner("Hệ thống đang soạn thảo..."):
            res = call_gemini_smart(prompt)
            st.session_state['res'] = res
            st.session_state['top'] = topic
            if "⚠️" in res: st.error(res)
            else: st.success("Xong! Qua tab Tải Về để lấy file."); st.write(res)

# Tab 2: Từ File
with tab2:
    f = st.file_uploader("Tải tài liệu (PDF/Word):", type=['pdf','docx'])
    if st.button("🚀 PHÂN TÍCH & SOẠN", use_container_width=True):
        if f:
            with st.spinner("Đang đọc và phân tích..."):
                content = read_file(f)
                if len(content) < 20: st.warning("File không có nội dung chữ.")
                else:
                    prompt = f"Dựa vào văn bản: {content[:15000]}. Soạn 10 câu trắc nghiệm có đáp án."
                    res = call_gemini_smart(prompt)
                    st.session_state['res'] = res
                    st.session_state['top'] = f.name
                    if "⚠️" in res: st.error(res)
                    else: st.success("Xong! Qua tab Tải Về để lấy file."); st.write(res)

# Tab 3: Tải Về
with tab3:
    if 'res' in st.session_state:
        txt = st.text_area("", st.session_state['res'], height=300)
        docx = create_word(txt, st.session_state['top'])
        st.download_button("📥 TẢI FILE WORD", docx, f"{st.session_state['top']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else: st.info("Chưa có dữ liệu.")
