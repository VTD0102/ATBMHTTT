# Tổng Quan Dự Án: ATBMHTTT - Demo Phòng Chống Ransomware

## 1. Toàn Cục Dự Án (Global Scope)
Dự án là một hệ thống mô phỏng học thuật về An Toàn Bảo Mật Hệ Thống Thông Tin (ATBMHTTT). Kịch bản bao quát toàn bộ vòng đời của một cuộc tấn công ransomware thông qua con đường Social Engineering (Tấn công phi kỹ thuật) vào một hệ thống Thương mại Điện tử (TMĐT), đồng thời thể hiện các giải pháp phòng thủ, phát hiện và phục hồi dữ liệu.

## 2. Công Nghệ & Công Cụ Vận Hành (Technologies Used)
- **Ngôn ngữ chính:** Python 3.10+ (cho Mã độc & Phần mềm phòng thủ), Node.js (React + Vite cho Landing Web).
- **Giao diện (GUI):** Thư viện `tkinter` của Python để tạo giao diện phần mềm giả mạo (Fake ProManager) và Bảng điều khiển bảo vệ (Defender Dashboard).
- **Mã hóa dữ liệu:** Thư viện `cryptography` (sử dụng chuẩn Fernet) để mã hóa các tệp tin.
- **Phân tích mã độc:** Thư viện `yara-python` (sử dụng YARA rules để nhận diện các pattern nguy hiểm).
- **Đóng gói phần mềm:** `PyInstaller` để đóng gói mã nguồn Python thành file thực thi độc lập (ELF binary `ProManagerSuite.exe`).

## 3. Các Chức Năng Chính (Core Functions)
Dự án được chia làm 3 cụm chức năng cốt lõi:
- **Tấn công (Attacker - `manager-agent/` & `landing-web/`):** Cung cấp trang web quảng cáo lừa đảo để tải xuống phần mềm độc hại. File thực thi là một phần mềm "chim mồi" với giao diện như thật, chứa engine ransomware ngầm.
- **Dữ liệu Nạn nhân (`shop_data/`):** Môi trường Sandbox chứa các file mô phỏng cơ sở dữ liệu hệ thống TMĐT (ví dụ: hóa đơn, thông tin khách hàng, hợp đồng...).
- **Phòng thủ (Defender - `defender/`):** Bộ công cụ tích hợp các chức năng rà quét (Scanner), phân tích tĩnh (Static Analyzer), giám sát hành vi theo thời gian thực (Behavior Monitor), quản lý sao lưu dữ liệu (Backup Manager), giải mã dữ liệu (Decryptor) và Giao diện giám sát trung tâm.

## 4. Luồng Hoạt Động (Flows & Activities)
**Luồng Tấn Công:**
1. Nạn nhân truy cập vào trang Landing Page lừa đảo và tải xuống file `ProManagerSuite.exe`.
2. Nạn nhân nhấp đúp thực thi file, một giao diện yêu cầu kích hoạt phần mềm giả mạo hiện ra.
3. Sau khi nhập thông tin, phần mềm hiển thị Dashboard giả như một công cụ quản lý dự án chuyên nghiệp, làm nạn nhân mất đi sự cảnh giác.
4. Khoảng 10 giây sau, "quả bom" Ransomware được kích hoạt: màn hình Ransom Note hiển thị phóng to toàn màn hình (yêu cầu nộp phạt 59 triệu VNĐ), đồng thời engine ngầm thực hiện mã hóa toàn bộ dữ liệu trong thư mục sandbox thành đuôi `.encrypted` và sinh ra tệp khóa giải mã `.ransom_key`.

**Luồng Phòng Thủ & Phục Hồi:**
1. **Phòng ngừa:** Tool `behavior_monitor.py` liên tục theo dõi hệ thống file.
2. **Phát hiện:** Sử dụng các luật YARA (`ransomware.yar`) và thuật toán tính Entropy (đo độ hỗn loạn) để phát hiện file thực thi bị đóng gói bất thường hoặc nhận diện dữ liệu vừa bị mã hóa.
3. **Phục hồi:** Sử dụng `decryptor.py` kết hợp với file khóa `.ransom_key` để khôi phục dữ liệu gốc, hoặc kịch bản xấu nhất là dùng `backup_manager.py` để restore lại toàn bộ từ bản lưu file nén `.tar.gz` an toàn trước đó.

## 5. Đầu Vào, Đầu Ra & Thông Số (Inputs / Outputs / Parameters)
- **Đầu vào (Inputs):**
  - Dữ liệu sạch (văn bản, PDF, CSV,...) nằm trong thư mục `shop_data/`.
  - Dữ liệu người dùng (API Key) trên phần mềm lừa đảo.
  - Các tệp luật phát hiện (YARA rules).
  - Bản sao lưu hệ thống (`.tar.gz`) trong thư mục `backups/`.
- **Đầu ra (Outputs):**
  - Các tệp tin bị khóa với phần mở rộng mới là `.encrypted`.
  - Cửa sổ Ransom Note đe dọa tống tiền.
  - Các luồng log cảnh báo từ Defender GUI: mức độ `CRITICAL` (khi tên pattern bị trùng khớp), `HIGH` (khi mức Entropy > 7.2 bits), `MEDIUM` (khi Entropy 6.5-7.2 bits).
  - Các tập tin dữ liệu đã được giải mã và trả lại trạng thái nguyên vẹn.
- **Thông số cấu hình quan trọng:**
  - **Mã Bypass Demo:** `DEMO-SAFE-2024-TMDT` (dùng để tắt nhanh cửa sổ Ransom Note).
  - **Ngưỡng đo độ hỗn loạn (Entropy Thresholds):** Tập tin có độ hỗn loạn > 7.5 bits bị nhận diện là file bị mã hóa; tập tin thực thi có entropy > 7.2 bits bị cảnh báo chứa mã độc nhúng ẩn.
  - **Danh sách mở rộng loại trừ (Whitelist):** `.exe, .py, .sh, .bat, .dll, .so` (giúp ransomware tránh tự mã hóa chính bản thân nó hoặc làm hỏng hệ điều hành).

## 6. Liên Tưởng Đến Tình Huống Thực Tế Trong Ransomware
Dự án mô phỏng này ánh xạ rất sát với các phương thức tấn công của các tổ chức tội phạm mạng lớn (như LockBit, Conti hay REvil):
- **Kỹ thuật Social Engineering (Phishing / Malvertising):** Kẻ tấn công không cố gắng đột nhập hệ thống (Brute-force) mà tạo ra một lớp vỏ bọc hoàn hảo (phần mềm ProManager) và dụ dỗ chính nhân viên nội bộ tải về. Rất nhiều vụ xâm nhập thực tế xuất phát từ một email lừa đảo hoặc link tải phần mềm giả mạo.
- **Chiến thuật "Trojan" ẩn mình (Stealth & Time Delay):** Khi chạy mã độc, nó không lập tức phá hoại mà hiển thị giao diện phần mềm hoạt động bình thường để củng cố lòng tin. Sau một độ trễ nhất định (trigger), quá trình mã hóa mới chạy ngầm (Trong thực tế, "thời gian nằm vùng" - Dwell Time có thể lên tới nhiều tháng để ăn cắp dữ liệu trước khi khóa file).
- **Mã hóa không thể phá vỡ (Strong Cryptography):** Việc sử dụng các chuẩn mật mã mạnh mẽ khiến cho quá trình giải mã mà thiếu Private Key là điều bất khả thi, đẩy doanh nghiệp vào thế buộc phải trả tiền chuộc.
- **Giải pháp tối thượng - Sao lưu ngoại tuyến (Offline Backups):** Kịch bản này nhấn mạnh một bài học thực tế sống còn: khi mọi lớp phòng thủ như Firewall, EDR, Scanner đều có khả năng bị vượt qua, thì việc có một bản Backup dữ liệu định kỳ là cứu cánh duy nhất để khôi phục hoạt động kinh doanh mà không phải thỏa hiệp với tin tặc.
