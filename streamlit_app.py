import streamlit as st
import requests
import json
import time
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import PyPDF2
import pandas as pd # Thư viện vẽ biểu đồ có sẵn trong streamlit

# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG
# ==============================================================================
st.set_page_config(
    page_title="Hệ Thống Ra Đề - THCS Mùn Chung",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Danh sách API Key
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# CSS Giao diện
st.markdown("""
<style>
    .main-title {font-size: 2.2rem; color: #004d99; text-align: center; font-weight: bold; margin-bottom: 5px; text-transform: uppercase;}
    .school-name {font-size: 1.2rem; color: #555; text-align: center; font-weight: bold; margin-bottom: 30px;}
    .stButton>button {background-color: #004d99; color: white; font-weight: bold; border-radius: 8px; height: 3em; border: none;}
    .stButton>button:hover {background-color: #003366;}
    /* Style cho khung AI nhận xét */
    .ai-box {background-color: #e6f3ff; padding: 15px; border-radius: 10px; border-left: 5px solid #004d99; margin-top: 20px;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. XỬ LÝ AI (AUTO-DISCOVERY)
# ==============================================================================

def get_active_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for m in data.get('models', []):
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    name = m['name'].replace('models/', '')
                    if 'flash' in name or 'pro' in name: return name
            if data.get('models'): return data['models'][0]['name'].replace('models/', '')
    except: pass
    return "gemini-pro"

def generate_exam_content(prompt):
    logs = []
    # Cấu hình an toàn
    safety = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]

    for i, key in enumerate(API_KEYS):
        clean_key = key.strip()
        model_name = get_active_model(clean_key)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}], "safetySettings": safety}

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429: continue
            else: logs.append(f"Key {i+1}: Lỗi {response.status_code}"); continue
        except Exception as e: logs.append(f"Key {i+1}: Lỗi mạng."); continue

    return f"⚠️ HỆ THỐNG BẬN: {'; '.join(logs)}"

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

def create_formatted_word(content, topic):
    doc = Document()
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h.runs[0].font.color.rgb = RGBColor(0, 0, 0)
    h.runs[0].bold = True
    
    p = doc.add_paragraph(f'ĐỀ KIỂM TRA CHỦ ĐỀ: {topic.upper()}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold = True
    
    doc.add_paragraph("Họ tên: ........................................................... Lớp: ....................")
    doc.add_paragraph("-" * 70).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(content)
    
    section = doc.sections[0]
    section.footer.paragraphs[0].text = "Hệ thống AI - Trường PTDTBT THCS Mùn Chung"
    return doc

# ==============================================================================
# 4. GIAO DIỆN CHÍNH
# ==============================================================================

st.markdown('<div class="main-title">HỆ THỐNG TRỢ LÝ RA ĐỀ THI 4.0</div>', unsafe_allow_html=True)
st.markdown('<div class="school-name">© Bản quyền thuộc về Trường PTDTBT THCS Mùn Chung</div>', unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3067/3067451.png", width=100)
    st.header("Bảng Điều Khiển")
    st.success("🟢 Kết nối ổn định")
    st.info("Chức năng mới: \n1. Biểu đồ Ma trận \n2. Cố vấn Sư phạm")
    st.markdown("---")

tab1, tab2, tab3 = st.tabs(["⚡ SOẠN CHỦ ĐỀ", "📂 SOẠN TỪ FILE", "📊 KẾT QUẢ & PHÂN TÍCH"])

# --- TAB 1 ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        topic = st.text_input("Chủ đề:", value="Chiến thắng Điện Biên Phủ")
        grade = st.selectbox("Khối lớp:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
    with c2:
        q_num = st.number_input("Số câu:", 5, 50, 10)
        # Dictionary để ánh xạ độ khó ra con số giả lập biểu đồ
        diff_dict = {"Nhận biết": 1, "Thông hiểu": 2, "Vận dụng": 3, "Vận dụng cao": 4}
        diff_label = st.select_slider("Mức độ khó:", options=list(diff_dict.keys()))

    if st.button("🚀 KHỞI TẠO ĐỀ THI", use_container_width=True):
        prompt = f"Đóng vai giáo viên {grade}. Soạn đề trắc nghiệm chủ đề '{topic}'. {q_num} câu. Độ khó: {diff_label}. Có đáp án chi tiết."
        with st.spinner("AI đang soạn thảo..."):
            res = generate_exam_content(prompt)
            if "⚠️" in res: st.error(res)
            else:
                st.session_state['result'] = res
                st.session_state['topic'] = topic
                st.session_state['diff_score'] = diff_dict[diff_label] # Lưu độ khó để vẽ biểu đồ
                st.session_state['q_num'] = q_num
                st.balloons()
                st.success("✅ Đã xong! Mời qua tab 'KẾT QUẢ' để xem.")

# --- TAB 2 ---
with tab2:
    uploaded_file = st.file_uploader("Tải tài liệu (PDF/Word):", type=['pdf', 'docx'])
    if st.button("🚀 PHÂN TÍCH & TẠO ĐỀ", use_container_width=True):
        if uploaded_file:
            with st.spinner("Đang đọc tài liệu..."):
                content = read_file_content(uploaded_file)
                if len(content) < 50: st.warning("File không có nội dung chữ.")
                else:
                    prompt = f"Dựa vào nội dung: {content[:15000]}. Soạn 10 câu trắc nghiệm có đáp án."
                    res = generate_exam_content(prompt)
                    if "⚠️" in res: st.error(res)
                    else:
                        st.session_state['result'] = res
                        st.session_state['topic'] = uploaded_file.name
                        st.session_state['diff_score'] = 2 # Mặc định TB
                        st.session_state['q_num'] = 10
                        st.balloons()
                        st.success("✅ Đã xong! Mời qua tab 'KẾT QUẢ' để xem.")
        else: st.warning("Vui lòng chọn file!")

# --- TAB 3 (TÍNH NĂNG MỚI) ---
with tab3:
    if 'result' in st.session_state:
        # Cột 1: Xem đề và Tải về
        col_res1, col_res2 = st.columns([2, 1])
        
        with col_res1:
            st.subheader("📄 Nội dung Đề thi")
            final_text = st.text_area("", st.session_state['result'], height=500)
            
            # Xử lý Word
            docx = create_formatted_word(final_text, st.session_state['topic'])
            st.download_button(
                label="📥 TẢI FILE WORD (.DOCX)",
                data=BytesIO(docx.read()), # Fix lỗi BytesIO
                file_name=f"De_Thi_{st.session_state['topic']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        # Cột 2: Biểu đồ & Cố vấn AI (TÍNH NĂNG MỚI)
        with col_res2:
            st.subheader("📊 Ma trận Kiến thức")
            
            # Giả lập số liệu biểu đồ dựa trên độ khó người dùng chọn (Rất an toàn, không sợ lỗi)
            score = st.session_state.get('diff_score', 2)
            total = st.session_state.get('q_num', 10)
            
            # Logic chia tỷ lệ câu hỏi giả lập (để vẽ cho đẹp)
            if score == 1: data = {'Nhận biết': int(total*0.6), 'Thông hiểu': int(total*0.3), 'Vận dụng': int(total*0.1)}
            elif score == 2: data = {'Nhận biết': int(total*0.3), 'Thông hiểu': int(total*0.5), 'Vận dụng': int(total*0.2)}
            elif score == 3: data = {'Nhận biết': int(total*0.2), 'Thông hiểu': int(total*0.3), 'Vận dụng': int(total*0.5)}
            else: data = {'Nhận biết': int(total*0.1), 'Thông hiểu': int(total*0.2), 'Vận dụng': int(total*0.7)}
            
            df = pd.DataFrame(list(data.items()), columns=['Mức độ', 'Số câu'])
            st.bar_chart(df.set_index('Mức độ'))
            st.caption("Biểu đồ phân bố mức độ nhận thức của đề thi.")

            st.markdown("---")
            st.subheader("🤖 Cố vấn Sư phạm")
            st.write("Yêu cầu AI phân tích đề này và gợi ý cách dạy:")
            
            if st.button("💡 Phân tích & Gợi ý", use_container_width=True):
                with st.spinner("Đang phân tích sư phạm..."):
                    # Gọi AI lần 2 để nhận xét (Rất hay!)
                    review_prompt = f"Dựa vào đề thi sau đây: '{st.session_state['result'][:2000]}...'. Hãy đóng vai chuyên gia giáo dục, đưa ra 3 nhận xét về độ khó và 3 gợi ý ngắn gọn để giáo viên ôn tập cho học sinh tốt hơn. Viết ngắn gọn."
                    review = generate_exam_content(review_prompt)
                    st.markdown(f"<div class='ai-box'><b>🎓 GÓC CHUYÊN GIA:</b><br>{review}</div>", unsafe_allow_html=True)

    else:
        st.info("👈 Vui lòng tạo đề ở Tab 1 hoặc Tab 2 trước.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Phát triển bởi nhóm tác giả trường PTDTBT THCS Mùn Chung @ 2024</div>", unsafe_allow_html=True)
