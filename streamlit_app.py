import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
import PyPDF2

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ Thống Ra Đề", page_icon="🏫", layout="wide")

# --- XỬ LÝ API KEY (QUAN TRỌNG: Cắt bỏ khoảng trắng thừa) ---
RAW_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]
# Tự động làm sạch Key (xóa dấu cách, xuống dòng nếu có)
API_KEYS = [k.strip() for k in RAW_KEYS if k.strip()]

# --- HÀM GỌI API SIÊU BỀN (HEADER AUTH) ---
def call_gemini_final(prompt):
    # Chỉ dùng 1 model ổn định nhất để test trước
    model = "gemini-1.5-flash"
    
    # URL chuẩn của Google
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    # Cấu hình Header (An toàn hơn để trên URL)
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    # Danh sách lỗi để debug
    error_logs = []

    for i, key in enumerate(API_KEYS):
        try:
            # Thêm key vào query param (Cách chuẩn nhất hiện tại)
            final_url = f"{url}?key={key}"
            
            # Gửi Request
            response = requests.post(final_url, headers=headers, data=json.dumps(payload), timeout=20)
            
            # 1. Nếu thành công (200 OK)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # 2. Nếu lỗi, ghi lại chi tiết
            else:
                error_body = response.text
                error_logs.append(f"Key {i+1} lỗi {response.status_code}: {error_body}")
                # Nếu lỗi 404 (Sai model) hoặc 400 (Sai request) -> Thử key tiếp theo vẫn thế thôi, nhưng cứ thử.
                # Nếu lỗi 429 (Hết tiền) -> Thử key tiếp theo là đúng.
                if response.status_code == 429:
                    continue
                else:
                    continue

        except Exception as e:
            error_logs.append(f"Key {i+1} lỗi kết nối: {str(e)}")
            continue

    # Nếu chạy hết vòng lặp mà vẫn xịt
    return f"⚠️ KẾT NỐI THẤT BẠI. ĐỌC KỸ LỖI SAU:\n" + "\n".join(error_logs)

# --- CÁC HÀM XỬ LÝ FILE & WORD (GIỮ NGUYÊN) ---
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
    doc.add_paragraph("-" * 60)
    doc.add_paragraph(content)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #004d99;'>🏫 HỆ THỐNG RA ĐỀ (FINAL FIX)</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.success(f"Đã nạp {len(API_KEYS)} API Keys")
    st.info("Chế độ: Deep Debug")

# Tabs
tab1, tab2, tab3 = st.tabs(["⚡ Soạn Nhanh", "📂 Từ File", "📥 Tải Về"])

# Tab 1
with tab1:
    topic = st.text_input("Chủ đề:", "Lịch sử Điện Biên Phủ")
    grade = st.selectbox("Khối:", ["6", "7", "8", "9"])
    if st.button("🚀 SOẠN ĐỀ", type="primary", use_container_width=True):
        p = f"Đóng vai giáo viên lớp {grade}. Soạn 10 câu trắc nghiệm về '{topic}'. Có đáp án."
        with st.spinner("Đang kết nối..."):
            res = call_gemini_final(p)
            st.session_state['res'] = res
            st.session_state['top'] = topic
            
            if "⚠️" in res:
                st.error("LỖI CHI TIẾT TỪ GOOGLE (Chụp màn hình gửi tôi xem):")
                st.code(res, language='json')
            else:
                st.success("Thành công!")
                st.write(res)

# Tab 2
with tab2:
    f = st.file_uploader("Upload file:", type=['pdf','docx'])
    if st.button("🚀 XỬ LÝ FILE", use_container_width=True):
        if f:
            with st.spinner("Đang xử lý..."):
                content = read_file(f)
                p = f"Dựa vào văn bản: {content[:10000]}. Soạn 10 câu trắc nghiệm."
                res = call_gemini_final(p)
                st.session_state['res'] = res
                st.session_state['top'] = f.name
                if "⚠️" in res:
                    st.error(res)
                else:
                    st.success("Thành công!"); st.write(res)

# Tab 3
with tab3:
    if 'res' in st.session_state:
        txt = st.text_area("", st.session_state['res'], height=300)
        docx = create_word(txt, st.session_state['top'])
        st.download_button("📥 TẢI WORD", docx, f"{st.session_state['top']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
