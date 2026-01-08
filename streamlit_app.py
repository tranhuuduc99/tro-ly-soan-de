import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
from docx.enum.text import WD_ALIGN_PARAGRAPH
import PyPDF2

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phần mềm soạn đề Đa Năng 2.1", page_icon="🏫", layout="wide")

# --- CẤU HÌNH API KEY ---
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
            for model in data.get('models', []):
                name = model['name'].replace('models/', '')
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    if 'gemini-1.5-flash' in name: return name
                    if 'gemini-1.5-pro' in name: return name
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    return model['name'].replace('models/', '')
    except:
        pass
    return "gemini-1.5-flash"

# --- 2. HÀM GỌI API ---
def call_gemini_auto(prompt):
    key = API_KEYS[0]
    clean_key = key.strip()
    current_model = get_best_available_model(clean_key)
    
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
            return "⚠️ HỆ THỐNG QUÁ TẢI (429). Vui lòng đợi 1 phút rồi thử lại."
        else:
            return f"⚠️ Lỗi kết nối ({response.status_code})."
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
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph(f'ĐỀ KIỂM TRA: {topic.upper()}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f"Lớp: {grade_info}      Họ và tên: .................................................")
    doc.add_paragraph("-" * 60)
    doc.add_paragraph(content)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center; color: #004d99;'>🏫 SOẠN ĐỀ ĐA DẠNG (TN + ĐÚNG SAI + TỰ LUẬN)</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.success("✅ Đang chạy Key cá nhân")
    st.info("Phiên bản 2.1: Hỗ trợ cấu trúc đề thi mới.")

tab1, tab2, tab3 = st.tabs(["⚡ Soạn Theo Chủ Đề", "📂 Soạn Từ File", "📥 Tải Về & In"])

# --- TAB 1: SOẠN THEO CHỦ ĐỀ ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Nhập chủ đề / Bài học:", "Vợ chồng A Phủ")
        grade = st.selectbox("Chọn Khối Lớp:", [str(i) for i in range(1, 13)], index=11) 
        subject = st.text_input("Môn học:", "Ngữ Văn")
        level = st.select_slider("Mức độ khó:", ["Cơ bản", "Khá", "Nâng cao", "Học sinh giỏi"])
        
    with col2:
        st.write("--- Cấu trúc đề thi ---")
        num_mc = st.number_input("Số câu Trắc nghiệm (4 đáp án):", 0, 50, 10)
        num_tf = st.number_input("Số câu Đúng/Sai (Câu chùm):", 0, 20, 2, help="Dạng câu hỏi có 4 ý a,b,c,d để học sinh chọn Đ/S")
        num_tl = st.number_input("Số câu Tự luận:", 0, 10, 1)

    if st.button("🚀 BẮT ĐẦU SOẠN ĐỀ", type="primary", use_container_width=True):
        if num_mc == 0 and num_tf == 0 and num_tl == 0:
            st.warning("Vui lòng chọn số lượng ít nhất 1 loại câu hỏi.")
        else:
            # Xây dựng yêu cầu chi tiết
            structure_req = []
            if num_mc > 0: structure_req.append(f"- Phần 1: {num_mc} câu Trắc nghiệm khách quan (4 lựa chọn A,B,C,D).")
            if num_tf > 0: structure_req.append(f"- Phần 2: {num_tf} câu Trắc nghiệm Đúng/Sai (Mỗi câu có câu dẫn và 4 ý a,b,c,d).")
            if num_tl > 0: structure_req.append(f"- Phần 3: {num_tl} câu Tự luận (Yêu cầu giải quyết vấn đề/vận dụng).")
            
            str_req_text = "\n".join(structure_req)

            full_prompt = (
                f"Bạn là giáo viên dạy môn {subject} lớp {grade}. "
                f"Hãy soạn đề kiểm tra về chủ đề: '{topic}'. "
                f"Độ khó: {level}. \n"
                f"Cấu trúc đề yêu cầu:\n{str_req_text}\n"
                f"Yêu cầu chung: Ngôn ngữ phù hợp học sinh lớp {grade}. "
                f"Trình bày rõ ràng: ĐỀ BÀI RIÊNG và ĐÁP ÁN/HƯỚNG DẪN CHẤM CHI TIẾT RIÊNG ở cuối."
            )
            
            with st.spinner(f"Đang soạn đề đa dạng cấu trúc cho lớp {grade}..."):
                res = call_gemini_auto(full_prompt)
                st.session_state['res'] = res
                st.session_state['top'] = topic
                st.session_state['gr'] = grade
                
                if "⚠️" in res: st.error(res)
                else: st.success("Đã soạn xong!"); st.write(res)

# --- TAB 2: SOẠN TỪ FILE ---
with tab2:
    f = st.file_uploader("Tải lên tài liệu (PDF/Word):", type=['pdf','docx'])
    grade_file = st.selectbox("Dành cho lớp:", [str(i) for i in range(1, 13)], index=8, key='gr_file')
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: n_mc_f = st.number_input("SL Trắc nghiệm:", 0, 50, 10, key='f1')
    with col_f2: n_tf_f = st.number_input("SL Đúng/Sai:", 0, 20, 2, key='f2')
    with col_f3: n_tl_f = st.number_input("SL Tự luận:", 0, 10, 1, key='f3')

    if st.button("🚀 PHÂN TÍCH & TẠO ĐỀ", use_container_width=True):
        if f:
            with st.spinner("AI đang đọc tài liệu và soạn đề..."):
                content = read_file(f)
                if len(content) < 50: 
                    st.warning("File quá ngắn hoặc không đọc được.")
                else:
                    # Xây dựng yêu cầu cấu trúc cho file
                    req_list = []
                    if n_mc_f > 0: req_list.append(f"- {n_mc_f} câu Trắc nghiệm (4 đáp án).")
                    if n_tf_f > 0: req_list.append(f"- {n_tf_f} câu Trắc nghiệm Đúng/Sai (dạng chùm a,b,c,d).")
                    if n_tl_f > 0: req_list.append(f"- {n_tl_f} câu Tự luận.")
                    req_text = "\n".join(req_list)

                    prompt = (
                        f"Dựa vào nội dung văn bản sau: \n'{content[:15000]}'... \n"
                        f"Hãy đóng vai giáo viên lớp {grade_file}, soạn đề kiểm tra gồm:\n{req_text}\n"
                        f"Có đáp án và hướng dẫn chấm chi tiết ở cuối."
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
        
        docx = create_word(txt_edit, st.session_state['top'], st.session_state.get('gr', ''))
        st.download_button(
            label="📥 TẢI FILE WORD (.DOCX)", 
            data=docx, 
            file_name=f"De_Thi_{st.session_state['top']}.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
            use_container_width=True
        )
    else:
        st.write("👈 Chưa có dữ liệu.")
