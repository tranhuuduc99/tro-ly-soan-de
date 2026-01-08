import streamlit as st
import requests
import json
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Trợ lý Sư phạm 4.0", page_icon="🎓", layout="wide")
st.title("🎓 HỆ THỐNG TRỢ LÝ ẢO SƯ PHẠM 4.0")
st.caption("Phiên bản: Debugging (Hiển thị lỗi chi tiết)")
st.markdown("---")

# 3 KEY CỦA THẦY (ĐÃ ĐƯỢC XỬ LÝ KHOẢNG TRẮNG)
DANH_SACH_KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

with st.sidebar:
    st.header("⚙️ CHỨC NĂNG")
    menu = st.radio("Chọn tác vụ:", ["1. Soạn Trắc nghiệm", "2. Soạn Đúng/Sai", "3. Soạn Tự luận", "4. Hỗ trợ Hòa nhập"])
    st.info(f"Đã nạp {len(DANH_SACH_KEYS)} Key dự phòng.")

# --- HÀM GỌI AI (CÓ BÁO LỖI CHI TIẾT) ---
def goi_ai_chi_tiet(prompt):
    log_loi = "" # Ghi lại nhật ký lỗi để báo cáo
    
    for index, key in enumerate(DANH_SACH_KEYS):
        # 1. Xử lý sạch Key (Xóa khoảng trắng thừa nếu có)
        clean_key = key.strip()
        
        # 2. Cấu hình gửi
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={clean_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # NẾU THÀNH CÔNG (200)
            if response.status_code == 200:
                try:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                except:
                    log_loi += f"Key {index+1}: Lỗi cấu trúc JSON.\n"
                    continue
            
            # NẾU THẤT BẠI -> GHI LẠI LÝ DO
            else:
                log_loi += f"Key {index+1}: Mã lỗi {response.status_code} ({response.text[:100]}...)\n"
                continue
                
        except Exception as e:
            log_loi += f"Key {index+1}: Lỗi mạng {str(e)}\n"
            continue

    # Trả về báo cáo lỗi nếu tất cả đều thất bại
    return f"⛔ KHÔNG THỂ KẾT NỐI!\n\nChi tiết lỗi (Thầy hãy chụp màn hình gửi kỹ thuật):\n{log_loi}"

# --- XỬ LÝ GIAO DIỆN ---
def thuc_hien(prompt):
    if st.button("🚀 THỰC HIỆN", type="primary"):
        if noi_dung:
            with st.spinner("Đang kiểm tra kết nối..."):
                ket_qua = goi_ai_chi_tiet(prompt)
                if "⛔" in ket_qua:
                    st.error(ket_qua) # Hiện khung đỏ báo lỗi chi tiết
                else:
                    st.success("✅ Thành công!")
                    st.markdown(ket_qua)
        else:
            st.error("Chưa nhập nội dung!")

# Giao diện nhập liệu
if "1." in menu:
    st.header("📝 1. SOẠN TRẮC NGHIỆM")
    noi_dung = st.text_area("Nội dung:")
    thuc_hien(f"Soạn 5 câu trắc nghiệm từ: '{noi_dung}'.")
elif "2." in menu:
    st.header("✅ 2. SOẠN ĐÚNG/SAI")
    noi_dung = st.text_area("Nội dung:")
    thuc_hien(f"Soạn 2 câu Đúng/Sai chuẩn GDPT 2018 từ: '{noi_dung}'.")
elif "3." in menu:
    st.header("✍️ 3. TỰ LUẬN")
    noi_dung = st.text_area("Nội dung:")
    thuc_hien(f"Soạn đề tự luận + Barem từ: '{noi_dung}'.")
elif "4." in menu:
    st.header("❤️ 4. HỖ TRỢ HÒA NHẬP")
    noi_dung = st.text_input("Từ khó:")
    thuc_hien(f"Giải thích '{noi_dung}' cho HS dân tộc bằng hình ảnh nương rẫy.")
