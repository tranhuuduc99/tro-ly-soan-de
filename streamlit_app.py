import streamlit as st
import requests
import json
import time
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import PyPDF2

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Soạn Đề Thông Minh", page_icon="📚", layout="wide")

# ==============================================================================
# ▼▼▼ KHU VỰC DÁN KEY CỦA BẠN (DÁN VÀO GIỮA HAI DẤU NGOẶC KÉP) ▼▼▼
# ==============================================================================

MY_API_KEY = "AIzaSyBY29kMfQWCB7ASsBrWcPHKn8EG8kYq_Bc" 

# ==============================================================================

# --- HÀM GỌI AI GEMINI (TỰ ĐỘNG SỬA LỖI 404) ---
def call_gemini(prompt):
    if "DÁN_MÃ_KEY" in MY_API_KEY or len(MY_API_KEY) < 30:
        return "⚠️ LỖI: Bạn chưa nhập API Key vào dòng 16 trong code!"

    # Danh sách các model để thử (Nếu cái đầu lỗi 404 thì tự thử cái sau)
    models_to_try = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro-latest"]
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    # Vòng lặp thử từng model
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={MY_API_KEY}"
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)
            
            # Nếu thành công (200) -> Trả về kết quả ngay
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # Nếu lỗi 404 (Sai tên model) -> Bỏ qua, thử model tiếp theo trong danh sách
            elif response.status_code == 404:
                continue 
            
            # Nếu lỗi khác (hết hạn mức, key sai) -> Báo lỗi ngay
            else:
                return f"❌ Lỗi (Code {response.status_code}): {response.text}"
                
        except Exception as e:
            continue # Lỗi mạng thì thử cái tiếp theo

    return "❌ Không tìm thấy model nào hoạt động với Key này. Hãy thử tạo Key mới."

# --- HÀM ĐỌC FILE TẢI LÊN ---
def read_uploaded_file(uploaded_file):
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
        return None
    return ""

# --- HÀM TẠO FILE WORD ĐẸP ---
def create_word_doc(content_text, topic_name, grade, subject):
    doc = Document()
    
    # 1. Header Sở/Trường
    section = doc.sections[0]
    header = section.header
    paragraph = header.paragraphs[0]
    paragraph.text = "SỞ GIÁO DỤC VÀ ĐÀO TẠO............\tĐỀ KIỂM TRA ĐÁNH GIÁ"
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 2. Tiêu đề chính
    heading = doc.add_heading(f'ĐỀ TÀI: {topic_name.upper()}', level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 3. Thông tin môn/lớp
    info = doc.add_paragraph(f"Môn: {subject} - Lớp: {grade}")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("-" * 70).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 4. Nội dung đề (Xử lý in đậm các phần)
    lines = content_text.split('\n')
    for line in lines:
        clean_line = line.strip()
        if clean_line:
            p = doc.add_paragraph()
            # In đậm các tiêu đề lớn
            if any(x in clean_line.upper() for x in ["PHẦN", "CÂU", "ĐÁP ÁN", "HƯỚNG DẪN"]):
                run = p.add_run(clean_line)
                run.bold = True
            else:
                p.add_run(clean_line)

    # 5. Lưu vào bộ nhớ đệm
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- GIAO DIỆN CHÍNH (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ CẤU HÌNH ĐỀ THI")
    st.divider()
    
    # Các lựa chọn
    subject = st.text_input("Môn học:", "Ngữ Văn")
    grade = st.selectbox("Khối lớp:", ["6", "7", "8", "9", "10", "11", "12"], index=3)
    difficulty = st.select_slider("Độ khó:", options=["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"], value="Thông hiểu")
    
    st.divider()
    st.subheader("📋 Cấu trúc đề:")
    col_a, col_b = st.columns(2)
    with col_a:
        num_mc = st.number_input("Trắc nghiệm (4 chọn 1):", min_value=0, value=10)
        num_tf = st.number_input("Đúng/Sai (Dạng chùm):", min_value=0, value=2)
    with col_b:
        num_essay = st.number_input("Câu Tự luận:", min_value=0, value=1)
        exam_time = st.number_input("Thời gian (phút):", min_value=15, value=45)

# --- GIAO DIỆN CHÍNH (MAIN) ---
st.title("🎓 TRỢ LÝ SOẠN ĐỀ THI 4.0")
st.markdown(f"**Trạng thái Key:** {'✅ Đã nhập' if 'AIza' in MY_API_KEY else '⚠️ Chưa nhập Key vào code!'}")

# Tabs chọn chế độ
tab_topic, tab_file = st.tabs(["📝 Soạn Từ Chủ Đề", "📂 Soạn Từ File Tài Liệu"])

# --- TAB 1: SOẠN TỪ CHỦ ĐỀ ---
with tab_topic:
    user_topic = st.text_area("Nhập tên bài học / chủ đề cần ra đề:", height=100, placeholder="Ví dụ: Tác phẩm Lặng lẽ Sa Pa, Bài thơ Đồng chí...")
    
    if st.button("🚀 KHỞI TẠO ĐỀ THI (THEO CHỦ ĐỀ)", type="primary"):
        if not user_topic:
            st.warning("Vui lòng nhập chủ đề!")
        else:
            # Tạo Prompt (Câu lệnh) chi tiết
            full_prompt = (
                f"Đóng vai giáo viên môn {subject} lớp {grade}. Hãy soạn đề kiểm tra {exam_time} phút.\n"
                f"Chủ đề: '{user_topic}'. Mức độ: {difficulty}.\n"
                f"Cấu trúc đề bắt buộc gồm:\n"
                f"1. PHẦN TRẮC NGHIỆM: {num_mc} câu (4 lựa chọn A,B,C,D).\n"
                f"2. PHẦN ĐÚNG/SAI: {num_tf} câu (Mỗi câu có 4 ý a,b,c,d).\n"
                f"3. PHẦN TỰ LUẬN: {num_essay} câu.\n"
                f"Yêu cầu đầu ra:\n"
                f"- Trình bày rõ ràng, có tiêu đề các phần.\n"
                f"- Cuối cùng phải có: ĐÁP ÁN CHI TIẾT VÀ THANG ĐIỂM.\n"
                f"- Không được viết lời chào, chỉ viết nội dung đề."
            )
            
            with st.spinner("🤖 AI đang tư duy và soạn đề..."):
                result = call_gemini(full_prompt)
                if "⚠️" in result or "❌" in result:
                    st.error(result)
                else:
                    st.success("Đã soạn thảo xong!")
                    st.session_state['exam_result'] = result
                    st.session_state['exam_source'] = user_topic

# --- TAB 2: SOẠN TỪ FILE ---
with tab_file:
    uploaded_file = st.file_uploader("Tải lên tài liệu tham khảo (PDF, Word):", type=['pdf', 'docx'])
    
    if st.button("🚀 PHÂN TÍCH TÀI LIỆU & RA ĐỀ"):
        if not uploaded_file:
            st.warning("Vui lòng chọn file!")
        else:
            file_text = read_uploaded_file(uploaded_file)
            if not file_text:
                st.error("Không đọc được nội dung file.")
            else:
                # Giới hạn ký tự để không bị quá tải
                input_text = file_text[:20000]
                
                full_prompt = (
                    f"Dựa vào nội dung văn bản sau đây:\n'''{input_text}'''\n\n"
                    f"Hãy đóng vai giáo viên môn {subject} lớp {grade}, soạn đề kiểm tra mức độ {difficulty}.\n"
                    f"Cấu trúc:\n"
                    f"- {num_mc} câu Trắc nghiệm.\n"
                    f"- {num_tf} câu Đúng/Sai.\n"
                    f"- {num_essay} câu Tự luận.\n"
                    f"Yêu cầu: Có đáp án chi tiết cuối đề."
                )
                
                with st.spinner("🤖 Đang đọc tài liệu và soạn đề..."):
                    result = call_gemini(full_prompt)
                    if "⚠️" in result or "❌" in result:
                        st.error(result)
                    else:
                        st.success("Đã soạn thảo xong từ file!")
                        st.session_state['exam_result'] = result
                        st.session_state['exam_source'] = uploaded_file.name

# --- KHU VỰC HIỂN THỊ VÀ TẢI VỀ ---
if 'exam_result' in st.session_state:
    st.divider()
    col_view, col_edit = st.columns([1, 1])
    
    with col_view:
        st.subheader("📄 Xem trước đề thi")
        st.markdown(st.session_state['exam_result'])
        
    with col_edit:
        st.subheader("📥 Tải về máy")
        final_content = st.text_area("Chỉnh sửa nhanh trước khi tải:", st.session_state['exam_result'], height=400)
        
        # Tạo file word
        doc_file = create_word_doc(final_content, st.session_state['exam_source'], grade, subject)
        
        st.download_button(
            label="BẤM ĐỂ TẢI FILE WORD (.DOCX)",
            data=doc_file,
            file_name=f"De_Kiem_Tra_{subject}_{grade}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
