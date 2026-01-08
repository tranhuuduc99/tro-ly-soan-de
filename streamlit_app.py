import streamlit as st
import requests
import json
import time
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import PyPDF2
import pandas as pd

# ==============================================================================
# 1. CẤU HÌNH
# ==============================================================================
st.set_page_config(
    page_title="Hệ Thống Ra Đề Nhanh",
    page_icon="⚡",
    layout="wide"
)

# Danh sách Key
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

st.markdown("""
<style>
    .main-title {font-size: 2rem; color: #B22222; text-align: center; font-weight: bold; margin-bottom: 5px; text-transform: uppercase;}
    .stButton>button {background-color: #B22222; color: white; font-weight: bold; border-radius: 5px; height: 3em; border: none;}
    .status-log {font-size: 0.9rem; color: #555; font-family: monospace;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. XỬ LÝ AI (TỐC ĐỘ CAO - KHÔNG CHỜ ĐỢI)
# ==============================================================================

def generate_exam_fast(prompt):
    # Dùng list này để quét. Nếu Flash lỗi 404 thì tự nhảy sang Pro.
    models_to_try = ["gemini-1.5-flash", "gemini-pro"]
    
    safety = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]

    status_container = st.empty() # Khung hiện trạng thái
    logs = []

    # Thuật toán quét nhanh
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}], "safetySettings": safety}

        for i, key in enumerate(API_KEYS):
            clean_key = key.strip()
            final_url = f"{url}?key={clean_key}"
            
            # Cập nhật trạng thái cho người dùng thấy
            status_container.markdown(f"⚡ Đang thử: **Model {model}** - **Key {i+1}**...")
            
            try:
                # TIMEOUT 8 GIÂY: Quá 8s không trả lời là cắt luôn
                response = requests.post(final_url, headers=headers, data=json.dumps(payload), timeout=8)
                
                if response.status_code == 200:
                    status_container.success(f"✅ Kết nối thành công! (Model: {model} - Key {i+1})")
                    time.sleep(1)
                    status_container.empty()
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    # Lỗi thì bỏ qua ngay, không chờ
                    logs.append(f"{model}/Key{i+1}: Lỗi {response.status_code}")
                    continue
            except Exception as e:
                logs.append(f"{model}/Key{i+1}: Timeout/Lỗi mạng")
                continue
    
    status_container.error("❌ Thất bại.")
    return f"⚠️ KHÔNG KẾT NỐI ĐƯỢC. Có thể cả 3 Key đều đã hết hạn mức trong phút này.\nChi tiết: {'; '.join(logs)}"

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

st.markdown('<div class="main-title">HỆ THỐNG RA ĐỀ TỐC ĐỘ CAO</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center;">Trường PTDTBT THCS Mùn Chung</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚡ SOẠN CHỦ ĐỀ", "📂 SOẠN TỪ FILE", "📊 KẾT QUẢ"])

# TAB 1
with tab1:
    c1, c2, c3 = st.columns(3)
    with c1: grade = st.selectbox("Khối:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "Lớp 10", "Lớp 11", "Lớp 12", "Lớp 1-5"])
    with c2: subject = st.selectbox("Môn:", ["Toán", "Văn", "Anh", "Sử", "Địa", "Lý", "Hóa", "Sinh", "GDCD", "Tin", "Công nghệ"])
    with c3: q_num = st.number_input("Số câu:", 5, 50, 10)

    topic = st.text_input("Chủ đề:", value="Ôn tập học kỳ 1")
    
    if st.button("🚀 TẠO ĐỀ NGAY (FAST)", use_container_width=True):
        prompt = f"Giáo viên {subject} lớp {grade}. Soạn {q_num} câu trắc nghiệm chủ đề '{topic}'. Có đáp án."
        res = generate_exam_fast(prompt)
        if "⚠️" in res: st.error(res)
        else:
            st.session_state['result'] = res
            st.session_state['topic'] = topic
            st.session_state['subject'] = subject
            st.session_state['grade'] = grade
            st.session_state['q_num'] = q_num
            st.success("Xong! Qua tab Kết Quả xem nhé.")

# TAB 2
with tab2:
    uploaded_file = st.file_uploader("Upload File:", type=['pdf', 'docx'])
    if st.button("🚀 PHÂN TÍCH FILE", use_container_width=True):
        if uploaded_file:
            content = read_file_content(uploaded_file)
            if len(content) < 20: st.warning("File lỗi.")
            else:
                prompt = f"Dựa vào văn bản: {content[:10000]}. Soạn 10 câu trắc nghiệm môn Tổng hợp. Có đáp án."
                res = generate_exam_fast(prompt)
                if "⚠️" in res: st.error(res)
                else:
                    st.session_state['result'] = res
                    st.session_state['topic'] = uploaded_file.name
                    st.session_state['subject'] = "Tài liệu"
                    st.session_state['grade'] = ""
                    st.session_state['q_num'] = 10
                    st.success("Xong! Qua tab Kết Quả xem nhé.")

# TAB 3
with tab3:
    if 'result' in st.session_state:
        c_res1, c_res2 = st.columns([2, 1])
        with c_res1:
            st.text_area("Nội dung:", st.session_state['result'], height=500)
            docx = create_formatted_word(st.session_state['result'], st.session_state['topic'], st.session_state.get('subject',''), st.session_state.get('grade',''))
            st.download_button("📥 TẢI WORD", BytesIO(docx.read()), "De_Thi.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with c_res2:
            st.subheader("Biểu đồ")
            # Vẽ biểu đồ đơn giản không cần logic phức tạp
            st.bar_chart({"NB": 3, "TH": 4, "VD": 2, "VDC": 1})
            st.info("Biểu đồ minh họa cơ cấu đề thi.")
            if st.button("💡 Gợi ý Sư phạm"):
                st.write("Đang tải gợi ý...")
                review = generate_exam_fast(f"Nhận xét ngắn đề thi: {st.session_state['result'][:1000]}")
                st.info(review)
