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
    
    # --- XỬ LÝ API KEY TỰ ĐỘNG (ƯU TIÊN LẤY TRONG SECRETS) ---
    api_key = None
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Đã kết nối Key hệ thống")
    else:
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
    
    st.info("💡 Hướng dẫn: \n1. Chọn chức năng.\n2. Nhập nội dung bài học.\n3. Bấm nút để AI làm việc.")

# --- 4. KẾT NỐI AI (CHỈ DÙNG BẢN FLASH - KHÔNG TỰ ĐỘNG NỮA) ---
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        # ÉP CỨNG DÙNG BẢN FLASH (Bản này quota cao nhất, khó bị lỗi)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.sidebar.error(f"Lỗi kết nối: {e}")
else:
    st.warning("👈 Vui lòng cấu hình API Key để sử dụng!")
    st.stop()

# --- 5. XỬ LÝ CÁC CHỨC NĂNG ---

# === CHỨC NĂNG 1: TRẮC NGHIỆM ===
if "1." in menu:
    st.header("📝 1. SOẠN ĐỀ TRẮC NGHIỆM")
    col1, col2 = st.columns([1, 2])
    with col1:
        mon_hoc = st.text_input("Môn học:", value="Lịch Sử 9")
        so_cau = st.number_input("Số câu hỏi:", min_value=1, value=5)
        do_kho = st.select_slider("Mức độ:", options=["Nhận biết", "Thông hiểu", "Vận dụng"])
    with col2:
        noi_dung = st.text_area("Dán nội dung bài học:", height=150, placeholder="Dán văn bản vào đây...")
    
    if st.button("🚀 SOẠN ĐỀ NGAY", type="primary"):
        if noi_dung:
            with st.spinner("Đang soạn đề..."):
                try:
                    prompt = f"Đóng vai GV môn {mon_hoc}. Soạn {so_cau} câu trắc nghiệm (Mức độ {do_kho}) từ: '{noi_dung}'. Yêu cầu: 4 đáp án A,B,C,D, có đáp án đúng và giải thích."
                    response = model.generate_content(prompt)
                    st.success("✅ Kết quả:")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        else:
            st.error("⚠️ Chưa có nội dung!")

# === CHỨC NĂNG 2: ĐÚNG / SAI ===
elif "2." in menu:
    st.header("✅ 2. SOẠN CÂU HỎI ĐÚNG/SAI")
    st.caption("Mỗi câu hỏi lớn gồm 4 ý nhỏ a, b, c, d.")
    noi_dung = st.text_area("Dán nội dung bài học:", height=150)
    so_cau = st.number_input("Số câu hỏi lớn:", min_value=1, value=2)
    
    if st.button("🚀 TẠO CÂU HỎI", type="primary"):
        if noi_dung:
            with st.spinner("Đang tư duy..."):
                try:
                    prompt = f"Dựa vào: '{noi_dung}'. Tạo {so_cau} câu hỏi dạng ĐÚNG/SAI chuẩn GDPT 2018 (Mỗi câu có 4 ý a,b,c,d). Có đáp án và giải thích."
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        else:
            st.error("⚠️ Chưa có nội dung!")

# === CHỨC NĂNG 3: TỰ LUẬN + BAREM ===
elif "3." in menu:
    st.header("✍️ 3. SOẠN TỰ LUẬN + BAREM")
    noi_dung = st.text_area("Dán nội dung bài học:", height=150)
    
    if st.button("🚀 SOẠN ĐỀ", type="primary"):
        if noi_dung:
            with st.spinner("Đang chấm điểm..."):
                try:
                    prompt = f"Soạn câu hỏi Tự luận từ: '{noi_dung}'. Yêu cầu: Kèm theo BAREM CHẤM ĐIỂM chi tiết (0.25đ, 0.5đ)."
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        else:
            st.error("⚠️ Chưa có nội dung!")

# === CHỨC NĂNG 4: HỖ TRỢ HÒA NHẬP ===
elif "4." in menu:
    st.header("❤️ 4. PHIÊN DỊCH NGÔN NGỮ BẢN LÀNG")
    col1, col2 = st.columns([1, 2])
    with col1:
        tu_khoa = st.text_input("Từ ngữ khó:", placeholder="VD: Hệ điều hành...")
    
    if st.button("🔍 GIẢI THÍCH", type="primary"):
        if tu_khoa:
            with st.spinner("Đang tìm ví dụ..."):
                try:
                    prompt = f"Giải thích '{tu_khoa}' cho học sinh dân tộc thiểu số. Dùng hình ảnh ví von với nương rẫy, bản làng dễ hiểu."
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Lỗi: {e}")

# --- CHÂN TRANG ---
st.markdown("---")
st.caption("© 2026 Bản quyền thuộc về Nhóm tác giả Trường PTDTBT THCS Mùn Chung")
