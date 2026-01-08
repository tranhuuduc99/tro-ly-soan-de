import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import PyPDF2
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Trợ Lý Soạn Đề",
    page_icon="🏫",
    layout="wide"
)

# --- DANH SÁCH KEY (Đã kiểm tra hoạt động) ---
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# --- HÀM XỬ LÝ (GIỮ NGUYÊN) ---
def read_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except: return "Không đọc được file PDF này."

def read_docx(file):
    try:
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    except: return "Không đọc được file Word này."

def create_docx(content, topic):
    doc = Document()
    doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    doc.add_paragraph(f'ĐỀ KIỂM TRA CHỦ ĐỀ: {topic.upper()}')
    doc.add_paragraph("Họ tên: ................................................. Lớp: ............")
    doc.add_paragraph("-" * 60)
    doc.add_paragraph(content)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- HÀM GỌI AI THÔNG MINH (MULTI-MODEL) ---
def get_gemini_response_smart(prompt):
    # Danh sách model ưu tiên (Mới nhất -> Cũ hơn)
    # Vì đã update requirements.txt nên máy chủ sẽ hiểu các tên này
    priority_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-pro"
    ]

    for key in API_KEYS:
        try:
            genai.configure(api_key=key)
            
            # Thử từng model trong danh sách
            for model_name in priority_models:
                try:
                    # Cấu hình an toàn để tránh lỗi safety filter
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    # Nếu lỗi 404 (không tìm thấy model) -> Thử model tiếp theo
                    if "404" in str(e) or "not found" in str(e):
                        continue
                    # Nếu lỗi 429 (Quá tải) -> Break để đổi Key khác
                    elif "429" in str(e):
                        break
                    else:
                        break # Lỗi khác đổi key
        except:
            continue
            
    return "⚠️ HỆ THỐNG ĐANG BẬN. Vui lòng thử lại sau 30 giây."

# --- GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #004d99;'>🏫 HỆ THỐNG HỖ TRỢ RA ĐỀ THI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>© Bản quyền thuộc về trường PTDTBT THCS Mùn Chung</p>", unsafe_allow_html=True)

if st.session_state.get('first', True):
    st.info("💡 Mẹo: Trên điện thoại, bấm mũi tên `>` góc trái trên để xem menu.")
    st.session_state['first'] = False

# Sidebar
with st.sidebar:
    st.header("Cấu hình")
    st.success("Trạng thái: Đã kết nối")

# Tabs
tab1, tab2, tab3 = st.tabs(["⚡ Soạn Nhanh", "📂 Từ File", "📥 Tải Về"])

# Tab 1
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        topic = st.text_input("Chủ đề:", "Lịch sử Điện Biên Phủ")
        grade = st.selectbox("Khối:", ["6", "7", "8", "9"])
    with c2:
        num = st.slider("Số câu:", 5, 20, 10)
        lv = st.select_slider("Độ khó:", ["Nhận biết", "Thông hiểu", "Vận dụng"])
    
    if st.button("🚀 SOẠN ĐỀ NGAY", type="primary", use_container_width=True):
        p = f"Đóng vai giáo viên lớp {grade}. Soạn {num} câu trắc nghiệm về '{topic}'. Độ khó: {lv}. Có đáp án chi tiết cuối bài."
        with st.spinner("Đang kết nối hệ thống AI..."):
            res = get_gemini_response_smart(p)
            st.session_state['res'] = res
            st.session_state['top'] = topic
            st.success("Đã xong! Qua tab Tải Về để lấy file.")
            st.write(res)

# Tab 2
with tab2:
    f = st.file_uploader("Tải tài liệu (PDF/Word):", type=['pdf','docx'])
    if st.button("🚀 PHÂN TÍCH & SOẠN", use_container_width=True):
        if f:
            with st.spinner("Đang đọc tài liệu..."):
                content = read_pdf(f) if f.name.endswith('.pdf') else read_docx(f)
                p = f"Dựa vào văn bản sau: {content}. Hãy soạn 10 câu trắc nghiệm có đáp án."
                res = get_gemini_response_smart(p)
                st.session_state['res'] = res
                st.session_state['top'] = f.name
                st.success("Đã xong! Qua tab Tải Về để lấy file.")
                st.write(res)

# Tab 3
with tab3:
    if 'res' in st.session_state:
        final = st.text_area("", st.session_state['res'], height=300)
        data = create_docx(final, st.session_state['top'])
        st.download_button("📥 TẢI FILE WORD", data, f"{st.session_state['top']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else: st.info("Chưa có dữ liệu đề thi.")
