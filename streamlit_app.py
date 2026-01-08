import streamlit as st
import requests
import json

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Trợ lý Sư phạm 4.0", page_icon="🎓", layout="wide")

# --- 2. GIAO DIỆN HEADER ---
st.title("🎓 HỆ THỐNG TRỢ LÝ ẢO SƯ PHẠM 4.0")
st.markdown("**Đơn vị:** Trường PTDTBT THCS Mùn Chung | **Tác giả:** Nhóm thầy Trần Hữu Đức")
st.caption("Phiên bản: Key tích hợp sẵn - Kết nối trực tiếp")
st.markdown("---")

# --- 3. THANH CÔNG CỤ BÊN TRÁI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    st.header("⚙️ CẤU HÌNH")
    
    # === CẬP NHẬT KEY MỚI TẠI ĐÂY ===
    # Tôi đã điền sẵn Key của thầy vào đây luôn cho tiện
    api_key = "AIzaSyB2CmDwKWc4hXAxF4LGjOFiLKVLg6QbH4U"
    
    st.success(f"✅ Đã tích hợp Key: ...{api_key[-6:]}")
    
    st.divider()

    # Menu chọn Model (Dự phòng khi Google đổi tên)
    chon_model = st.selectbox(
        "🤖 CHỌN PHIÊN BẢN AI:",
        ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"],
        index=0,
        help="Nếu báo lỗi 404, hãy đổi sang model khác trong danh sách này."
    )
    
    st.divider()
    
    menu = st.radio(
        "🎯 CHỌN CHỨC NĂNG:",
        ["1. Soạn đề Trắc nghiệm", 
         "2. Soạn đề Đúng/Sai (GDPT 2018)",
         "3. Soạn Tự luận + Barem",
         "4. Hỗ trợ Giáo dục hòa nhập"]
    )

# --- 4. HÀM KẾT NỐI TRỰC TIẾP (DIRECT API CALL) ---
def call_google_api(key, model_name, prompt):
    # Đường dẫn API trực tiếp
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Xử lý các mã lỗi phổ biến
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except:
                return "⚠️ AI trả lời rỗng (Vui lòng thử lại)."
        elif response.status_code == 404:
            return f"⚠️ Lỗi 404: Model '{model_name}' không khả dụng. 👉 Thầy hãy chọn model khác ở cột bên trái!"
        elif response.status_code == 429:
            return "⚠️ Lỗi 429: Key này đã hết lượt dùng miễn phí. Vui lòng đổi Key khác."
        elif response.status_code == 400:
            return f"⚠️ Lỗi 400: Yêu cầu không hợp lệ. ({response.text})"
        else:
            return f"⚠️ Lỗi Google (Mã {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"⚠️ Lỗi kết nối mạng: {e}"

# --- 5. XỬ LÝ CHỨC NĂNG ---

def xu_ly_ai(prompt_text, button_text="🚀 THỰC HIỆN"):
    if st.button(button_text, type="primary"):
        if noi_dung or tu_khoa:
            with st.spinner(f"Đang gửi lệnh tới {chon_model}..."):
                # Gọi hàm xử lý
                ket_qua = call_google_api(api_key, chon_model, prompt_text)
                
                if "⚠️" in ket_qua:
                    st.error(ket_qua)
                else:
                    st.success("✅ Đã xong! Kết quả bên dưới:")
                    st.markdown(ket_qua)
        else:
            st.error("⚠️ Chưa nhập nội dung!")

# === CHỨC NĂNG 1: TRẮC NGHIỆM ===
if "1." in menu:
    st.header("📝 1. SOẠN TRẮC NGHIỆM")
    col1, col2 = st.columns([1, 2])
    with col1:
        mon = st.text_input("Môn:", value="Lịch Sử 9")
        sl = st.number_input("Số câu:", value=5, min_value=1)
        do_kho = st.select_slider("Mức độ:", ["Nhận biết", "Thông hiểu", "Vận dụng"])
    with col2:
        noi_dung = st.text_area("Dán bài học:", height=150)
        tu_khoa = "dummy"
    
    prompt = f"Đóng vai GV môn {mon}. Soạn {sl} câu trắc nghiệm khách quan ({do_kho}) từ văn bản: '{noi_dung}'. Yêu cầu: 4 đáp án A,B,C,D. Cuối mỗi câu có ĐÁP ÁN ĐÚNG và GIẢI THÍCH."
    xu_ly_ai(prompt)

# === CHỨC NĂNG 2: ĐÚNG/SAI ===
elif "2." in menu:
    st.header("✅ 2. SOẠN CÂU HỎI ĐÚNG/SAI")
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
