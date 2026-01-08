import streamlit as st
import google.generativeai as genai

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Trợ lý Sư phạm 4.0",
    page_icon="🎓",
    layout="wide"
)

# --- 2. GIAO DIỆN HEADER ---
st.title("🎓 HỆ THỐNG TRỢ LÝ ẢO SƯ PHẠM 4.0")
st.markdown("**Đơn vị:** Trường PTDTBT THCS Mùn Chung | **Tác giả:** Nhóm thầy Trần Hữu Đức")
st.markdown("---")

# --- 3. THANH CÔNG CỤ BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    st.header("⚙️ CẤU HÌNH")
    
    # Ô nhập Key (Để ẩn mật khẩu cho bảo mật)
    api_key = st.text_input("Nhập API Key Google:", type="password")
    
    st.divider()
    
    # Menu chọn chức năng
    menu = st.radio(
        "🎯 CHỌN CHỨC NĂNG:",
        ["1. Soạn đề Trắc nghiệm (4 đáp án)", 
         "2. Soạn đề Đúng/Sai (Mới 2018)",
         "3. Soạn Tự luận + Barem chấm",
         "4. Hỗ trợ Giáo dục hòa nhập"]
    )
    
    st.info("💡 Hướng dẫn: \n1. Nhập Key.\n2. Chọn chức năng.\n3. Nhập nội dung bài học.\n4. Bấm nút để AI làm việc.")

# --- 4. XỬ LÝ KẾT NỐI AI ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Sử dụng model Flash cho tốc độ nhanh nhất
        model = genai.GenerativeModel('gemini-2.0-pro')
    except:
        st.error("❌ Lỗi API Key! Vui lòng kiểm tra lại.")
        st.stop()
else:
    st.warning("👈 Thầy/Cô vui lòng nhập API Key ở cột bên trái để bắt đầu!")
    st.stop() # Dừng lại nếu chưa có Key

# --- 5. XỬ LÝ CÁC CHỨC NĂNG ---

# === CHỨC NĂNG 1: TRẮC NGHIỆM ===
if "1." in menu:
    st.header("📝 1. SOẠN ĐỀ TRẮC NGHIỆM (4 LỰA CHỌN)")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        mon_hoc = st.text_input("Môn học:", value="Lịch Sử 9")
        so_cau = st.number_input("Số câu hỏi:", min_value=1, value=5)
        do_kho = st.select_slider("Mức độ:", options=["Nhận biết", "Thông hiểu", "Vận dụng"])
    with col2:
        noi_dung = st.text_area("Dán nội dung bài học vào đây:", height=150, placeholder="Copy văn bản từ Word/PDF dán vào đây...")
    
    if st.button("🚀 SOẠN ĐỀ NGAY", type="primary"):
        if noi_dung:
            with st.spinner(f"AI đang soạn {so_cau} câu trắc nghiệm môn {mon_hoc}..."):
                try:
                    prompt = f"""
                    Đóng vai giáo viên môn {mon_hoc}. 
                    Soạn {so_cau} câu trắc nghiệm khách quan (Mức độ {do_kho}) từ văn bản: '{noi_dung}'.
                    Yêu cầu: 
                    - 4 đáp án A, B, C, D.
                    - Cuối mỗi câu có ĐÁP ÁN ĐÚNG và GIẢI THÍCH CHI TIẾT.
                    """
                    response = model.generate_content(prompt)
                    st.success("✅ Đã soạn xong! Thầy/cô có thể copy kết quả bên dưới:")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Có lỗi xảy ra: {e}")
        else:
            st.error("⚠️ Vui lòng dán nội dung bài học trước!")

# === CHỨC NĂNG 2: ĐÚNG / SAI ===
elif "2." in menu:
    st.header("✅ 2. SOẠN CÂU HỎI ĐÚNG/SAI (CHUẨN GDPT 2018)")
    st.caption("Dạng câu hỏi mới: Mỗi câu hỏi lớn gồm 4 ý nhỏ a, b, c, d.")
    
    noi_dung = st.text_area("Dán nội dung bài học:", height=150)
    so_cau = st.number_input("Số câu hỏi lớn:", min_value=1, value=2)
    
    if st.button("🚀 TẠO CÂU HỎI", type="primary"):
        if noi_dung:
            with st.spinner("Đang tư duy và thiết kế câu hỏi..."):
                prompt = f"""
                Dựa vào nội dung: '{noi_dung}'. 
                Tạo {so_cau} câu hỏi dạng ĐÚNG/SAI chuẩn GDPT 2018.
                Cấu trúc mỗi câu gồm 4 ý nhỏ (a,b,c,d). 
                Yêu cầu: Có đáp án (Đúng/Sai) và giải thích ngắn gọn cho từng ý.
                """
                response = model.generate_content(prompt)
                st.markdown(response.text)
        else:
            st.error("⚠️ Chưa có nội dung bài học!")

# === CHỨC NĂNG 3: TỰ LUẬN + BAREM ===
elif "3." in menu:
    st.header("✍️ 3. SOẠN TỰ LUẬN + BAREM CHẤM")
    noi_dung = st.text_area("Dán nội dung bài học:", height=150)
    
    if st.button("🚀 SOẠN ĐỀ & BAREM", type="primary"):
        if noi_dung:
            with st.spinner("Đang chia điểm chi tiết..."):
                prompt = f"""
                Soạn câu hỏi Tự luận đánh giá năng lực từ: '{noi_dung}'. 
                Yêu cầu QUAN TRỌNG: Kèm theo HƯỚNG DẪN CHẤM (BAREM) chi tiết, chia nhỏ điểm số (0.25đ, 0.5đ) cho từng ý trả lời.
                """
                response = model.generate_content(prompt)
                st.markdown(response.text)
        else:
            st.error("⚠️ Chưa có nội dung!")

# === CHỨC NĂNG 4: HỖ TRỢ HÒA NHẬP ===
elif "4." in menu:
    st.header("❤️ 4. PHIÊN DỊCH NGÔN NGỮ BẢN LÀNG")
    st.markdown("*Chức năng hỗ trợ học sinh dân tộc thiểu số tiếp cận kiến thức*")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        tu_khoa = st.text_input("Từ ngữ/Khái niệm khó hiểu:", placeholder="VD: Hệ điều hành, Virus...")
    
    if st.button("🔍 GIẢI THÍCH", type="primary"):
        if tu_khoa:
            with st.spinner("Đang tìm ví dụ nương rẫy..."):
                prompt = f"""
                Giải thích khái niệm '{tu_khoa}' cho học sinh dân tộc thiểu số vùng cao.
                Yêu cầu: Dùng hình ảnh ví von, so sánh với nương rẫy, bản làng, con trâu, con gà... để các em dễ hình dung nhất.
                Tránh dùng từ Hán Việt khó hiểu.
                """
                response = model.generate_content(prompt)
                st.info(response.text)
        else:
            st.error("⚠️ Hãy nhập từ cần giải thích!")

# --- CHÂN TRANG ---
st.markdown("---")
st.caption("© 2026 Bản quyền thuộc về Nhóm tác giả Trường PTDTBT THCS Mùn Chung")
