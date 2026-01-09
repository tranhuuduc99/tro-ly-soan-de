import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
from docx.enum.text import WD_ALIGN_PARAGRAPH
import PyPDF2

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phần mềm Soạn đề Pro", page_icon="🎓", layout="wide")

# --- XỬ LÝ API KEY BẢO MẬT ---
def get_api_key():
    """AIzaSyBY29kMfQWCB7ASsBrWcPHKn8EG8kYq_Bc"""
    try:
        # Ưu tiên lấy từ Secrets (Bảo mật)
        return st.secrets["GEMINI_API_KEY"]
    except FileNotFoundError:
        # Dự phòng: Nhập trực tiếp trên giao diện nếu chưa cấu hình file secrets
        return st.sidebar.text_input("AIzaSyBY29kMfQWCB7ASsBrWcPHKn8EG8kYq_Bc", type="password")
    except KeyError:
        return st.sidebar.text_input("AIzaSyBY29kMfQWCB7ASsBrWcPHKn8EG8kYq_Bc", type="password")

# --- HÀM GỌI GEMINI ---
def call_gemini(prompt, api_key):
    if not api_key:
        return "AIzaSyBY29kMfQWCB7ASsBrWcPHKn8EG8kYq_Bc"

    # Dùng model Flash cho nhanh và ổn định
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 403:
            return "❌ Lỗi Key: Key không hợp lệ hoặc bị Google chặn. Hãy tạo Key mới."
        elif response.status_code == 429:
            return "⏳ Hệ thống đang bận, vui lòng thử lại sau 5 giây."
        else:
            return f"❌ Lỗi kết nối: {response.status_code}"
    except Exception as e:
        return f"❌ Lỗi hệ thống: {str(e)}"

# --- HÀM ĐỌC FILE ---
def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            return text
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        return ""
    except: return "Lỗi đọc file."

# --- HÀM TẠO FILE WORD KẾT QUẢ ---
def create_word(content, topic, grade_info):
    doc = Document()
    
    # Header
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(f'ĐỀ KIỂM TRA: {topic.upper()}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Lớp: {grade_info}      Họ và tên: .................................................")
    doc.add_paragraph("-" * 60)
    
    # Nội dung
    doc.add_paragraph(content)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- GIAO DIỆN CHÍNH ---
st.title("🎓 TRỢ LÝ SOẠN ĐỀ THI 2.0")
st.markdown("---")

# Lấy Key an toàn
my_api_key = get_api_key()

# Cảnh báo nếu chưa có Key
if not my_api_key:
    st.warning("⚠️ Chưa tìm thấy API Key. Vui lòng tạo file `.streamlit/secrets.toml` hoặc nhập Key vào thanh bên trái.")

# Tabs chức năng
tab1, tab2 = st.tabs(["📝 Soạn theo chủ đề", "📂 Soạn từ tài liệu"])

# --- TAB 1: SOẠN THEO CHỦ ĐỀ ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        grade = st.selectbox("Khối lớp:", ["6", "7", "8", "9"], index=3)
        subject = st.text_input("Môn học:", "Ngữ Văn")
    with col2:
        topic = st.text_input("Nhập chủ đề / Tên bài học:", "Bài thơ Đồng Chí")
    
    btn_create = st.button("🚀 Soạn đề ngay", type="primary")

    if btn_create and topic:
        if not my_api_key:
            st.error("Thiếu API Key!")
        else:
            prompt = (
                f"Đóng vai giáo viên {subject} lớp {grade}. "
                f"Hãy soạn đề kiểm tra 1 tiết về chủ đề: '{topic}'.\n"
                f"Cấu trúc: 3 điểm trắc nghiệm (12 câu), 7 điểm tự luận (2 câu).\n"
                f"Yêu cầu: Có đáp án và thang điểm chi tiết."
            )
            with st.spinner("🤖 Đang soạn thảo..."):
                result = call_gemini(prompt, my_api_key)
                st.session_state['result_text'] = result
                st.session_state['topic_name'] = topic
                st.session_state['grade_name'] = grade

# --- TAB 2: SOẠN TỪ FILE ---
with tab2:
    uploaded_file = st.file_uploader("Tải lên tài liệu (PDF/Word):", type=['pdf', 'docx'])
    btn_analyze = st.button("🚀 Phân tích & Ra đề")
    
    if btn_analyze and uploaded_file:
        if not my_api_key:
            st.error("Thiếu API Key!")
        else:
            file_content = read_file(uploaded_file)
            prompt = (
                f"Dựa vào nội dung tài liệu sau đây:\n\n{file_content[:10000]}\n\n"
                f"Hãy soạn một đề kiểm tra ngắn (15 phút) gồm 10 câu trắc nghiệm có đáp án."
            )
            with st.spinner("🤖 Đang đọc tài liệu và ra đề..."):
                result = call_gemini(prompt, my_api_key)
                st.session_state['result_text'] = result
                st.session_state['topic_name'] = uploaded_file.name
                st.session_state['grade_name'] = "Tài liệu"

# --- HIỂN THỊ KẾT QUẢ ---
if 'result_text' in st.session_state:
    st.divider()
    st.subheader("📄 Kết quả:")
    st.text_area("Nội dung đề:", st.session_state['result_text'], height=400)
    
    # Nút tải về
    docx = create_word(st.session_state['result_text'], st.session_state['topic_name'], st.session_state['grade_name'])
    st.download_button(
        label="📥 Tải về file Word (.docx)",
        data=docx,
        file_name=f"De_Kiem_Tra_{st.session_state['topic_name']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
