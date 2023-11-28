### Chức Năng của Bot Facebook:

1. **Đăng Nhập Tự Động:** Bot tự động đăng nhập vào tài khoản Facebook sử dụng thông tin từ file `metadata.json`.

2. **Truy Cập Nhóm Facebook:** Bot tự động chuyển đến một nhóm Facebook cụ thể sau khi đăng nhập.

3. **Xử Lý Bài Viết:** 
   - **Mở Rộng Nội Dung Bài Viết:** Nếu có nút "Xem thêm", bot sẽ tự động click để hiển thị toàn bộ nội dung.
   - **Xem Ảnh trong Bài Viết:** Bot sẽ xem mọi ảnh có thuộc tính `alt` trong bài viết.
   - **Đóng Ảnh:** Sau khi xem, bot sẽ đóng hình ảnh.

4. **Thả Reaction Ngẫu Nhiên:** Bot sẽ thả một trong bốn loại reaction ("Love", "Care", "Haha", "Wow") một cách ngẫu nhiên.

5. **Thời Gian Chạy:** Mỗi tài khoản chỉ chạy trong 5 phút.

6. **Cuộn Trang để Xem Bài Viết Mới:** Bot tự động cuộn trang để tải thêm bài viết.

### Hướng Dẫn Sử Dụng Bot:

#### Chuẩn Bị File `metadata.json`:

1. **Tạo File `metadata.json`:** Tạo một file mới với tên `metadata.json`.
2. **Nhập Thông Tin Tài Khoản:**
   - Mở file `metadata.json` bằng một trình soạn thảo văn bản.
   - Nhập thông tin tài khoản của bạn dưới dạng JSON. Mỗi tài khoản bao gồm email và mật khẩu.
   - Ví dụ về cấu trúc file:

     ```json
     [
       {
         "email": "emailcuaban@example.com",
         "password": "matkhaucuaban"
       },
       {
         "email": "emailkhac@example.com",
         "password": "matkhaukhac"
       }
       // Thêm các tài khoản khác theo cùng định dạng
     ]
     ```

#### Lưu Ý Khi Sử Dụng:

- Đảm bảo rằng bạn có Python và các thư viện cần thiết (Selenium, WebDriver, v.v.) đã được cài đặt trên máy của bạn.
- Đảm bảo rằng bạn có quyền truy cập vào nhóm Facebook mà bot sẽ tương tác.
- Lưu ý rằng việc sử dụng bot để tương tác tự động với Facebook có thể vi phạm các điều khoản dịch vụ của họ.