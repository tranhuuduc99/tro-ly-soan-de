import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
from docx.enum.text import WD_ALIGN_PARAGRAPH
import PyPDF2
import random

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phần mềm Soạn đề Siêu Tốc (3 Key)", page_icon="🚀", layout="wide")

# --- CẤU HÌNH DANH SÁCH API KEY ---
# Đã tích hợp 3 Key mới của bạn vào đây
API_KEYS = [
    "AIzaSyDto59lBW1gswhSkZeokoBpC3nZn1LiXsU",  # Key 1
    "AIzaSyDl0g9kd5p7jRBkTU1WYx8x8VTBykvlWI0",  # Key 2
    "AIzaSyAdyIu_JyQX2lahQwbDW6ipK_nm_gWzddo"   # Key 3
]

# --- 1. HÀM TỰ ĐỘNG TÌM MODEL ---
def get_best_available_model(api_key):
    # Dùng Flash để phản hồi nhanh nhất cho tác vụ soạn đề
    return "gemini-1.5-flash"

# --- 2. HÀM GỌI API VỚI CƠ CHẾ ĐỔI KEY LIÊN TỤC ---
def call_gemini_auto(prompt):
    # Xáo trộn danh sách để tải đều lên 3 Key, không dồn hết vào Key 1
    valid_keys = API_KEYS.copy()
    random.shuffle(valid_keys)
    
    errors = []

    # Vòng lặp thử từng Key
    for i, key in enumerate(valid_keys):
        clean_key = key.strip()
        model = "gemini-1.5-flash"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={clean_key}"
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
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=25)
            
            if response.status_code == 200:
                # ✅ THÀNH CÔNG -> Trả về kết quả ngay
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            
            elif response.status_code == 429:
                # ⚠️ Key này đang bận -> Ghi nhận và thử Key tiếp theo ngay lập tức
                errors.append(f"Key đuôi ...{clean_key[-4:]} bận")
                continue 
            
            else:
                errors.append(f"Lỗi {response.status_code}")
                continue

        except Exception as e:
            errors.append("Lỗi mạng")
            continue

    # Nếu thử cả 3 Key đều thất bại (rất hiếm khi xảy ra)
    return f"❌ TẤT CẢ HỆ THỐNG ĐANG BẬN. Vui lòng đợi 30 giây rồi thử lại.\n(Chi tiết: {'; '.join(errors)})"

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
    # Định dạng tiêu đề
    h = doc.add_heading('TRƯỜNG PTDTBT THCS MÙN CHUNG', 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
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
st.markdown("<h1 style='text-align: center; color: #004d99;'>🚀 PHẦN MỀM SOẠN ĐỀ (3 LUỒNG TỐC ĐỘ CAO)</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.success(f"✅ Đã nạp thành công {len(API_KEYS)} API Key")
    st.info("Hệ thống sẽ tự động chuyển Key nếu gặp lỗi quá tải.")

# Tabs chức năng
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
        num_tf = st.number_input("Số câu Đúng/Sai (Câu chùm):", 0, 20, 2)
        num_tl = st.number_input("Số câu Tự luận:", 0, 10, 1)

    if st.button("🚀 BẮT ĐẦU SOẠN ĐỀ", type="primary", use_container_width=True):
        if num_mc == 0 and num_tf == 0 and num_tl == 0:
            st.warning("Vui lòng chọn số lượng câu hỏi!")
        else:
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
            
            with st.spinner(f"Đang xử lý đa luồng..."):
                res = call_gemini_auto(full_prompt)
                st.session_state['res'] = res
                st.session_state['top'] = topic
                st.session_state['gr'] = grade
                
                if "❌" in res: st.error(res)
                else: st.success("Thành công! Tốc độ phản hồi cực nhanh."); st.write(res)

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
            with st.spinner("Đang đọc tài liệu và phân tích..."):
                content = read_file(f)
                if len(content) < 50: 
                    st.warning("File không đọc được hoặc quá ngắn.")
                else:
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
                    
                    if "❌" in res: st.error(res)
                    else: st.success("Thành công!"); st.write(res)

# --- TAB 3: TẢI VỀ ---
with tab3:
    if 'res' in st.session_state:
        st.info("Kiểm tra nội dung trước khi tải về:")
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
