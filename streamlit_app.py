import streamlit as st
import google.generativeai as genai
import time

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Trợ lý Sư phạm 4.0", page_icon="🎓", layout="wide")

# --- 2. GIAO DIỆN HEADER ---
st.title("🎓 HỆ THỐNG TRỢ LÝ ẢO SƯ PHẠM 4.0")
st.markdown("**Đơn vị:** Trường PTDTBT THCS Mùn Chung | **Tác giả:** Nhóm thầy Trần Hữu Đức")
st.markdown("---")

# --- 3. THANH CÔNG CỤ BÊN TRÁI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    st.header("⚙️ CẤU HÌNH")
    
    # Lấy API Key từ Secrets hoặc nhập tay
    api_key = None
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Đã kết nối Key hệ thống")
    else:
        api_key = st.text_input("Nhập API Key:", type="password")
    
    st.divider()
    
    menu = st.radio(
        "🎯 CHỌN CHỨC NĂNG:",
        ["1. Soạn đề Trắc nghiệm", 
         "2. Soạn đề Đúng/Sai (GDPT 2018)",
         "3. Soạn Tự luận + Barem",
         "4. Hỗ trợ Giáo dục hòa nhập"]
    )

# --- 4. HÀM KẾT NỐI AI (DÙNG GEMINI-PRO CHO ỔN ĐỊNH) ---
def get_ai_response(prompt):
    # Cấu hình AI
    genai.configure(api_key=api_key)
    
    # Dùng gemini-pro (Bản ổn định nhất, không bao giờ lỗi 404)
    model = genai.GenerativeModel('gemini-pro') 
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Lỗi kết nối: {e}"

# --- 5. XỬ LÝ CHỨC NĂNG ---
if not api_key:
    st.warning("👈 Vui lòng nhập API Key để bắt đầu!")
    st.stop()

# Xử lý nút bấm chung
def xu_ly_ai(prompt_text, button_text="🚀 THỰC HIỆN"):
    if st.button(button_text, type="primary"):
        if noi_dung or tu_khoa: # Kiểm tra xem đã nhập liệu chưa
            with st.spinner("AI đang suy nghĩ... (Mất khoảng 3-5 giây)"):
                ket_qua = get_ai_response(prompt_text)
                if "⚠️ Lỗi" in ket_qua:
                    st.error(ket_qua)
                else:
                    st.success("✅ Đã xong! Kết quả bên dưới:")
                    st.markdown(ket_qua)
        else:
            st.error("⚠️ Thầy cô chưa nhập nội dung!")

# === CHỨC NĂNG 1: TRẮC NGHIỆM ===
if "1." in menu:
    st.header("📝 1. SOẠN TRẮC NGHIỆM (4 ĐÁP ÁN)")
    col1, col2 = st.columns([1, 2])
    with col1:
        mon = st.text_input("Môn:", value="Lịch Sử 9")
        sl = st.number_input("Số câu:", value=5, min_value=1)
        do_kho = st.select_slider("Mức độ:", ["Nhận biết", "Thông hiểu", "Vận dụng"])
    with col2:
        noi_dung = st.text_area("Dán bài học:", height=150)
        tu_khoa = "dummy" # Biến giả để qua bước kiểm tra
    
    prompt = f"Đóng vai GV môn {mon}. Soạn {sl} câu trắc nghiệm khách quan ({do_kho}) từ văn bản: '{noi_dung}'. Yêu cầu: 4 đáp án A,B,C,D. Cuối mỗi câu có ĐÁP ÁN ĐÚNG và GIẢI THÍCH."
    xu_ly_ai(prompt)

# === CHỨC NĂNG 2: ĐÚNG/SAI ===
elif "2." in menu:
    st.header("✅ 2. SOẠN CÂU HỎI ĐÚNG/SAI")
    st.caption("Chuẩn GDPT 2018: Mỗi câu lớn có 4 ý nhỏ a/b/c/d")
    noi_dung = st.text_area("Dán bài học:", height=150)
    sl = st.number_input("Số câu lớn:", value=2, min_value=1)
    tu_khoa = "dummy"
    
    prompt = f"Dựa vào: '{noi_dung}'. Tạo {sl} câu hỏi dạng ĐÚNG/SAI chuẩn GDPT 2018 (Mỗi câu 4 ý a,b,c,d). Có đáp án và giải thích ngắn gọn."
    xu_ly_ai(prompt)

# === CHỨC NĂNG 3: TỰ LUẬN ===
elif "3." in menu:
    st.header("✍️ 3. SOẠN TỰ LUẬN + BAREM")
    noi_dung = st.text_area("Dán bài học:", height=150)
    tu_khoa = "dummy"
    
    prompt = f"Soạn câu hỏi Tự luận đánh giá năng lực từ: '{noi_dung}'. Yêu cầu QUAN TRỌNG: Kèm theo BAREM CHẤM ĐIỂM chi tiết (chia nhỏ 0.25đ, 0.5đ)."
    xu_ly_ai(prompt)

# === CHỨC NĂNG 4: HÒA NHẬP ===
elif "4." in menu:
    st.header("❤️ 4. HỖ TRỢ HỌC SINH DÂN TỘC")
    tu_khoa = st.text_input("Nhập từ khó (VD: RAM, Virus, Axit...):")
    noi_dung = "dummy"
    
    prompt = f"Giải thích '{tu_khoa}' cho học sinh dân tộc thiểu số. Dùng hình ảnh ví von nương rẫy, bản làng, con vật cho dễ hiểu."
    xu_ly_ai(prompt, button_text="🔍 GIẢI THÍCH")

st.markdown("---")
st.caption("© 2026 Bản quyền thuộc về Nhóm tác giả Trường PTDTBT THCS Mùn Chung")
