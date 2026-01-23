from playwright.sync_api import sync_playwright
import time
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

from captcha_solver import solve_tiktok_captcha

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL và SUPABASE_KEY phải được thiết lập trong biến môi trường.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def solve_captcha(page):
    print("[Solve Captcha] PHÁT HIỆN CAPTCHA! Đang tiến hành giải...")
    captcha_count = 0
    max_retries = 3

    while captcha_count < max_retries:
        is_solved = solve_tiktok_captcha(page)

        if is_solved:
            print("[Solve Captcha] GIẢI THÀNH CÔNG")
            time.sleep(2)
            break
        else:
            print(
                f"[Solve Captcha] Giả lập thất bại hoặc cần thử lại. (Lần {captcha_count + 1}/{max_retries})")
            captcha_count += 1
            time.sleep(3)

            if captcha_count == max_retries:
                print(
                    "[Solve Captcha] Cảnh báo: Không thể giải Captcha sau nhiều lần thử.")


def extract_products_data(product_card, category_name):
    data = {
        "product_id": "N/A",
        "title": "N/A",
        "link": "N/A",
        "category": category_name,
        "label_trend": "Không",  # Nhãn: Xu hướng / Hàng Việt
        "label_marketing": "Không",  # Nhãn: Deal / Flash Sale
        "rating": "0",
        "sold": "0",
        "original_price": "0",
        "current_price": "0",
        "discount_percent": "0%",
        "update_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        # Tiêu đề sản phẩm và nhãn xu hướng / hàng Việt
        title_el = product_card.query_selector("h3")
        if title_el:
            data["title"] = title_el.inner_text().strip()
            img_labels = title_el.query_selector_all("img")
            for img in img_labels:
                src = img.get_attribute("src")
                if src:
                    if "6146a1d9caee4ae286fa92f8cbc0c449" in src:
                        data["label_trend"] = "Xu hướng"
                    elif "751625e8194f455cb1ce639b4f9dff2c" in src:
                        data["label_trend"] = "Hàng Việt"

        # Link sản phẩm & Product ID
        link_el = product_card.query_selector("a[href*='/pdp/']")
        if link_el:
            href = link_el.get_attribute("href")
            if href.startswith("/pdp/"):
                data["link"] = "https://www.tiktok.com" + href
            else:
                data["link"] = href

            # Lấy Product ID từ URL
            data["product_id"] = href.split('?')[0].rsplit('/')[-1]

        # Đánh giá sao
        rating_el = product_card.query_selector("span.P3-Semibold.mr-2")
        if rating_el:
            data["rating"] = rating_el.inner_text().strip()

        # Số sản phẩm đã bán
        sold_el = product_card.query_selector("span:has-text('sold')")
        if sold_el:
            data["sold"] = sold_el.inner_text().strip().replace(" sold", "")

        # Nhãn marketing (Deal / Flash Sale)
        if product_card.query_selector("span:has-text('Deal')"):
            data["label_marketing"] = "Deal"
        elif product_card.query_selector("span:has-text('Flash Sale')"):
            data["label_marketing"] = "Flash Sale"

        # Giá gốc, giá hiện tại và phần trăm giảm giá
        current_price_el = product_card.query_selector("span.H2-Semibold")
        if current_price_el:
            data["current_price"] = current_price_el.inner_text().strip()

        original_price_el = product_card.query_selector("span.line-through")
        if original_price_el:
            data["original_price"] = original_price_el.inner_text().strip()

        discount_el = product_card.query_selector(
            "span:has-text('-'):has-text('%')")
        if discount_el:
            data["discount_percent"] = discount_el.inner_text().strip()

    except Exception as e:
        print(f"[Extract Data]Lỗi khi trích xuất dữ liệu sản phẩm: {e}")

    return data


def scrape_tiktok_shop(url):
    user_data_dir = './tiktok_user_data'

    with sync_playwright() as p:
        print("[Scrape]Khởi động trình duyệt")

        args = [
            '--disable-blink-features=AutomationControlled',
            '--start-maximized',
            '--disable-infobars',
            '--no-sandbox'
        ]

        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=args,
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print("[Scrape]Đang truy cập trang TikTok Shop")
        page.goto(url)

        # Giải Captcha
        solve_captcha(page)
        time.sleep(2)

        try:
            page.locator(
                "div.flex-1.flex.justify-center").wait_for(timeout=10000)
        except:
            print("[Scrape] Không tìm thấy element chính")
            input("[Scrape] Nhấn Enter để tiếp tục...")

        category_elements = page.query_selector_all('a[href*="/c/"]')
        categories = []

        for cat in category_elements:
            url = cat.get_attribute('href')
            name = cat.inner_text().strip()

            if url:
                if url.startswith("/c/"):
                    full_url = "https://www.tiktok.com" + url
                else:
                    full_url = url
                categories.append({"name": name, "url": full_url})

        categories = list({v['url']: v for v in categories}.values())

        print(f"[Scrape] Tìm thấy {len(categories)} danh mục")
        print("-" * 100)

        for index, cat in enumerate(categories):
            print(
                f"[Scrape] ({index + 1}/{len(categories)}) Đang xử lý danh mục: {cat['name']}")

            try:
                page.goto(cat['url'])
                while True:
                    if page.locator("div:has-text('Verify to continue:')").count() > 0 or page.locator("#captcha-verify-image").count() > 0:
                        solve_captcha(page)
                        time.sleep(2)

                    else:
                        if page.locator('div.flex.justify-center.mt-16:has-text("No more products")').count() > 0:
                            print("[Scrape] Đã tải hết sản phẩm")
                            break

                        else:
                            page.get_by_role(
                                "button", name="View more").click(timeout=2000)
                            page.wait_for_timeout(2000)

                page.mouse.wheel(0, 800)

                product_cards = page.query_selector_all(
                    "div[class*='rounded']:has(a[href*='/pdp/'])")

                cat_products = []
                for card in product_cards:
                    data = extract_products_data(card, cat['name'])
                    if data["product_id"] != "N/A":
                        cat_products.append(data)

                print(
                    f"[Scrape] Danh mục '{cat['name']}' thu thập được {len(cat_products)} sản phẩm")
                print("-" * 50)

                if cat_products:
                    supabase.table('products').upsert(
                        cat_products, on_conflict="product_id").execute()
                    print(
                        f"[Scrape] Dữ liệu danh mục '{cat['name']}' đã được lưu vào Supabase")

            except Exception as e:
                print(f"[Scrape] Lỗi khi xử lý danh mục '{cat['name']}': {e}")

            time.sleep(2)

        print("-" * 100)
        print("[Scrape] Hoàn tất thu thập dữ liệu từ TikTok Shop")
        context.close()


if __name__ == "__main__":
    tiktok_shop_url = "https://www.tiktok.com/shop/vn"
    scrape_tiktok_shop(tiktok_shop_url)
