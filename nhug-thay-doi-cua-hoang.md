1. thêm escape key ở màn hình tống tiền (fake_ransom)
+ Ấn Esc hoặc Ctrl + Q để thoát terminal màn hình ransom 
2. thêm 1 file c2_server và thay đổi trong fake_manager để có thể kết nối tới c2_server khi ở chế độ tấn công và có thể nhận key giải mã khi ở chế độ phòng thủ
- các câu lệnh hoạt động
+ pip install flask 
+ python -m manager-agent.c2_server (mở server để lưu ransom_key và key giải mã)
+ .\.venv310\Scripts\activate
+ Tấn công: .\demo.ps1 -AttackOnly
+ Phòng thủ/phục hồi: .\demo.ps1 -DefendOnly
+ Chạy full demo: .\demo.ps1
