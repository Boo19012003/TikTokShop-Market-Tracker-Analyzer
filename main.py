from playwright.sync_api import sync_playwright
import time
import pandas as pd
import os


def extract_products_data(product_card, category_name):
    data = {
        "Product_ID": "N/A",
        "Title": "N/A",
        "Link": "N/A",
        "Category": category_name,
        "Label_Trend": "Không",    # Nhãn: Xu hướng / Hàng Việt
        "Label_Marketing": "Không",     # Nhãn: Deal / Flash Sale
        "Rating": "0",
        "Sold": "0",
        "Original_Price": "N/A",
        "Current_Price": "N/A",
        "Discount_Percent": "0%"
    }

    # Title và nhãn (xu hướng / hàng Việt)
    try:
        title_el = product_card.query_selector("h3")

        if title_el:
            data["Title"] = title_el.inner_text().strip()

            img_labels = title_el.query_selector_all("img")
            for img in img_labels:
                src = img.get_attribute("src")
                if src:
                    if "6146a1d9caee4ae286fa92f8cbc0c449" in src:
                        data["Label_Trend"] = "Xu hướng"
                        break
                    elif "751625e8194f455cb1ce639b4f9dff2c" in src:
                        data["Label_Trend"] = "Hàng Việt"
                        break
    except:
        pass
    # Link sản phẩm & Product ID
    try:
        link_el = product_card.query_selector("a[href*='/pdp/']")
        if link_el:
            href = link_el.get_attribute("href")

            if href.startswith("/pdp/"):
                data["Link"] = "https://www.tiktok.com" + href
            else:
                data["Link"] = href

            # Lấy Product ID từ URL
            Product_ID = href.split('?')[0].rsplit('/')[-1]
            data["Product_ID"] = Product_ID
    except:
        pass

    # Đánh giá sao
    try:
        rating_el = product_card.query_selector("span.P3-Semibold.mr-2")
        if rating_el:
            data["Rating"] = rating_el.inner_text().strip()
    except:
        pass

    # Số sản phẩm đã bán
    try:
        sold_el = product_card.query_selector("span:has-text('sold')")
        if sold_el:
            data["Sold"] = sold_el.inner_text().strip().replace(" sold", "")
    except:
        pass

    # Nhãn marketing (Deal / Flash Sale)
    try:
        if product_card.query_selector("span:has-text('Deal')"):
            data["Label_Marketing"] = "Deal"
        elif product_card.query_selector("span:has-text('Flash Sale')"):
            data["Label_Marketing"] = "Flash Sale"
    except:
        pass

    # Giá gốc, giá hiện tại và phần trăm giảm giá
    try:
        current_price_el = product_card.query_selector("span.H2-Semibold")
        if current_price_el:
            data["Current_Price"] = current_price_el.inner_text().strip()

        original_price_el = product_card.query_selector("span.line-through")
        if original_price_el:
            data["Original_Price"] = original_price_el.inner_text().strip()

        discount_el = product_card.query_selector(
            "span:has-text('-'):has-text('%')")
        if discount_el:
            data["Discount_Percent"] = discount_el.inner_text().strip()
    except:
        pass

    return data


def scrape_tiktok_shop(url):
    user_data_dir = './tiktok_user_data'

    with sync_playwright() as p:
        print("--- Khởi động trình duyệt ---")

        args = [
            '--disable-blink-features=AutomationControlled',
            '--start-maximized',
            '--disable-infobars',
        ]

        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=args,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print("--- Đang truy cập trang TikTok Shop ---")
        page.goto(url)

        try:
            page.locator(
                "div.flex-1.flex.justify-center").wait_for(timeout=10000)
        except:
            print("Không tìm thấy element chính")
            input("Nhấn Enter để tiếp tục...")

        category_elements = page.query_selector_all('a[href*="/c/"]')

        categories = []
        for cat in category_elements:
            url = cat.get_attribute('href')
            name = cat.inner_text().strip()

            if url:
                full_url = "https://www.tiktok.com" + \
                    url if url.startswith("/c/") else url
                categories.append({"name": name, "url": full_url})

        categories = list({v['url']: v for v in categories}.values())
        print(f"--- Tìm thấy {len(categories)} danh mục ---")
        print("-" * 50)

        for index, cat in enumerate(categories):
            print(
                f" --- ({index + 1}/{len(categories)}) Đang xử lý danh mục: {cat['name']} ---")

            try:
                page.goto(cat['url'])
                while True:
                    if page.locator("div.sc-iRbamj.gtaCnW.captcha_verify_bar--title:has-text('Verify to continue:')").count() > 0:
                        input(
                            "Nhấn Enter để tiếp tục sau khi đã giải quyết CAPTCHA...")

                    else:
                        if page.locator('div.flex.justify-center.mt-16:has-text("No more products")').count() > 0:
                            print("--- Đã tải hết sản phẩm ---")
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
                    cat_products.append(data)

                print(
                    f"--- Danh mục '{cat['name']}' thu thập được {len(cat_products)} sản phẩm ---")

                if cat_products:
                    df = pd.DataFrame(cat_products)
                    csv_file = "tiktok_shop_products.csv"

                    header_mode = not os.path.exists(csv_file)
                    df.to_csv(csv_file, mode='a', index=False,
                              header=header_mode, encoding='utf-8-sig')
                    print(
                        f"--- Dữ liệu sản phẩm đã được lưu vào '{csv_file}' ---")

            except Exception as e:
                print(f"Lỗi khi xử lý danh mục '{cat['name']}': {e}")

            time.sleep(2)

        print("-" * 50)
        print("--- Hoàn tất thu thập dữ liệu từ TikTok Shop ---")
        context.close()


if __name__ == "__main__":
    tiktok_shop_url = "https://www.tiktok.com/shop/vn"
    scrape_tiktok_shop(tiktok_shop_url)
