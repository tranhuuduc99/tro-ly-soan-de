import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
from docx.enum.text import WD_ALIGN_PARAGRAPH
import PyPDF2

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phần mềm soạn đề tự động 2.0", page_icon="🏫", layout="wide")

# --- CẤU HÌNH API KEY ---
# Chỉ sử dụng 1 Key duy nhất theo yêu cầu
API_KEYS = [
    "AIzaSyB_A61JcSMdmUjqCcHEc3Sg-Vv79j-yarE"
]

# --- 1. HÀM TỰ ĐỘNG TÌM MODEL TỐT NHẤT ---
def get_best_available_model(api_key):
    """Hỏi Google xem model nào đang rảnh và dùng được"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Ưu tiên tìm các model Flash hoặc Pro mới nhất
            for model in data.get('models', []):
                name = model['name'].replace('models/', '')
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    if 'gemini-1.5-flash' in name: return name
                    if 'gemini-1.5-pro' in name: return name
            # Nếu không tìm thấy cái ưu tiên, lấy cái đầu tiên hỗ trợ generateContent
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    return model['name'].replace('models/', '')
    except:
        pass
    return "gemini-1.5-flash" # Model dự phòng

# --- 2. HÀM GỌI API ---
def call_gemini_auto(prompt):
    logs = []
    
    # Lấy key duy nhất
    key = API_KEYS[0]
    clean_key = key.strip()
    
    # Bước 1: Dò model
    current_model = get_best_available_model(clean_key)
    
    # Bước 2: Gọi API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={clean_key}"
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
        elif response.status_code == 429:
            return "⚠️ HỆ THỐNG QUÁ TẢI (429). Bạn đang thao tác quá nhanh. Vui lòng đợi 1 phút rồi thử lại."
        else:
            return f"⚠️ Lỗi kết nối ({response.status_code}). Chi tiết: {response.text}"

    except Exception as e:
        return f"⚠️ Lỗi mạng: {str(e)}"

# --- 3. HÀM XỬ LÝ FILE ---
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

# --- 4. HÀM TẠO FILE WORD ---
def create_word(content, topic, grade_info):
    doc = Document()
    
    # Header tên trường
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Tiêu đề đề thi
    p = doc.add_paragraph(f'ĐỀ KIỂM TRA: {topic.upper()}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Thông tin học sinh
    doc.add_paragraph(f"Lớp: {grade_info}      Họ và tên: .................................................")
    doc.add_paragraph("-" * 60)
    
    # Nội dung đề
    doc.add_paragraph(content)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center; color: #004d99;'>🏫 HỆ THỐNG RA ĐỀ THI (1 KEY)</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.success("✅ Đang chạy Key cá nhân")
    st.info("Hệ thống tự động dò tìm model ổn định nhất cho Key này.")

# Tabs chức năng
tab1, tab2, tab3 = st.tabs(["⚡ Soạn Theo Chủ Đề", "📂 Soạn Từ File", "📥 Tải Về & In"])

# --- TAB 1: SOẠN THEO CHỦ ĐỀ ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Nhập chủ đề / Bài học:", "Vợ chồng A Phủ")
        # Chọn lớp từ 1 đến 12
        grade = st.selectbox("Chọn Khối Lớp:", [str(i) for i in range(1, 13)], index=11) 
        subject = st.text_input("Môn học (Tùy chọn):", "Ngữ Văn")
        
    with col2:
        num = st.slider("Số lượng câu hỏi:", 5, 40, 10)
        level = st.select_slider("Mức độ khó:", ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"])

    if st.button("🚀 BẮT ĐẦU SOẠN ĐỀ", type="primary", use_container_width=True):
        # Tùy chỉnh lời nhắc (Prompt) dựa trên lớp học
        context_prompt = ""
        if int(grade) <= 5:
            context_prompt = "Dùng ngôn ngữ đơn giản, dễ hiểu, phù hợp với tâm lý học sinh Tiểu học."
        elif int(grade) <= 9:
            context_prompt = "Dùng ngôn ngữ chuẩn mực, bám sát chương trình THCS."
        else:
            context_prompt = "Dùng ngôn ngữ học thuật, chính xác, bám sát cấu trúc đề thi THPT Quốc gia."

        full_prompt = (
            f"Bạn là giáo viên dạy môn {subject} lớp {grade}. "
            f"Hãy soạn {num} câu trắc nghiệm (có 4 đáp án A,B,C,D) về chủ đề: '{topic}'. "
            f"Độ khó: {level}. "
            f"{context_prompt} "
            f"Yêu cầu định dạng: Đề bài riêng và Đáp án chi tiết để ở cuối cùng."
        )
        
        with st.spinner(f"Đang kết nối AI để soạn đề Lớp {grade}..."):
            res = call_gemini_auto(full_prompt)
            st.session_state['res'] = res
            st.session_state['top'] = topic
            st.session_state['gr'] = grade
            
            if "⚠️" in res: st.error(res)
            else: st.success("Đã soạn xong!"); st.write(res)

# --- TAB 2: SOẠN TỪ FILE ---
with tab2:
    f = st.file_uploader("Tải lên tài liệu (PDF/Word) để AI đọc:", type=['pdf','docx'])
    grade_file = st.selectbox("Dành cho lớp:", [str(i) for i in range(1, 13)], index=8, key='gr_file')
    
    if st.button("🚀 PHÂN TÍCH & TẠO ĐỀ", use_container_width=True):
        if f:
            with st.spinner("AI đang đọc tài liệu..."):
                content = read_file(f)
                if len(content) < 50: 
                    st.warning("File quá ngắn hoặc không đọc được nội dung.")
                else:
                    prompt = (
                        f"Dựa vào nội dung văn bản sau đây: \n'{content[:15000]}'... \n"
                        f"Hãy đóng vai giáo viên lớp {grade_file}, soạn 10 câu hỏi trắc nghiệm ôn tập nội dung trên. "
                        f"Có đáp án chi tiết."
                    )
                    res = call_gemini_auto(prompt)
                    st.session_state['res'] = res
                    st.session_state['top'] = f"Tài liệu: {f.name}"
                    st.session_state['gr'] = grade_file
                    
                    if "⚠️" in res: st.error(res)
                    else: st.success("Thành công!"); st.write(res)

# --- TAB 3: TẢI VỀ ---
with tab3:
    if 'res' in st.session_state:
        st.info("Xem lại nội dung trước khi tải về:")
        txt_edit = st.text_area("Chỉnh sửa nhanh:", st.session_state['res'], height=300)
        
        # Nút tải về
        docx = create_word(txt_edit, st.session_state['top'], st.session_state.get('gr', ''))
        st.download_button(
            label="📥 TẢI FILE WORD (.DOCX)", 
            data=docx, 
            file_name=f"De_Thi_{st.session_state['top']}.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
            use_container_width=True
        )
    else:
        st.write("👈 Chưa có dữ liệu. Vui lòng tạo đề ở Tab 1 hoặc Tab 2 trước.")
