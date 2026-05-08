# CHƯƠNG 3: DEMO QUÁ TRÌNH TẤN CÔNG VÀ PHÒNG THỦ RANSOMWARE

## Mục lục

1. [Giới thiệu môi trường demo](#1-giới-thiệu-môi-trường-demo)
2. [Kịch bản tấn công — Social Engineering + Ransomware](#2-kịch-bản-tấn-công--social-engineering--ransomware)
   - 2.1 [Phát tán mã độc qua trang web giả](#21-phát-tán-mã-độc-qua-trang-web-giả)
   - 2.2 [Giai đoạn giả mạo phần mềm (Fake ProManager Suite)](#22-giai-đoạn-giả-mạo-phần-mềm-fake-promanager-suite)
   - 2.3 [Giai đoạn mã hóa dữ liệu (Ransomware Engine)](#23-giai-đoạn-mã-hóa-dữ-liệu-ransomware-engine)
   - 2.4 [Màn hình tống tiền (Ransom Note)](#24-màn-hình-tống-tiền-ransom-note)
3. [Hệ thống phòng thủ — HIDS và ứng phó sự cố](#3-hệ-thống-phòng-thủ--hids-và-ứng-phó-sự-cố)
   - 3.1 [Các phương pháp phát hiện tấn công](#31-các-phương-pháp-phát-hiện-tấn-công)
   - 3.2 [Quy trình ứng phó tự động](#32-quy-trình-ứng-phó-tự-động)
   - 3.3 [Chiến lược phục hồi dữ liệu](#33-chiến-lược-phục-hồi-dữ-liệu)
4. [Kết quả và đánh giá](#4-kết-quả-và-đánh-giá)
5. [Kết luận](#5-kết-luận)

---

## 1. Giới thiệu môi trường demo

Chương này trình bày hệ thống phòng thủ được xây dựng để phát hiện, ngăn chặn và ứng phó với cuộc tấn công ransomware trong kịch bản demo. Hệ thống được thiết kế theo khung ứng phó sự cố chuẩn NIST, với mục tiêu minh họa trực quan toàn bộ quy trình phòng thủ từ lúc phát hiện dấu hiệu đầu tiên đến khi hoàn tất đánh giá thiệt hại.

**Môi trường thực thi:**

| Thành phần | Thông số |
|---|---|
| Hệ điều hành | Arch Linux |
| Ngôn ngữ | Python 3.10+ |
| Giao diện phòng thủ | `tkinter` — Live Feed + Defense Steps |
| Phân tích tĩnh | YARA (3 rules) |
| Dữ liệu được bảo vệ | `shop_data/` — 8 file dữ liệu TMĐT mẫu |

---

## 2. Kịch bản tấn công — Social Engineering + Ransomware

Cuộc tấn công trong demo được thiết kế theo mô hình **Kill Chain** gồm 4 giai đoạn liên tiếp: phát tán qua trang web giả mạo, lây nhiễm thông qua phần mềm trojan, thực thi mã hóa ngầm, và cuối cùng là hiển thị màn hình tống tiền. Mỗi giai đoạn được xây dựng để phản ánh đúng cách các nhóm tội phạm ransomware thực sự hoạt động.

---

### 2.1 Phát tán mã độc qua trang web giả

Bước đầu tiên của chuỗi tấn công là **social engineering** — thao túng tâm lý nạn nhân thay vì khai thác lỗ hổng kỹ thuật. Kẻ tấn công dựng trang web quảng cáo giả mạo phần mềm quản lý dự án "ProManager Suite" bằng React + Vite, trông hoàn toàn chuyên nghiệp và đáng tin.

Trang web (`landing-web/`) có giao diện đầy đủ với các mục Hero, Features, Pricing, và nút Download nổi bật. Khi nạn nhân nhấn tải, trình duyệt phục vụ thẳng file `ProManagerSuite.exe` từ `landing-web/public/`. File này (~14 MB) được đóng gói bằng PyInstaller, chứa toàn bộ Python runtime cùng với mã độc bên trong — nạn nhân không thể phân biệt được với phần mềm hợp lệ bằng mắt thường.

Đây là lý do tại sao social engineering nguy hiểm hơn khai thác lỗ hổng kỹ thuật: nó không cần vượt qua bất kỳ hàng rào bảo mật nào — nạn nhân tự nguyện tải và chạy mã độc.

---

### 2.2 Giai đoạn giả mạo phần mềm (Fake ProManager Suite)

Khi nạn nhân chạy `ProManagerSuite.exe`, chương trình `fake_manager.py` khởi động và dẫn dắt qua 3 màn hình UI được thiết kế kỹ lưỡng nhằm tạo sự tin tưởng và câu giờ để mã hóa diễn ra ngầm.

**Màn hình 1 — Activation (cửa sổ nhỏ, nền trắng):**

Giao diện activation giả mạo xuất hiện ở giữa màn hình với thiết kế chuyên nghiệp: logo 📋, form nhập "API License Key" với placeholder `sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx`, nút "Activate License" màu tím indigo, và badge bảo mật "🔒 256-bit encrypted activation" ở góc dưới. Nạn nhân nhập bất kỳ key nào (trừ placeholder mặc định) và nhấn Activate.

Đây là thời điểm quan trọng: **ngay khi nút Activate được nhấn**, `fake_manager.py` lập tức khởi động `ransomware_simulator.py` trong một thread nền riêng biệt — quá trình mã hóa bắt đầu ngay lập tức, trước cả khi màn hình tiếp theo xuất hiện.

```python
# Trích từ fake_manager.py — _on_activate()
threading.Thread(target=self._silent_encrypt, daemon=True).start()
self._show_verifying()
```

**Màn hình 2 — Verifying (toàn màn hình, nền đen):**

Màn hình chuyển sang chế độ fullscreen với nền tối và thanh tiến trình xanh chạy liên tục, kèm các thông báo tuần tự: "Connecting to license server..." → "Validating entitlements..." → "Syncing workspace data..." → "Configuring your workspace...". Toàn bộ giai đoạn này kéo dài ~2.4 giây — đủ để nạn nhân tin rằng phần mềm đang xác thực hợp lệ, trong khi mã hóa vẫn đang chạy ngầm.

**Màn hình 3 — Dashboard (toàn màn hình, giao diện quản lý dự án đầy đủ):**

Dashboard ProManager giả xuất hiện với sidebar điều hướng, 4 thẻ thống kê (12 Active Projects, 47 Open Tasks, 3 Due Today, 8 Team Members), danh sách dự án với thanh tiến trình, và danh sách task. Giao diện hoàn toàn có vẻ hoạt động bình thường.

Dashboard hiển thị trong **3 giây** rồi tự động kích hoạt `_trigger_ransom()` — đóng dashboard và mở màn hình tống tiền. Trong suốt 3 giây đó, mã hóa vẫn tiếp tục chạy ngầm.

---

### 2.3 Giai đoạn mã hóa dữ liệu (Ransomware Engine)

`ransomware_simulator.py` triển khai engine mã hóa thực sự — không chỉ mô phỏng — sử dụng thuật toán **Fernet** từ thư viện `cryptography`. Fernet là mã hóa đối xứng kết hợp AES-128-CBC và HMAC-SHA256, nghĩa là dữ liệu đã bị mã hóa không thể khôi phục nếu không có đúng khóa.

**Quy trình mã hóa từng file:**

1. Tạo khóa Fernet ngẫu nhiên một lần duy nhất (`Fernet.generate_key()`) và lưu tại `shop_data/.ransom_key`
2. Duyệt đệ quy toàn bộ thư mục `shop_data/`, thu thập danh sách file cần mã hóa
3. Với mỗi file: đọc nội dung → mã hóa bằng Fernet → ghi ra `<tên_file>.encrypted` → **xóa file gốc**
4. Chờ `encrypt_delay` giây (mặc định 10s) trước khi chuyển sang file tiếp theo — làm chậm tốc độ để demo rõ ràng hơn

**Cơ chế sandbox an toàn:**

Hàm `_is_inside_sandbox()` sử dụng `os.path.realpath()` để kiểm tra mọi file trước khi mã hóa — ngăn chặn triệt để path traversal attack. Các đuôi file `.exe .py .sh .bat .so .dll` bị bỏ qua, đảm bảo mã độc không tự mã hóa chính nó. Chuỗi `RANSOMWARE_SIMULATOR_DEMO_SAFE` được nhúng vào source code để scanner có thể tự nhận diện đây là công cụ demo.

**Timeline mã hóa 8 file dữ liệu TMĐT:**

| Thời điểm | File bị mã hóa | Ghi chú |
|---|---|---|
| t = 0s | Bắt đầu (khi nạn nhân nhấn Activate) | Chạy ngầm, nạn nhân chưa biết |
| t = 10s | `invoice_2024.txt` → `.encrypted` | HIDS phát hiện ở đây |
| t = 20s | `customer_data.csv` → `.encrypted` | Nếu chưa bị chặn |
| t = 30s | `contract.txt` → `.encrypted` | … |
| … | 5 file còn lại | … |
| t = 80s | Toàn bộ 8 file bị mã hóa | Kịch bản không có phòng thủ |

---

### 2.4 Màn hình tống tiền (Ransom Note)

`fake_ransom.py` chiếm toàn bộ màn hình ở chế độ fullscreen không thể đóng thông thường, hiển thị giao diện đe dọa với nền đen và chữ đỏ:

- **Tiêu đề nhấp nháy** mỗi 0.8 giây: `YOUR FILES HAVE BEEN ENCRYPTED` 💀
- **Đồng hồ đếm ngược 72 giờ** (màu vàng cam, font lớn) — mỗi giây giảm một, kèm cảnh báo "KEY WILL BE PERMANENTLY DELETED AT ZERO"
- **Thông tin thanh toán:**

| Trường | Nội dung |
|---|---|
| Bank | BIDV — PGD Ha Tinh |
| Account Owner | An Thuyên |
| Account Number | 2929292929 |
| Nội dung chuyển khoản | `UNLOCK <tên_máy_nạn_nhân>` |
| Liên hệ sau thanh toán | support@promanager.io |
| **Số tiền yêu cầu** | **29.000.000 VND** |

- **Ô nhập decrypt code** — trong thực tế chỉ kẻ tấn công mới biết code. Trong demo, nhập `DEMO-SAFE-2024-TMDT` để mô phỏng kịch bản đã trả tiền chuộc và nhận được code giải mã.

Màn hình này minh họa rõ tâm lý áp lực mà ransomware tạo ra: đếm ngược thời gian, mất dữ liệu vĩnh viễn nếu hết hạn, và cảm giác không còn lựa chọn nào khác ngoài trả tiền.

---

## 3. Hệ thống phòng thủ

Hệ thống phòng thủ trong demo được thiết kế theo khung ứng phó sự cố chuẩn NIST, bao gồm các giai đoạn: chuẩn bị trước tấn công, phát hiện sớm khi tấn công xảy ra, cô lập và ngăn chặn lây lan, backup khẩn cấp dữ liệu còn lại, và cuối cùng là đánh giá thiệt hại để phục hồi. Triết lý cốt lõi là: hệ thống phòng thủ không thể đảm bảo ngăn chặn hoàn toàn mọi cuộc tấn công, nhưng có thể giảm thiểu thiệt hại xuống mức thấp nhất có thể và đảm bảo khả năng phục hồi.

---

### 3.1 Các phương pháp phát hiện tấn công

Thách thức lớn nhất trong phòng chống ransomware là phát hiện sớm — lý tưởng nhất là trước khi quá nhiều dữ liệu bị mã hóa. Hệ thống demo kết hợp nhiều lớp phát hiện khác nhau, bởi vì không có phương pháp nào là hoàn hảo khi đứng độc lập.

**Phát hiện dựa trên chữ ký (Signature-based Detection)**

Đây là phương pháp truyền thống và đơn giản nhất: hệ thống duy trì một danh sách các tên file, chuỗi ký tự, và mẫu mã nguồn đặc trưng của mã độc đã biết. Khi quét thư mục, nếu phát hiện tên file chứa các từ khóa như "promanagersuite", "ransomware", "fake_manager", hoặc các đoạn mã đặc trưng như lời gọi hàm mã hóa Fernet trong file script, hệ thống ngay lập tức đưa ra cảnh báo mức cao nhất (CRITICAL).

Ưu điểm của phương pháp này là tốc độ nhanh và độ chính xác cao với các mã độc đã biết. Hạn chế là không phát hiện được các biến thể mới chưa có trong danh sách chữ ký — đây là lý do cần kết hợp thêm các phương pháp khác.

**Phân tích entropy (Anomaly-based Detection)**

Phương pháp này dựa trên một đặc điểm toán học của dữ liệu bị mã hóa: entropy — hay độ ngẫu nhiên của dữ liệu — rất cao. Một file văn bản thông thường có entropy thấp vì các ký tự lặp đi lặp lại theo quy luật ngôn ngữ. Ngược lại, một file đã bị mã hóa hoặc nén có phân bố byte gần như ngẫu nhiên hoàn toàn, đẩy giá trị entropy lên gần mức tối đa (8 bits).

Hệ thống demo đọc phần đầu của mỗi file (64KB) và tính entropy Shannon. Nếu giá trị vượt ngưỡng 7.2 bits, file đó bị đánh dấu là nghi ngờ. Phương pháp này đặc biệt hiệu quả để phát hiện các file đã bị mã hóa mà không cần biết trước loại mã độc cụ thể.

**Giám sát hành vi filesystem (Behavior-based Detection)**

Ransomware có một dấu hiệu hành vi rất đặc trưng: trong thời gian ngắn, một lượng lớn file lần lượt bị đọc rồi biến mất và được thay thế bằng file mới có đuôi `.encrypted`. Đây là kiểu hoạt động Disk I/O bất thường không bao giờ xuất hiện trong điều kiện bình thường.

Hệ thống giám sát theo dõi thư mục `shop_data/` mỗi giây, so sánh danh sách file hiện tại với danh sách trước đó. Ngay khi phát hiện bất kỳ file `.encrypted` mới nào xuất hiện — tức là sau khi file đầu tiên bị mã hóa — hệ thống lập tức kích hoạt quy trình ứng phó. Đây là lớp phát hiện quan trọng nhất trong demo vì nó hoạt động theo thời gian thực, không cần quét định kỳ.

**Giám sát tiến trình (Process Monitoring)**

Hệ thống liên tục kiểm tra danh sách các tiến trình đang chạy trên máy, tìm kiếm các tên tiến trình khớp với danh sách mã độc đã biết như `ProManagerSuite`, `fake_manager`, `ransomware_simulator`. Nếu phát hiện bất kỳ tiến trình nào trong danh sách này đang hoạt động, đây là tín hiệu cảnh báo rõ ràng ngay cả trước khi file nào bị mã hóa.

**Phân tích tĩnh bằng luật YARA**

Trước khi thực thi một file đáng ngờ, có thể sử dụng công cụ phân tích tĩnh để quét file bằng các luật YARA — một ngôn ngữ đặc tả mẫu nhận dạng mã độc được dùng rộng rãi trong ngành bảo mật. Hệ thống demo có 3 luật YARA: một luật phát hiện chữ ký đặc trưng của bộ mô phỏng ransomware, một luật nhận dạng header của token Fernet trong dữ liệu đã mã hóa, và một luật phát hiện nội dung HTML của màn hình tống tiền. Phân tích tĩnh giúp cảnh báo nguy cơ trước khi thiệt hại xảy ra.

---

### 3.2 Quy trình ứng phó tự động khi bị tấn công

Khi lớp giám sát hành vi filesystem phát hiện file `.encrypted` đầu tiên xuất hiện, hệ thống không chờ người dùng xử lý mà lập tức kích hoạt quy trình ứng phó tự động gồm 4 bước liên tiếp. Giao diện phòng thủ hiển thị từng bước này theo thời gian thực trên màn hình Live Feed để người quan sát có thể theo dõi.

**Bước 1 — Xác nhận và phân loại mối đe dọa**

Ngay sau khi phát hiện, hệ thống ghi nhận thời điểm tấn công, đếm số file đã bị mã hóa cho đến thời điểm đó, và xác nhận đây là một cuộc tấn công ransomware dựa trên tổ hợp các tín hiệu: sự xuất hiện của file `.encrypted`, có thể có tiến trình mã độc đang chạy, và khóa `.ransom_key` được tạo trong thư mục dữ liệu. Bước này quan trọng để tránh phản ứng nhầm với các hoạt động bình thường của hệ thống.

**Bước 2 — Cô lập và dừng tiến trình mã độc**

Đây là bước tranh đua với thời gian: mỗi giây trôi qua là thêm một file bị mã hóa. Hệ thống ngay lập tức gửi lệnh dừng tới tất cả các tiến trình trong danh sách mã độc đang chạy. Đồng thời, một file cờ trạng thái được tạo ra để thông báo hệ thống đang trong chế độ bảo trì — ngăn chặn các giao dịch mới và giảm thiểu nguy cơ dữ liệu tiếp tục bị xâm phạm.

Trong thực tế, bước này còn bao gồm cô lập mạng — ngắt kết nối máy bị nhiễm khỏi mạng nội bộ để ngăn mã độc gửi dữ liệu ra ngoài hoặc lây lan sang các máy khác. Demo mô phỏng hành động này bằng cách tạo file cờ `NETWORK_ISOLATED.flag`.

**Bước 3 — Backup khẩn cấp dữ liệu còn lại**

Sau khi tiến trình mã độc đã bị dừng, hệ thống ngay lập tức tạo một bản sao lưu khẩn cấp toàn bộ thư mục dữ liệu — bao gồm cả các file đã bị mã hóa và các file còn nguyên vẹn. Mục đích của bước này là "đóng băng" trạng thái hiện tại của hệ thống: dù một số file đã mất, những file chưa bị đụng đến vẫn được bảo toàn tuyệt đối trong bản backup này.

Bản backup khẩn cấp được lưu dưới định dạng nén `.tar.gz` với tên có dấu thời gian chính xác, giúp dễ dàng xác định trạng thái dữ liệu tại thời điểm ứng phó. Đây sẽ là nguồn để phục hồi dữ liệu trong bước tiếp theo.

**Bước 4 — Đánh giá thiệt hại**

Khi các bước khẩn cấp đã hoàn tất, hệ thống tổng hợp báo cáo thiệt hại: có bao nhiêu file đã bị mã hóa (mất), bao nhiêu file còn nguyên vẹn, bản backup khẩn cấp đã được tạo hay chưa. Báo cáo này hiển thị ngay trên giao diện và có thể xuất ra file văn bản để lưu hồ sơ sự cố.

---

### 3.3 Chiến lược phục hồi dữ liệu

Sau khi kiểm soát được tình huống, câu hỏi quan trọng nhất là: làm thế nào để lấy lại dữ liệu đã mất? Hệ thống demo cung cấp hai hướng tiếp cận, phản ánh đúng thực tế mà các tổ chức phải đối mặt khi bị ransomware tấn công.

**Phục hồi từ backup — Phương án không cần thương lượng với kẻ tấn công**

Nếu tổ chức duy trì backup định kỳ và bản backup gần nhất được tạo trước khi cuộc tấn công xảy ra, đây là con đường phục hồi lý tưởng. Toàn bộ dữ liệu được khôi phục về trạng thái tại thời điểm backup mà không cần biết khóa giải mã của kẻ tấn công, không cần trả bất kỳ khoản tiền chuộc nào.

Đây là lý do tại sao backup định kỳ được xem là biện pháp phòng thủ quan trọng nhất đối với ransomware. Trong demo, hệ thống hỗ trợ lịch backup tự động theo chu kỳ 1 giờ, 3 giờ, 6 giờ, 12 giờ hoặc 24 giờ — tần suất cao hơn đồng nghĩa với ít dữ liệu bị mất hơn trong trường hợp xấu nhất.

Tuy nhiên, cần lưu ý một giới hạn quan trọng: backup khẩn cấp được tạo ra trong quá trình ứng phó vẫn chứa các file đã bị mã hóa, vì hệ thống chỉ có thể sao lưu trạng thái hiện tại. Những file bị mã hóa trước khi backup được tạo ra sẽ vẫn ở dạng mã hóa trong bản sao lưu đó. Để phục hồi hoàn toàn, cần sử dụng bản backup định kỳ được tạo từ trước khi cuộc tấn công bắt đầu.

**Giải mã bằng khóa của kẻ tấn công — Kịch bản trả tiền chuộc**

Trong trường hợp không có backup, con đường duy nhất để lấy lại dữ liệu là nhận khóa giải mã từ kẻ tấn công — thường đồng nghĩa với việc phải trả tiền chuộc. Đây là kịch bản mà các tổ chức thiếu chiến lược backup phải đối mặt, và kết quả thường rất bấp bênh: kẻ tấn công có thể không giữ lời, cung cấp khóa sai, hoặc yêu cầu thêm tiền sau khi đã nhận được khoản đầu tiên.

Giao diện demo có phần nhập khóa giải mã để mô phỏng kịch bản này. Trong môi trường thực tế, khóa giải mã Fernet là một chuỗi 44 ký tự base64 mà chỉ kẻ tấn công mới nắm giữ — minh họa rõ ràng tại sao backup không thể thiếu và tại sao không bao giờ nên phụ thuộc vào việc thương lượng với tội phạm mạng.

---

## 4. Kết quả và đánh giá

### 4.1 Hiệu quả phát hiện và ứng phó

Trong quá trình chạy demo thực tế, kết quả thu được cho thấy hệ thống HIDS hoạt động đúng theo thiết kế. Kể từ khi mã độc bắt đầu mã hóa cho đến khi bị phát hiện và ngăn chặn, chỉ có 1 trong 8 file bị mã hóa — tức là 7/8 file dữ liệu được bảo toàn. Toàn bộ quy trình ứng phó tự động từ lúc phát hiện đến lúc hoàn tất đánh giá thiệt hại kéo dài khoảng 55 giây.

| Thông số | Kết quả |
|---|---|
| Số file bị mã hóa trước khi bị ngăn chặn | 1 / 8 file (12,5%) |
| Số file được bảo toàn | 7 / 8 file (87,5%) |
| Backup khẩn cấp được tạo tự động | Có |
| Tổng thời gian ứng phó tự động | ~55 giây |

Tiến trình mã độc bị dừng hoàn toàn trong bước 2 của quy trình ứng phó, ngăn không cho thêm file nào bị mã hóa sau đó. Điều này minh họa giá trị của việc phát hiện dựa trên hành vi theo thời gian thực: thay vì chờ quét định kỳ, hệ thống phản ứng ngay khi có dấu hiệu đầu tiên.

---

### 4.2 Điểm mạnh của hệ thống

Cách tiếp cận kết hợp nhiều lớp phát hiện giúp hệ thống không phụ thuộc vào bất kỳ một phương pháp duy nhất nào. Một mã độc chưa có trong cơ sở dữ liệu chữ ký vẫn có thể bị phát hiện qua entropy cao hoặc hành vi filesystem bất thường. Ngược lại, một file entropy cao nhưng thực chất là file nén hợp lệ sẽ không bị cảnh báo nhầm nếu không có dấu hiệu hành vi kèm theo.

Khả năng ứng phó tự động không phụ thuộc vào sự có mặt của người quản trị là điểm mấu chốt trong thực tế — ransomware thường được kích hoạt vào ban đêm hoặc cuối tuần khi không có ai theo dõi. Hệ thống tự dừng tiến trình mã độc và tạo backup khẩn cấp mà không cần can thiệp thủ công.

Việc tách biệt rõ ràng giữa "backup là công cụ phòng thủ chủ động" và "giải mã bằng key là giải pháp bị động sau khi đã thua" phản ánh đúng quan điểm bảo mật hiện đại: đầu tư vào phòng ngừa và phục hồi, không đặt cược vào việc thương lượng với kẻ tấn công.

---

### 4.3 Hạn chế và hướng cải thiện

Hệ thống demo còn một số điểm chưa phản ánh đầy đủ môi trường thực tế. Danh sách chữ ký mã độc hiện được hard-code trong mã nguồn, trong khi thực tế cần một cơ chế cập nhật liên tục từ các nguồn threat intelligence. Việc cô lập mạng được mô phỏng bằng file cờ thay vì thực sự chặn giao tiếp mạng — trong triển khai thực tế cần tích hợp với tường lửa. Log sự kiện hiện chỉ lưu trong bộ nhớ, mất khi ứng dụng đóng, trong khi một hệ thống thực cần ghi log bền vững phục vụ điều tra pháp y sau sự cố. Ngoài ra, hệ thống chưa kiểm tra khả năng mã độc thiết lập cơ chế tự khởi động lại sau khi bị dừng.

---

## 5. Kết luận

Qua demo chương 3, có thể thấy rõ cuộc đối đầu không cân sức giữa tốc độ tấn công và khả năng phòng thủ của hệ thống. Ransomware hoạt động âm thầm, nhanh chóng, và khai thác triệt để yếu tố bất ngờ. Hệ thống phòng thủ, dù được tự động hóa đến mức nào, vẫn luôn ở thế phản ứng — chỉ có thể giảm thiểu thiệt hại chứ không thể ngăn chặn hoàn toàn khi mã độc đã được kích hoạt.

Bài học thực tiễn quan trọng nhất từ demo này là: **backup định kỳ, được lưu tách biệt khỏi mạng nội bộ, là biện pháp phòng thủ duy nhất đảm bảo phục hồi hoàn toàn mà không phụ thuộc vào bất kỳ yếu tố nào khác**. Mọi lớp phát hiện và ứng phó đều có giá trị, nhưng nếu không có backup, ngay cả khi phát hiện sớm cũng không thể cứu được dữ liệu đã bị mã hóa trước đó.

Bên cạnh đó, demo cũng nhấn mạnh rằng con người — thông qua hành động tải và chạy phần mềm không rõ nguồn gốc — vẫn là điểm yếu căn bản nhất trong chuỗi bảo mật. Không có hệ thống kỹ thuật nào có thể bù đắp hoàn toàn cho sự thiếu cảnh giác của người dùng cuối.

---

*Báo cáo môn An Toàn Bảo Mật Hệ Thống Thông Tin*
*Demo Environment: Arch Linux — Python 3.10+ — Fernet Encryption*
