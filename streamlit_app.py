import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
from docx.enum.text import WD_ALIGN_PARAGRAPH
import PyPDF2

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ Thống Ra Đề", page_icon="🏫", layout="wide")

# --- API KEYS ---
# Tôi đã làm sạch Key để đảm bảo không dính ký tự lạ
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# --- HÀM GỌI API (SỬ DỤNG GEMINI-PRO ĐỂ TRÁNH LỖI 404) ---
def call_gemini_stable(prompt):
    # QUAN TRỌNG: Dùng 'gemini-pro' thay vì 'flash'. 
    # gemini-pro có mặt ở mọi server nên sẽ KHÔNG BỊ LỖI 404.
    model = "gemini-pro"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    logs = []

    for i, key in enumerate(API_KEYS):
        try:
            final_url = f"{url}?key={key.strip()}"
            response = requests.post(final_url, headers=headers, data=json.dumps(payload), timeout=25)
            
            if response.status_code == 200:
                # Thành công!
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                # Quá tải -> Thử key tiếp theo
                logs.append(f"Key {i+1}: Quá tải (429)")
                continue
            else:
                # Lỗi khác
                logs.append(f"Key {i+1}: Lỗi {response.status_code} - {response.text[:100]}")
                continue

        except Exception as e:
            logs.append(f"Key {i+1}: Lỗi mạng {str(e)}")
            continue

    # Nếu chạy hết 3 key mà vẫn không được
    return f"⚠️ HỆ THỐNG ĐANG BẬN. Vui lòng thử lại sau 30 giây.\nChi tiết: {'; '.join(logs)}"

# --- CÁC HÀM XỬ LÝ FILE (GIỮ NGUYÊN) ---
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
    
    # Tiêu đề trường căn giữa
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Tên đề bài
    p = doc.add_paragraph(f'ĐỀ KIỂM TRA: {topic.upper()}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph("Họ tên: ................................................. Lớp: ............")
    doc.add_paragraph("-" * 60)
    doc.add_paragraph(content)
    
    # Footer
    section = doc.sections[0]
    footer = section.footer
    p_footer = footer.paragraphs[0]
    p_footer.text = "Hệ thống hỗ trợ ra đề thi tự động - THCS Mùn Chung"

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #004d99;'>🏫 HỆ THỐNG HỖ TRỢ RA ĐỀ THI</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: grey;'>© Bản quyền thuộc về trường PTDTBT THCS Mùn Chung</div>", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2232/2232688.png", width=80)
    st.header("Trạng thái hệ thống")
    st.success("✅ Kết nối: GEMINI-PRO (Stable)")
    st.info("Phiên bản ổn định nhất")

# Tabs
tab1, tab2, tab3 = st.tabs(["⚡ Soạn Nhanh", "📂 Từ File", "📥 Tải Về"])

# Tab 1
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Chủ đề:", "Chiến thắng Điện Biên Phủ")
        grade = st.selectbox("Khối:", ["6", "7", "8", "9"])
    with col2:
        num = st.slider("Số câu:", 5, 20, 10)
        level = st.select_slider("Độ khó:", ["Nhận biết", "Thông hiểu", "Vận dụng"])

    if st.button("🚀 SOẠN ĐỀ NGAY", type="primary", use_container_width=True):
        prompt = f"Đóng vai giáo viên lớp {grade}. Soạn {num} câu trắc nghiệm về chủ đề '{topic}'. Độ khó: {level}. Yêu cầu: Có đáp án chi tiết cuối bài."
        with st.spinner("Đang kết nối hệ thống AI..."):
            res = call_gemini_stable(prompt)
            st.session_state['res'] = res
            st.session_state['top'] = topic
            
            if "⚠️" in res:
                st.error(res)
            else:
                st.success("Đã xong! Mời thầy/cô xem kết quả.")
                st.write(res)

# Tab 2
with tab2:
    f = st.file_uploader("Upload file tài liệu:", type=['pdf','docx'])
    if st.button("🚀 PHÂN TÍCH & SOẠN", use_container_width=True):
        if f:
            with st.spinner("Đang đọc tài liệu..."):
                content = read_file(f)
                if len(content) < 20: st.warning("File không có nội dung chữ.")
                else:
                    prompt = f"Dựa vào văn bản sau: {content[:10000]}. Soạn 10 câu trắc nghiệm có đáp án."
                    res = call_gemini_stable(prompt)
                    st.session_state['res'] = res
                    st.session_state['top'] = f.name
                    if "⚠️" in res: st.error(res)
                    else: st.success("Đã xong!"); st.write(res)

# Tab 3
with tab3:
    if 'res' in st.session_state:
        txt = st.text_area("Chỉnh sửa nội dung:", st.session_state['res'], height=300)
        docx = create_word(txt, st.session_state['top'])
        st.download_button("📥 TẢI FILE WORD", docx, f"{st.session_state['top']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else: st.info("Chưa có dữ liệu.")
