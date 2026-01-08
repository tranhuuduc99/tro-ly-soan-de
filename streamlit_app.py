import streamlit as st
import requests
import json
import time
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import PyPDF2

# ==============================================================================
# 1. CẤU HÌNH
# ==============================================================================
st.set_page_config(
    page_title="Hệ Thống Ra Đề (v1 Stable)",
    page_icon="🏫",
    layout="wide"
)

# Danh sách Key
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# CSS
st.markdown("""
<style>
    .main-title {font-size: 2rem; color: #004d99; text-align: center; font-weight: bold; margin-bottom: 5px; text-transform: uppercase;}
    .stButton>button {background-color: #004d99; color: white; font-weight: bold; border-radius: 5px; height: 3em; border: none;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. XỬ LÝ AI (DÙNG API V1 CHÍNH THỨC)
# ==============================================================================

def call_gemini_v1(prompt):
    # Dùng bản v1 chính thức (Ổn định hơn v1beta)
    # Model: gemini-pro (Bản chuẩn nhất của Google)
    url_base = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    
    headers = {'Content-Type': 'application/json'}
    
    # Tắt bộ lọc an toàn để tránh bị block ngầm
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
        final_url = f"{url_base}?key={key.strip()}"
        
        try:
            response = requests.post(final_url, headers=headers, data=json.dumps(payload), timeout=15)
            
            # Nếu thành công (200 OK)
            if response.status_code == 200:
                data = response.json()
                # Kiểm tra kỹ xem có nội dung không hay bị lọc mất
                try:
                    return data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    # Trường hợp Google trả về 200 nhưng không có nội dung (do bị lọc)
                    return "⚠️ AI từ chối trả lời vì lý do an toàn. Vui lòng đổi chủ đề khác."
            
            # Nếu lỗi, ghi lại mã lỗi để debug
            else:
                logs.append(f"Key {i+1}: Lỗi {response.status_code} ({response.text[:100]})")
                continue

        except Exception as e:
            logs.append(f"Key {i+1}: Lỗi kết nối ({str(e)})")
            continue

    # Nếu thử hết mà vẫn lỗi
    return f"❌ LỖI HỆ THỐNG:\n{'\n'.join(logs)}"

# ==============================================================================
# 3. XỬ LÝ FILE & WORD
# ==============================================================================

def read_file_content(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            return "".join([page.extract_text() or "" for page in reader.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
    except: return ""
    return ""

def create_formatted_word(content, topic, subject, grade):
    doc = Document()
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h.runs[0].font.color.rgb = RGBColor(0, 0, 0)
    h.runs[0].bold = True
    
    p = doc.add_paragraph(f'ĐỀ KIỂM TRA MÔN: {subject.upper()}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold = True

    p2 = doc.add_paragraph(f'Chủ đề: {topic} - {grade}')
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph("Họ tên: ........................................................... Lớp: ....................")
    doc.add_paragraph("-" * 70).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(content)
    
    section = doc.sections[0]
    section.footer.paragraphs[0].text = "Hệ thống AI - Trường PTDTBT THCS Mùn Chung"
    return doc

# ==============================================================================
# 4. GIAO DIỆN
# ==============================================================================

st.markdown('<div class="main-title">HỆ THỐNG TRỢ LÝ RA ĐỀ THI</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center;">Trường PTDTBT THCS Mùn Chung</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚡ SOẠN CHỦ ĐỀ", "📂 SOẠN TỪ FILE", "📥 KẾT QUẢ"])

# TAB 1
with tab1:
    c1, c2, c3 = st.columns(3)
    with c1: grade = st.selectbox("Khối:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "THPT", "Tiểu học"])
    with c2: subject = st.selectbox("Môn:", ["Toán", "Văn", "Anh", "Sử", "Địa", "Lý", "Hóa", "Sinh", "GDCD", "Tin", "Công nghệ"])
    with c3: q_num = st.number_input("Số câu:", 5, 50, 10)

    topic = st.text_input("Chủ đề:", value="Ôn tập chương I")
    
    if st.button("🚀 TẠO ĐỀ NGAY", use_container_width=True):
        prompt = f"Giáo viên {subject} lớp {grade}. Soạn {q_num} câu trắc nghiệm chủ đề '{topic}'. Có đáp án."
        with st.spinner("Đang kết nối API v1..."):
            res = call_gemini_v1(prompt)
            if "❌" in res or "⚠️" in res: st.error(res)
            else:
                st.session_state['result'] = res
                st.session_state['topic'] = topic
                st.session_state['subject'] = subject
                st.session_state['grade'] = grade
                st.success("Thành công! Xem kết quả ở tab bên cạnh.")

# TAB 2
with tab2:
    uploaded_file = st.file_uploader("Upload File:", type=['pdf', 'docx'])
    if st.button("🚀 XỬ LÝ FILE", use_container_width=True):
        if uploaded_file:
            content = read_file_content(uploaded_file)
            if len(content) < 20: st.warning("File lỗi.")
            else:
                prompt = f"Dựa vào văn bản: {content[:10000]}. Soạn 10 câu trắc nghiệm môn Tổng hợp. Có đáp án."
                res = call_gemini_v1(prompt)
                if "❌" in res or "⚠️" in res: st.error(res)
                else:
                    st.session_state['result'] = res
                    st.session_state['topic'] = uploaded_file.name
                    st.session_state['subject'] = "Tài liệu"
                    st.session_state['grade'] = ""
                    st.success("Thành công! Xem kết quả ở tab bên cạnh.")

# TAB 3
with tab3:
    if 'result' in st.session_state:
        st.text_area("Nội dung:", st.session_state['result'], height=500)
        docx = create_formatted_word(st.session_state['result'], st.session_state['topic'], st.session_state.get('subject',''), st.session_state.get('grade',''))
        st.download_button("📥 TẢI WORD", BytesIO(docx.read()), "De_Thi.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
