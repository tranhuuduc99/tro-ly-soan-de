import streamlit as st
import requests
import json
import time

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Trợ lý Sư phạm 4.0", page_icon="🎓", layout="wide")

# --- 2. GIAO DIỆN HEADER ---
st.title("🎓 HỆ THỐNG TRỢ LÝ ẢO SƯ PHẠM 4.0")
st.markdown("**Đơn vị:** Trường PTDTBT THCS Mùn Chung | **Tác giả:** Nhóm thầy Trần Hữu Đức")
st.caption("Phiên bản: Tự động chuyển đổi Model (Auto-Switching)")
st.markdown("---")

# --- 3. CẤU HÌNH TỰ ĐỘNG (KHÔNG CẦN CHỈNH) ---
# Key của thầy đã được tích hợp sẵn
API_KEY = "AIzaSyB2CmDwKWc4hXAxF4LGjOFiLKVLg6QbH4U"

# Danh sách các Model sẽ tự động thử lần lượt nếu cái trước bị lỗi
DANH_SACH_MODEL = [
    "gemini-1.5-flash",          # Ưu tiên 1: Nhanh nhất
    "gemini-1.5-pro",            # Ưu tiên 2: Thông minh hơn
    "gemini-1.5-flash-latest",   # Ưu tiên 3: Bản cập nhật
    "gemini-1.0-pro",            # Ưu tiên 4: Bản cũ ổn định
    "gemini-pro"                 # Ưu tiên 5: Bản gốc
]

# --- 4. HÀM GỬI LỆNH THÔNG MINH (CORE AI) ---
def goi_ai_tu_dong(prompt):
    # Tạo vùng chứa thông báo trạng thái
    status_box = st.empty()
    
    # Vòng lặp thử từng model
    for model_name in DANH_SACH_MODEL:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            # Thông báo nhỏ cho người dùng biết đang làm gì
            status_box.caption(f"🔄 Đang thử kết nối với: {model_name}...")
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                # Thành công!
                status_box.success(f"✅ Đã kết nối thành công với: {model_name}")
                time.sleep(1) # Dừng 1 xíu cho người dùng kịp đọc
                status_box.empty() # Xóa thông báo đi cho gọn
                
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            
            elif response.status_code == 429:
                return "⚠️ Lỗi 429: Key hết hạn mức. Vui lòng đổi Key khác!"
            
            # Nếu lỗi 404 hoặc lỗi khác -> Không return, để vòng lặp chạy tiếp sang model sau
            print(f"Model {model_name} bị lỗi: {response.status_code}")
            
        except Exception as e:
            print(f"Lỗi mạng với {model_name}: {e}")
            continue

    # Nếu thử hết danh sách mà vẫn không được
    status_box.empty()
    return "⚠️ HỆ THỐNG QUÁ TẢI: Đã thử tất cả các phiên bản AI nhưng đều thất bại. Vui lòng thử lại sau 1 phút."

# --- 5. GIAO DIỆN VÀ CHỨC NĂNG ---

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    st.header("⚙️ MENU CHỨC NĂNG")
    
    menu = st.radio(
        "Chọn tác vụ:",
        ["1. Soạn Trắc nghiệm (4 đáp án)", 
         "2. Soạn Đúng/Sai (GDPT 2018)",
         "3. Soạn Tự luận + Barem",
         "4. Hỗ trợ Giáo dục hòa nhập"]
    )
    st.info(f"🔑 Key đang dùng: ...{API_KEY[-6:]}")

# Hàm xử lý chung cho nút bấm
def thuc_hien_lenh(prompt_input):
    if st.button("🚀 THỰC HIỆN NGAY", type="primary"):
        if noi_dung_input:
            with st.spinner("Hệ thống đang tự động tìm đường truyền tốt nhất..."):
                ket_qua = goi_ai_tu_dong(prompt_input)
                st.markdown("### 📄 KẾT QUẢ:")
                st.markdown(ket_qua)
        else:
            st.error("⚠️ Thầy cô chưa nhập nội dung!")

# === CHỨC NĂNG 1: TRẮC NGHIỆM ===
if "1." in menu:
    st.header("📝 1. SOẠN TRẮC NGHIỆM")
    col1, col2 = st.columns([1, 2])
    with col1:
        mon = st.text_input("Môn học:", value="Tin học 9")
        sl = st.number_input("Số câu:", value=5, min_value=1)
        do_kho = st.select_slider("Mức độ:", ["Nhận biết", "Thông hiểu", "Vận dụng"])
    with col2:
        noi_dung_input = st.text_area("Dán bài học vào đây:", height=150)
    
    prompt = f"Đóng vai GV bộ môn {mon}. Soạn {sl} câu trắc nghiệm khách quan mức độ {do_kho} dựa trên nội dung: '{noi_dung_input}'. Yêu cầu: 4 đáp án A,B,C,D. Có đáp án đúng và giải thích chi tiết."
    thuc_hien_lenh(prompt)

# === CHỨC NĂNG 2: ĐÚNG/SAI ===
elif "2." in menu:
    st.header("✅ 2. SOẠN CÂU HỎI ĐÚNG/SAI")
    noi_dung_input = st.text_area("Dán bài học vào đây:", height=150)
    sl = st.number_input("Số câu lớn:", value=2, min_value=1)
    
    prompt = f"Dựa vào văn bản: '{noi_dung_input}'. Hãy soạn {sl} câu hỏi dạng ĐÚNG/SAI theo chuẩn GDPT 2018. Mỗi câu hỏi lớn gồm 4 ý nhỏ a), b), c), d). Cung cấp đáp án và giải thích."
    thuc_hien_lenh(prompt)

# === CHỨC NĂNG 3: TỰ LUẬN ===
elif "3." in menu:
    st.header("✍️ 3. SOẠN TỰ LUẬN + BAREM")
    noi_dung_input = st.text_area("Dán bài học vào đây:", height=150)
    
    prompt = f"Soạn đề kiểm tra tự luận đánh giá năng lực từ nội dung: '{noi_dung_input}'. Yêu cầu QUAN TRỌNG: Phải có HƯỚNG DẪN CHẤM (BAREM) chi tiết, chia nhỏ điểm số (0.25đ, 0.5đ)."
    thuc_hien_lenh(prompt)

# === CHỨC NĂNG 4: HÒA NHẬP ===
elif "4." in menu:
    st.header("❤️ 4. HỖ TRỢ HÒA NHẬP")
    st.caption("Giải thích từ ngữ khó bằng hình ảnh nương rẫy, đời sống dân tộc.")
    col1, col2 = st.columns([1, 2])
    with col1:
        noi_dung_input = st.text_input("Nhập từ/khái niệm khó:", placeholder="VD: RAM, Hệ sinh thái...")
    
    prompt = f"Giải thích khái niệm '{noi_dung_input}' cho học sinh dân tộc thiểu số vùng cao. Yêu cầu: Dùng hình ảnh ví von, so sánh với nương rẫy, bản làng, con trâu, con gà... để các em dễ hiểu nhất."
    thuc_hien_lenh(prompt)

st.markdown("---")
st.caption("© 2026 Bản quyền thuộc về Nhóm tác giả Trường PTDTBT THCS Mùn Chung")
