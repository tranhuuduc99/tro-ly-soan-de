import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import PyPDF2
import random

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="AI Exam Pro", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="auto" # Tự động điều chỉnh theo thiết bị
)

# --- DANH SÁCH KEY API (Đã kiểm tra) ---
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# --- CSS TỐI ƯU GIAO DIỆN MOBILE ---
st.markdown("""
<style>
    /* Chỉnh màu tiêu đề */
    h1 {color: #0066cc;}
    /* Tăng kích thước chữ cho dễ đọc trên điện thoại */
    p {font-size: 16px;}
    /* Nút bấm nổi bật hơn */
    .stButton>button {
        font-weight: bold;
        border: 2px solid #0066cc;
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
    doc.add_heading(f'ĐỀ KIỂM TRA: {topic.upper()}', 0)
    doc.add_paragraph("Môn: ..................... Thời gian: ........... phút")
    doc.add_paragraph("-" * 50)
    doc.add_paragraph(content)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def get_gemini_response_smart(prompt, model_name="gemini-1.5-flash"):
    keys_to_try = API_KEYS # Thử tuần tự
    last_error = ""
    for i, key in enumerate(keys_to_try):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"temperature": 0.7, "max_output_tokens": 8192}
            )
            return model.generate_content(prompt).text
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "404" in last_error: continue 
            continue
    return f"⚠️ HỆ THỐNG ĐANG BẬN (Lỗi kết nối AI). Vui lòng thử lại sau 30s.\n(Chi tiết: {last_error})"

# --- GIAO DIỆN NGƯỜI DÙNG ---

# SIDEBAR (Dành cho cài đặt)
with st.sidebar:
    st.header("⚙️ Cấu hình")
    st.success(f"🟢 Hệ thống sẵn sàng ({len(API_KEYS)} cores)")
    model_option = st.selectbox("Mô hình AI:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    st.markdown("---")
    st.caption("Tips: Nếu dùng điện thoại, xoay ngang màn hình để xem bảng tốt hơn.")

# MAIN CONTENT
st.title("📝 AI Exam Creator")
st.markdown("**Công cụ trợ giảng thông minh 4.0 - Tạo đề thi trong 30 giây**")

# Hiển thị cảnh báo nhỏ cho người dùng Mobile để họ biết mở Sidebar
if st.session_state.get('first_visit', True):
    st.info("💡 **Mẹo:** Bấm vào dấu mũi tên `>` ở góc trên bên trái để mở menu Cấu hình.")
    st.session_state['first_visit'] = False

# TABS CHỨC NĂNG
tab1, tab2, tab3 = st.tabs(["⚡ Tạo Nhanh", "📂 Tải File", "💾 Tải Về"])

# TAB 1: TẠO TỪ CHỦ ĐỀ
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Nhập chủ đề/Bài học:", "Văn bản: Lão Hạc - Nam Cao")
        grade = st.selectbox("Khối lớp:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9", "THPT"])
    with col2:
        q_num = st.slider("Số câu:", 5, 50, 10)
        level = st.select_slider("Độ khó:", ["Nhận biết", "Thông hiểu", "Vận dụng"])

    # Nút bấm full width (use_container_width=True) để dễ bấm trên mobile
    if st.button("🚀 TẠO ĐỀ THI NGAY", type="primary", use_container_width=True):
        prompt = f"""
        Đóng vai giáo viên {grade}. Soạn đề trắc nghiệm chủ đề: "{topic}".
        - Số lượng: {q_num} câu.
        - Độ khó: {level}.
        - Yêu cầu: Có đáp án chi tiết cuối bài. Format rõ ràng.
        """
        with st.spinner("AI đang soạn đề..."):
            result = get_gemini_response_smart(prompt, model_option)
            st.session_state['result'] = result
            st.session_state['topic'] = topic
            
            if "HỆ THỐNG ĐANG BẬN" in result:
                st.error(result)
            else:
                st.success("✅ Đã tạo xong! Chuyển sang Tab 'Tải Về' để lấy file Word.")
                st.write(result)

# TAB 2: TẠO TỪ FILE
with tab2:
    uploaded_file = st.file_uploader("Tải lên tài liệu (PDF/Word):", type=['pdf', 'docx', 'txt'])
    if st.button("🚀 PHÂN TÍCH & TẠO ĐỀ", use_container_width=True):
        if uploaded_file:
            with st.spinner("Đang đọc tài liệu..."):
                if uploaded_file.name.endswith('.pdf'): content = read_pdf(uploaded_file)
                elif uploaded_file.name.endswith('.docx'): content = read_docx(uploaded_file)
                else: content = str(uploaded_file.read(), "utf-8")
                
                prompt_file = f"Dựa vào nội dung này: \n{content}\n. Hãy soạn 10 câu trắc nghiệm có đáp án."
                result_file = get_gemini_response_smart(prompt_file, model_option)
                st.session_state['result'] = result_file
                st.session_state['topic'] = uploaded_file.name
                st.success("✅ Xong! Chuyển sang Tab 'Tải Về' để xuất file.")
                st.write(result_file)
        else:
            st.warning("Vui lòng chọn file trước!")

# TAB 3: TẢI VỀ
with tab3:
    if 'result' in st.session_state:
        st.subheader("📄 Xem trước & Xuất file")
        final_text = st.text_area("", st.session_state['result'], height=300)
        
        docx_data = create_docx(final_text, st.session_state['topic'])
        
        st.download_button(
            label="📥 TẢI FILE WORD (.DOCX)",
            data=docx_data,
            file_name=f"De_Thi_{st.session_state['topic']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True # Nút tải to rõ
        )
    else:
        st.info("👈 Hãy tạo đề ở Tab 1 hoặc Tab 2 trước.")

st.markdown("---")
st.caption("Sản phẩm dự thi ứng dụng AI trong Giáo dục")
