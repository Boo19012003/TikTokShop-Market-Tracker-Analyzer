# TikTok Shop Market Tracker & Analyzer

Dự án này thu thập dữ liệu sản phẩm từ trang [TikTok Shop Việt Nam](https://www.tiktok.com/shop/vn), làm sạch và xử lý dữ liệu để phục vụ cho việc phân tích.

## Cách thức hoạt động

Dự án bao gồm hai phần chính:

1.  **Thu thập dữ liệu (`main.py`):**
    *   Sử dụng Playwright để khởi chạy một trình duyệt Chromium và tự động duyệt web.
    *   Truy cập vào trang chủ của TikTok Shop Việt Nam để lấy danh sách các danh mục sản phẩm.
    *   Với mỗi danh mục, kịch bản sẽ truy cập vào trang của danh mục đó, cuộn trang để tải thêm sản phẩm.
    *   Trích xuất thông tin chi tiết của từng sản phẩm, bao gồm: tên, nhãn (xu hướng, hàng Việt, deal), link, đánh giá, số lượng đã bán, giá gốc, giá hiện tại và phần trăm giảm giá.
    *   Lưu dữ liệu thô vào file `tiktok_shop_products.csv`. Kịch bản có sử dụng một hồ sơ người dùng trình duyệt (`tiktok_user_data`) để mô phỏng người dùng thật và tránh bị chặn.

2.  **Làm sạch dữ liệu (`clean_data.ipynb`):**
    *   Sử dụng thư viện Pandas để đọc dữ liệu từ `tiktok_shop_products.csv`.
    *   Thực hiện các bước làm sạch:
        *   Chuyển đổi kiểu dữ liệu cho các cột (ví dụ: `Rating` sang số thực, `Sold` sang số nguyên).
        *   Loại bỏ các ký tự không cần thiết (như `₫`, `.`, `%`) khỏi các cột giá và số lượng.
        *   Xử lý các giá trị bị thiếu (null), ví dụ như ở cột `Original_Price`.
    *   Lưu dữ liệu đã được làm sạch vào file `tiktok_shop_products_cleaned.csv`.

## Cài đặt

1.  **Clone repository:**
    ```bash
    git clone https://github.com/Boo19012003/TikTokShop-Market-Tracker-Analyzer.git
    cd TikTokShop-Market-Tracker-Analyzer
    ```

2.  **Tạo môi trường ảo (khuyến nghị):**
    ```bash
    python -m venv .venv
    # Trên Windows
    .venv\Scripts\activate
    # Trên macOS/Linux
    source .venv/bin/activate
    ```

3.  **Cài đặt các gói phụ thuộc:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Cài đặt trình duyệt cho Playwright:**
    ```bash
    playwright install
    ```

## Sử dụng

### 1. Thu thập dữ liệu

Chạy file `main.py` để bắt đầu quá trình thu thập dữ liệu.
**Lưu ý:** Kịch bản sẽ mở một cửa sổ trình duyệt. Bạn có thể sẽ cần đăng nhập vào tài khoản TikTok của mình trong lần chạy đầu tiên để có thể truy cập đầy đủ vào các trang sản phẩm.

```bash
python main.py
```

Dữ liệu thô sẽ được lưu trong file `tiktok_shop_products.csv`.

### 2. Làm sạch và Phân tích dữ liệu

Mở và chạy các cell trong file Jupyter Notebook `clean_data.ipynb` để xử lý dữ liệu thô và lưu lại dưới dạng file `tiktok_shop_products_cleaned.csv`.

Bạn có thể thêm các phân tích của riêng mình vào file notebook này.

## Mô tả các file

*   `main.py`: Kịch bản chính để thu thập dữ liệu sản phẩm từ TikTok Shop.
*   `clean_data.ipynb`: Jupyter Notebook để làm sạch và xử lý dữ liệu đã thu thập.
*   `requirements.txt`: Danh sách các gói Python cần thiết cho dự án.
*   `tiktok_shop_products.csv`: File CSV chứa dữ liệu sản phẩm thô được thu thập bởi `main.py`.
*   `tiktok_shop_products_cleaned.csv`: File CSV chứa dữ liệu sản phẩm đã được làm sạch từ `clean_data.ipynb`.
*   `tiktok_user_data/`: Thư mục chứa dữ liệu người dùng trình duyệt (cache, cookie) để Playwright sử dụng, giúp duy trì phiên đăng nhập và tránh bị phát hiện là bot.
*   `.gitignore`: File cấu hình để bỏ qua các file và thư mục không cần thiết khi commit lên Git.
