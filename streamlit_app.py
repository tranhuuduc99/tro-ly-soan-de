import streamlit as st
import requests
import json

# --- CẤU HÌNH ---
st.set_page_config(page_title="Trợ lý Sư phạm", page_icon="🎓")
st.title("🎓 TRỢ LÝ SƯ PHẠM (BẢN ỔN ĐỊNH)")
st.markdown("---")

# --- DANH SÁCH 3 CHÌA KHÓA CỦA THẦY ---
KEYS = [
    "AIzaSyC7DAv7xrQ7rndZ72Sogogb4CWBdt1xpRM",
    "AIzaSyBsBd5X79HwzHmZUStQFrAC1ixhfpjeWV0",
    "AIzaSyBzMYO-OC9In_ilgLbg1rc57Pl7K8a-ay0"
]

# --- HÀM GỌI AI ĐƠN GIẢN NHẤT ---
def goi_ai(prompt):
    # Thử lần lượt từng chìa khóa
    for i, key in enumerate(KEYS):
        key = key.strip() # Xóa khoảng trắng thừa
        
        # Dùng model gemini-pro (Bản chuẩn quốc tế, không bao giờ lỗi mốt)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                continue # Key này hết hạn, thử key kế tiếp
            else:
                # Nếu lỗi khác, in ra để biết
                print(f"Key {i+1} lỗi: {response.status_code}")
                continue
                
        except:
            continue
            
    return "⚠️ LỖI: Tất cả 3 Key đều không chạy được. Có thể do mạng hoặc Google đang bảo trì."

# --- GIAO DIỆN ---
menu = st.radio("Chọn chức năng:", ["1. Soạn Trắc nghiệm", "2. Soạn Đúng/Sai", "3. Soạn Tự luận", "4. Giải thích từ khó"])
noi_dung = st.text_area("Nhập nội dung bài học:", height=150)

if st.button("🚀 THỰC HIỆN", type="primary"):
    if noi_dung:
        with st.spinner("Đang kết nối..."):
            # Tạo câu lệnh dựa trên menu
            if "1." in menu:
                prompt = f"Soạn 5 câu trắc nghiệm (4 đáp án A,B,C,D) có đáp án và giải thích từ: {noi_dung}"
            elif "2." in menu:
                prompt = f"Soạn 2 câu hỏi ĐÚNG/SAI (mỗi câu 4 ý) chuẩn GDPT 2018 từ: {noi_dung}"
            elif "3." in menu:
                prompt = f"Soạn đề tự luận + Barem chấm điểm chi tiết từ: {noi_dung}"
            else:
                prompt = f"Giải thích từ ngữ '{noi_dung}' cho học sinh dân tộc thiểu số dễ hiểu."
            
            # Gọi AI
            ket_qua = goi_ai(prompt)
            
            if "⚠️" in ket_qua:
                st.error(ket_qua)
            else:
                st.success("✅ Thành công!")
                st.markdown(ket_qua)
    else:
        st.warning("Thầy chưa nhập nội dung!")
