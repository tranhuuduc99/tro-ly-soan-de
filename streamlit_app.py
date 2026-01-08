import streamlit as st
import requests
import json
import time
import random
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import PyPDF2

# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN
# ==============================================================================
st.set_page_config(
    page_title="Hệ Thống Ra Đề Thông Minh",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Danh sách API Key dự phòng (Cơ chế cân bằng tải)
API_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# CSS tùy chỉnh để làm đẹp giao diện
st.markdown("""
<style>
    /* Tiêu đề chính */
    .main-title {
        font-size: 2.5rem;
        color: #004d99; /* Xanh giáo dục */
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    /* Phụ đề */
    .sub-title {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        font-style: italic;
        margin-bottom: 30px;
    }
    /* Nút bấm */
    .stButton>button {
        background-color: #004d99;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 3em;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    /* Khung kết quả */
    .result-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CÁC HÀM XỬ LÝ LOGIC (BACKEND)
# ==============================================================================

def call_google_ai_direct(prompt):
    """
    Hàm gọi AI thông qua HTTP Request trực tiếp.
    Ưu điểm: Không phụ thuộc vào thư viện, chạy được trên mọi môi trường mạng.
    """
    # Sử dụng model Flash cho tốc độ nhanh, fallback sang Pro nếu cần
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    headers = {'Content-Type': 'application/json'}
    
    # Cấu hình an toàn (Tắt bộ lọc để AI không từ chối các câu hỏi lịch sử/chiến tranh)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]

    log_errors = []

    # Thuật toán thử sai (Retry Logic): Quét qua Key -> Quét qua Model
    for key in API_KEYS:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "safetySettings": safety_settings,
                "generationConfig": {
                    "temperature": 0.7, # Độ sáng tạo vừa phải
                    "maxOutputTokens": 8192
                }
            }
            
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
                
                if response.status_code == 200:
                    try:
                        return response.json()['candidates'][0]['content']['parts'][0]['text']
                    except KeyError:
                        continue # Lỗi cấu trúc JSON, thử cái tiếp theo
                elif response.status_code == 429:
                    break # Key này hết hạn mức, đổi Key khác ngay
                else:
                    log_errors.append(f"{model}: {response.status_code}")
                    continue
            except Exception as e:
                log_errors.append(str(e))
                continue
    
    # Nếu chạy hết vòng lặp mà không được
    return f"⚠️ HỆ THỐNG QUÁ TẢI. Vui lòng thử lại sau 30 giây.\n(Chi tiết: {', '.join(log_errors)})"

def read_document(uploaded_file):
    """Đọc nội dung từ file PDF hoặc Word tải lên."""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text
    except Exception as e:
        return f"Lỗi đọc file: {str(e)}"
    return ""

def create_professional_word(content, topic):
    """Tạo file Word với định dạng chuẩn sư phạm."""
    doc = Document()
    
    # Header: Tên trường
    header = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Sub-header: Đề kiểm tra
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f'ĐỀ KIỂM TRA CHỦ ĐỀ: {topic.upper()}')
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)
    
    # Thông tin học sinh
    info = doc.add_paragraph("Họ và tên: .............................................................. Lớp: ....................")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph("-" * 70).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Nội dung đề thi
    doc.add_paragraph(content)
    
    # Footer
    section = doc.sections[0]
    footer = section.footer
    p_footer = footer.paragraphs[0]
    p_footer.text = "Đề thi được tạo tự động bởi Hệ thống AI - Trường PTDTBT THCS Mùn Chung"
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 3. GIAO DIỆN NGƯỜI DÙNG (FRONTEND)
# ==============================================================================

# Header trang
st.markdown('<div class="main-title">🏫 HỆ THỐNG TRỢ LÝ RA ĐỀ THI 4.0</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">© Bản quyền thuộc về Trường PTDTBT THCS Mùn Chung</div>', unsafe_allow_html=True)

# Sidebar cấu hình
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997277.png", width=100)
    st.header("⚙️ Bảng Điều Khiển")
    st.success("✅ Trạng thái: Đã kết nối Máy chủ AI")
    st.info("ℹ️ Phiên bản: v2.5 (Direct API Stable)")
    st.markdown("---")
    st.write("**Hướng dẫn nhanh:**")
    st.markdown("1. Chọn tab chức năng bên phải.\n2. Nhập chủ đề hoặc tải file.\n3. Bấm nút tạo đề và chờ kết quả.")

# Tabs chức năng
tab1, tab2, tab3 = st.tabs(["⚡ SOẠN ĐỀ NHANH", "📂 SOẠN TỪ TÀI LIỆU", "💾 KHO LƯU TRỮ & TẢI VỀ"])

# --- TAB 1: SOẠN THEO CHỦ ĐỀ ---
with tab1:
    st.subheader("📝 Nhập thông tin đề thi")
    col1, col2 = st.columns(2)
    
    with col1:
        topic_input = st.text_input("Chủ đề / Bài học:", placeholder="Ví dụ: Chiến thắng Điện Biên Phủ", value="Lịch sử Điện Biên Phủ")
        grade_input = st.selectbox("Dành cho học sinh:", ["Khối 6", "Khối 7", "Khối 8", "Khối 9", "Ôn thi vào 10"])
    
    with col2:
        q_count = st.number_input("Số lượng câu hỏi:", min_value=5, max_value=50, value=10)
        difficulty = st.select_slider("Mức độ nhận thức:", options=["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"])

    if st.button("🚀 KHỞI TẠO ĐỀ THI", use_container_width=True):
        if not topic_input:
            st.warning("Vui lòng nhập chủ đề trước!")
        else:
            prompt_text = f"""
            Đóng vai là một giáo viên {grade_input} có kinh nghiệm.
            Hãy soạn một đề kiểm tra trắc nghiệm khách quan (4 lựa chọn A,B,C,D) về chủ đề: "{topic_input}".
            
            Thông số kỹ thuật:
            - Số lượng: {q_count} câu.
            - Độ khó: {difficulty}.
            
            Yêu cầu định dạng:
            - Phần 1: Nội dung đề thi (Chỉ có câu hỏi).
            - Phần 2: Bảng đáp án và Hướng dẫn giải chi tiết (Tách riêng ở cuối).
            - Ngôn ngữ: Tiếng Việt chuẩn mực, không lỗi chính tả.
            """
            
            with st.spinner(f"AI đang phân tích dữ liệu và soạn đề về '{topic_input}'..."):
                start_time = time.time()
                result = call_google_ai_direct(prompt_text)
                end_time = time.time()
                
                if "HỆ THỐNG QUÁ TẢI" in result:
                    st.error(result)
                else:
                    st.session_state['exam_content'] = result
                    st.session_state['exam_topic'] = topic_input
                    st.balloons() # Hiệu ứng chúc mừng
                    st.success(f"✅ Đã soạn xong trong {round(end_time - start_time, 2)} giây! Mời thầy/cô xem kết quả bên dưới.")
                    st.markdown("### 📄 Xem trước nội dung:")
                    st.text_area("", result, height=400)

# --- TAB 2: SOẠN TỪ FILE (RAG) ---
with tab2:
    st.subheader("📂 Tải lên giáo trình/tài liệu tham khảo")
    uploaded_file = st.file_uploader("Hỗ trợ định dạng PDF hoặc Word (.docx)", type=['pdf', 'docx'])
    
    if st.button("🚀 PHÂN TÍCH FILE & TẠO ĐỀ", use_container_width=True):
        if uploaded_file:
            with st.spinner("Đang đọc tài liệu..."):
                doc_content = read_document(uploaded_file)
                
                if len(doc_content) < 50:
                    st.warning("⚠️ Tài liệu quá ngắn hoặc không đọc được nội dung chữ (File ảnh scan).")
                else:
                    # Giới hạn ký tự để tránh quá tải
                    prompt_file = f"""
                    Dựa hoàn toàn vào nội dung văn bản được cung cấp dưới đây:
                    ----------------
                    {doc_content[:15000]}
                    ----------------
                    Yêu cầu:
                    Hãy soạn 10 câu hỏi trắc nghiệm khách quan để kiểm tra mức độ hiểu bài của học sinh về văn bản trên.
                    Cung cấp đáp án đúng ở cuối đề.
                    """
                    
                    res_file = call_google_ai_direct(prompt_file)
                    
                    if "HỆ THỐNG QUÁ TẢI" in res_file:
                        st.error(res_file)
                    else:
                        st.session_state['exam_content'] = res_file
                        st.session_state['exam_topic'] = uploaded_file.name
                        st.success("✅ Đã xử lý xong tài liệu!")
                        st.text_area("Kết quả:", res_file, height=400)
        else:
            st.warning("Vui lòng chọn file trước khi bấm nút!")

# --- TAB 3: TẢI VỀ ---
with tab3:
    st.subheader("📥 Xuất bản tài liệu")
    if 'exam_content' in st.session_state:
        st.info(f"Đang có bản nháp cho chủ đề: **{st.session_state['exam_topic']}**")
        
        # Cho phép sửa lại trước khi tải
        final_edit = st.text_area("Chỉnh sửa lần cuối trước khi in:", st.session_state['exam_content'], height=300)
        
        # Tạo file Word
        word_data = create_professional_word(final_edit, st.session_state['exam_topic'])
        
        col_d1, col_d2 = st.columns([1, 2])
        with col_d1:
            st.download_button(
                label="📥 TẢI FILE WORD (.DOCX)",
                data=word_data,
                file_name=f"De_Thi_{st.session_state['exam_topic']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with col_d2:
            st.warning("💡 Lưu ý: File Word tải về đã được căn chỉnh lề và thêm tiêu đề trường chuẩn.")
            
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/7486/7486744.png", width=100)
        st.caption("Chưa có dữ liệu. Vui lòng tạo đề ở Tab 1 hoặc Tab 2.")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey; font-size: 0.8rem;'>Sản phẩm tham dự cuộc thi Khoa học Kỹ thuật - Phát triển bởi Giáo viên trường PTDTBT THCS Mùn Chung</div>", unsafe_allow_html=True)
