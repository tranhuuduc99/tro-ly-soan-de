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
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# --- HÀM TỰ ĐỘNG TÌM MODEL (VŨ KHÍ BÍ MẬT) ---
def get_best_available_model(api_key):
    """Hỏi Google xem model nào đang rảnh và dùng được"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Lọc ra các model hỗ trợ tạo văn bản (generateContent)
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    # Ưu tiên các model Flash hoặc Pro vì nó thông minh
                    if 'flash' in model['name'] or 'pro' in model['name']:
                        return model['name'].replace('models/', '')
            
            # Nếu không tìm thấy cái ưu tiên, lấy cái đầu tiên tìm được
            if data.get('models'):
                return data['models'][0]['name'].replace('models/', '')
    except:
        pass
    return "gemini-1.5-flash" # Fallback cuối cùng nếu không dò được

# --- HÀM GỌI API CHÍNH ---
def call_gemini_auto(prompt):
    logs = []

    for i, key in enumerate(API_KEYS):
        clean_key = key.strip()
        
        # Bước 1: Tự động dò tìm model phù hợp với Key này
        current_model = get_best_available_model(clean_key)
        
        # Bước 2: Gọi API với model vừa tìm được
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={clean_key}"
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

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                logs.append(f"Key {i+1}: Quá tải.")
                continue
            else:
                logs.append(f"Key {i+1} ({current_model}): Lỗi {response.status_code}")
                continue

        except Exception as e:
            logs.append(f"Key {i+1}: Lỗi mạng {str(e)}")
            continue

    return f"⚠️ KHÔNG THỂ TẠO ĐỀ. Lỗi chi tiết:\n{'; '.join(logs)}\n(Hãy thử lại sau 1 phút)"

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
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(f'ĐỀ KIỂM TRA: {topic.upper()}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9626/9626622.png", width=80)
    st.header("Trạng thái")
    st.success("✅ Chế độ: Tự động dò Model")
    st.caption("Hệ thống sẽ tự tìm model tốt nhất hiện có.")

# Tabs
tab1, tab2, tab3 = st.tabs(["⚡ Soạn Nhanh", "📂 Từ File", "📥 Tải Về"])

# Tab 1
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Chủ đề:", "Tác phẩm Lão Hạc")
        grade = st.selectbox("Khối:", ["6", "7", "8", "9"])
    with col2:
        num = st.slider("Số câu:", 5, 20, 10)
        level = st.select_slider("Độ khó:", ["Nhận biết", "Thông hiểu", "Vận dụng"])

    if st.button("🚀 SOẠN ĐỀ NGAY", type="primary", use_container_width=True):
        prompt = f"Đóng vai giáo viên lớp {grade}. Soạn {num} câu trắc nghiệm về chủ đề '{topic}'. Độ khó: {level}. Có đáp án chi tiết."
        with st.spinner("Đang tìm model AI và soạn đề..."):
            res = call_gemini_auto(prompt)
            st.session_state['res'] = res
            st.session_state['top'] = topic
            
            if "⚠️" in res: st.error(res)
            else: st.success("Thành công!"); st.write(res)

# Tab 2
with tab2:
    f = st.file_uploader("Upload file tài liệu:", type=['pdf','docx'])
    if st.button("🚀 PHÂN TÍCH & SOẠN", use_container_width=True):
        if f:
            with st.spinner("Đang xử lý..."):
                content = read_file(f)
                if len(content) < 20: st.warning("File rỗng.")
                else:
                    prompt = f"Dựa vào văn bản: {content[:10000]}. Soạn 10 câu trắc nghiệm."
                    res = call_gemini_auto(prompt)
                    st.session_state['res'] = res
                    st.session_state['top'] = f.name
                    if "⚠️" in res: st.error(res)
                    else: st.success("Thành công!"); st.write(res)

# Tab 3
with tab3:
    if 'res' in st.session_state:
        txt = st.text_area("Nội dung đề:", st.session_state['res'], height=300)
        docx = create_word(txt, st.session_state['top'])
        st.download_button("📥 TẢI FILE WORD", docx, f"{st.session_state['top']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else: st.info("Chưa có dữ liệu.")
