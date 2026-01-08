import streamlit as st
import requests
import json
import time

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Trợ lý Sư phạm 4.0", page_icon="🎓", layout="wide")

# --- 2. GIAO DIỆN HEADER ---
st.title("🎓 HỆ THỐNG TRỢ LÝ ẢO SƯ PHẠM 4.0")
st.markdown("**Đơn vị:** Trường PTDTBT THCS Mùn Chung | **Tác giả:** Nhóm thầy Trần Hữu Đức")
st.caption("Phiên bản: Siêu bền bỉ (3 Key dự phòng)")
st.markdown("---")

# =========================================================
# ⚡ KHU VỰC CẤU HÌNH KEY (ĐÃ CẬP NHẬT 3 KEY MỚI) ⚡
# =========================================================
DANH_SACH_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",  # Key 1
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",  # Key 2
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"   # Key 3
]
# =========================================================

# --- 3. HÀM GỬI LỆNH THÔNG MINH (TỰ ĐỔI KEY KHI LỖI) ---
def goi_ai_sieu_ben(prompt):
    status_box = st.empty() # Hộp thông báo trạng thái
    
    # Chiến thuật: Thử từng chìa khóa một
    for index, current_key in enumerate(DANH_SACH_KEYS):
        # Thử kết nối với Key hiện tại
        model = "gemini-1.5-flash" # Dùng bản Flash cho nhanh nhất
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            # Gửi lệnh
            response = requests.post(url, headers=headers, json=data)
            
            # 1. Trường hợp THÀNH CÔNG (200)
            if response.status_code == 200:
                result = response.json()
                try:
                    text_tra_ve = result['candidates'][0]['content']['parts'][0]['text']
                    status_box.empty() # Xóa thông báo
                    return text_tra_ve
                except:
                    continue # Lỗi cấu trúc thì thử key khác
            
            # 2. Trường hợp QUÁ TẢI (429) -> Tự động đổi sang Key tiếp theo
            elif response.status_code == 429:
                print(f"Key số {index+1} bị quá tải. Đang chuyển sang Key tiếp theo...")
                continue 
            
            # 3. Trường hợp Lỗi Model (404) -> Thử đổi sang Model Pro với cùng Key này
            elif response.status_code == 404:
                url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={current_key}"
                response_pro = requests.post(url_pro, headers=headers, json=data)
                if response_pro.status_code == 200:
                    return response_pro.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    continue

        except Exception as e:
            print(f"Lỗi mạng: {e}")
            continue

    # Nếu chạy hết 3 Key mà vẫn không được
    return "⛔ SỰ CỐ MẠNG: Đã thử tất cả các kênh kết nối nhưng thất bại. Vui lòng kiểm tra lại Wifi hoặc chờ 1 phút."

# --- 4. GIAO DIỆN CỘT TRÁI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    st.header("⚙️ CHỨC NĂNG")
    
    # Hiển thị trạng thái hệ thống
    st.success(f"✅ Hệ thống sẵn sàng!\n(Đã nạp {len(DANH_SACH_KEYS)} nguồn năng lượng)")
    
    st.divider()
    
    menu = st.radio(
        "🎯 LỰA CHỌN:",
        ["1. Soạn Trắc nghiệm", 
         "2. Soạn Đúng/Sai (Mới)",
         "3. Soạn Tự luận + Barem",
         "4. Hỗ trợ Giáo dục hòa nhập"]
    )

# --- 5. HÀM XỬ LÝ CHUNG ---
def thuc_hien(prompt_input):
    if st.button("🚀 THỰC HIỆN NGAY", type="primary"):
        if noi_dung_input:
            with st.spinner("Trợ lý ảo đang làm việc..."):
                ket_qua = goi_ai_sieu_ben(prompt_input)
                
                if "⛔" in ket_qua:
                    st.error(ket_qua)
                else:
                    st.success("✅ Kết quả chi tiết:")
                    st.markdown(ket_qua)
        else:
            st.error("⚠️ Thầy cô chưa nhập nội dung!")

# === CHỨC NĂNG 1 ===
if "1." in menu:
    st.header("📝 1. SOẠN TRẮC NGHIỆM")
    col1, col2 = st.columns([1, 2])
    with col1:
        mon = st.text_input("Môn:", value="Tin học 9")
        sl = st.number_input("Số câu:", value=5)
        do_kho = st.select_slider("Mức độ:", ["Nhận biết", "Thông hiểu", "Vận dụng"])
    with col2:
        noi_dung_input = st.text_area("Dán bài học:", height=150)
    
    prompt = f"Đóng vai GV môn {mon}. Soạn {sl} câu trắc nghiệm ({do_kho}) từ: '{noi_dung_input}'. Yêu cầu: 4 đáp án A,B,C,D. Có đáp án và giải thích."
    thuc_hien(prompt)

# === CHỨC NĂNG 2 ===
elif "2." in menu:
    st.header("✅ 2. SOẠN ĐÚNG/SAI")
    st.caption("Chuẩn GDPT 2018: Mỗi câu lớn có 4 ý nhỏ")
    noi_dung_input = st.text_area("Dán bài học:", height=150)
    sl = st.number_input("Số câu lớn:", value=2)
    prompt = f"Dựa vào: '{noi_dung_input}'. Soạn {sl} câu hỏi ĐÚNG/SAI chuẩn GDPT 2018 (Mỗi câu 4 ý a,b,c,d). Có đáp án."
    thuc_hien(prompt)

# === CHỨC NĂNG 3 ===
elif "3." in menu:
    st.header("✍️ 3. TỰ LUẬN + BAREM")
    noi_dung_input = st.text_area("Dán bài học:", height=150)
    prompt = f"Soạn câu hỏi Tự luận từ: '{noi_dung_input}'. Yêu cầu: Kèm BAREM CHẤM ĐIỂM chi tiết (0.25đ)."
    thuc_hien(prompt)

# === CHỨC NĂNG 4 ===
elif "4." in menu:
    st.header("❤️ 4. HỖ TRỢ HÒA NHẬP")
    st.caption("Giải thích từ khó cho học sinh dân tộc thiểu số")
    noi_dung_input = st.text_input("Từ khó:", placeholder="VD: Axit, RAM...")
    prompt = f"Giải thích '{noi_dung_input}' cho HS dân tộc thiểu số bằng hình ảnh nương rẫy, bản làng."
    thuc_hien(prompt)

st.markdown("---")
st.caption("© 2026 Bản quyền thuộc về Nhóm tác giả Trường PTDTBT THCS Mùn Chung")
