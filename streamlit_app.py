import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import PyPDF2
import random

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Trợ Lý Soạn Đề", # Tên hiển thị trên tab trình duyệt
    page_icon="🏫", 
    layout="wide",
    initial_sidebar_state="auto"
)

# --- DANH SÁCH KEY API ---
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# --- CSS TỐI ƯU ---
st.markdown("""
<style>
    /* Màu xanh giáo dục chủ đạo */
    h1 {color: #004d99;}
    p {font-size: 16px;}
    .stButton>button {
        font-weight: bold;
        border: 2px solid #004d99;
        color: #004d99;
    }
    .stButton>button:hover {
        background-color: #004d99;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- CÁC HÀM XỬ LÝ (GIỮ NGUYÊN) ---
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def create_docx(content, topic):
    doc = Document()
    doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0) # Tiêu đề trong file Word
    doc.add_paragraph(f'ĐỀ KIỂM TRA CHỦ ĐỀ: {topic.upper()}')
    doc.add_paragraph("Họ và tên: ................................................. Lớp: ............")
    doc.add_paragraph("-" * 60)
    doc.add_paragraph(content)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def get_gemini_response_smart(prompt):
    # Sử dụng model Flash cho nhanh và ổn định
    MODEL_NAME = "gemini-1.5-flash" 
    
    keys_to_try = API_KEYS 
    last_error = ""
    
    for i, key in enumerate(keys_to_try):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config={"temperature": 0.7, "max_output_tokens": 8192}
            )
            return model.generate_content(prompt).text
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "404" in last_error: continue 
            continue
            
    return f"⚠️ Đang nghẽn mạng AI. Vui lòng thử lại sau 10s.\n(Lỗi: {last_error})"

# --- GIAO DIỆN CHÍNH ---

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Cấu hình hệ thống")
    st.success(f"🟢 Trạng thái: Sẵn sàng")
    st.info("🏫 Đơn vị: Trường PTDTBT THCS Mùn Chung")
    st.caption("Phiên bản v2.0 - Tối ưu hóa cho giáo viên.")

# HEADER
st.title("🏫 HỆ THỐNG HỖ TRỢ RA ĐỀ THI")
st.markdown("**Công cụ soạn thảo đề kiểm tra tự động dành cho Giáo viên**")

# Hướng dẫn nhỏ cho Mobile
if st.session_state.get('first_visit', True):
    st.info("💡 Thầy/Cô bấm vào dấu mũi tên `>` ở góc trái trên cùng để mở menu cài đặt.")
    st.session_state['first_visit'] = False

# TABS CHỨC NĂNG
tab1, tab2, tab3 = st.tabs(["⚡ Soạn nhanh theo chủ đề", "📂 Soạn từ file tài liệu", "📥 Tải đề về máy"])

# TAB 1: SOẠN NHANH
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Nhập bài học/chủ đề:", "Văn bản: Lão Hạc - Nam Cao")
        grade = st.selectbox("Khối lớp:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"])
    with col2:
        q_num = st.slider("Số lượng câu hỏi:", 5, 40, 10)
        level = st.select_slider("Mức độ khó:", ["Nhận biết", "Thông hiểu", "Vận dụng"])

    if st.button("🚀 BẮT ĐẦU SOẠN ĐỀ", type="primary", use_container_width=True):
        prompt = f"""
        Đóng vai giáo viên {grade}. Soạn đề trắc nghiệm chủ đề: "{topic}".
        - Số lượng: {q_num} câu.
        - Độ khó: {level}.
        - Yêu cầu: Có đáp án chi tiết cuối bài. Ngôn ngữ chuẩn sư phạm Việt Nam.
        """
        with st.spinner("Hệ thống đang phân tích và soạn câu hỏi..."):
            result = get_gemini_response_smart(prompt)
            st.session_state['result'] = result
            st.session_state['topic'] = topic
            
            if "Lỗi" in result:
                st.error(result)
            else:
                st.success("✅ Đã soạn xong! Mời Thầy/Cô qua tab 'Tải đề về máy' để xem và in.")
                st.write(result)

# TAB 2: SOẠN TỪ FILE
with tab2:
    st.write("Tải lên giáo trình, tài liệu tham khảo (PDF/Word):")
    uploaded_file = st.file_uploader("", type=['pdf', 'docx', 'txt'])
    
    if st.button("🚀 PHÂN TÍCH TÀI LIỆU & SOẠN ĐỀ", use_container_width=True):
        if uploaded_file:
            with st.spinner("Đang đọc nội dung tài liệu..."):
                if uploaded_file.name.endswith('.pdf'): content = read_pdf(uploaded_file)
                elif uploaded_file.name.endswith('.docx'): content = read_docx(uploaded_file)
                else: content = str(uploaded_file.read(), "utf-8")
                
                prompt_file = f"Dựa vào nội dung văn bản sau: \n{content}\n. Hãy soạn 10 câu trắc nghiệm có đáp án."
                result_file = get_gemini_response_smart(prompt_file)
                st.session_state['result'] = result_file
                st.session_state['topic'] = uploaded_file.name
                st.success("✅ Đã xử lý xong tài liệu! Mời Thầy/Cô qua tab 'Tải đề về máy'.")
                st.write(result_file)
        else:
            st.warning("Vui lòng chọn file tài liệu trước!")

# TAB 3: TẢI VỀ
with tab3:
    if 'result' in st.session_state:
        st.subheader("📄 Xem trước & Xuất file Word")
        final_text = st.text_area("", st.session_state['result'], height=300)
        
        docx_data = create_docx(final_text, st.session_state['topic'])
        
        st.download_button(
            label="📥 TẢI FILE WORD (.DOCX)",
            data=docx_data,
            file_name=f"De_Thi_{st.session_state['topic']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        st.info("👈 Thầy/Cô vui lòng tạo đề ở Tab 1 hoặc Tab 2 trước.")

# FOOTER BẢN QUYỀN
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: grey;'>
        © 2024 Bản quyền thuộc về trường <b>PTDTBT THCS Mùn Chung</b><br>
        <i>Ứng dụng được xây dựng phục vụ đổi mới sáng tạo trong dạy và học</i>
    </div>
    """, 
    unsafe_allow_html=True
)
