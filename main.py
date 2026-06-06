# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright
import time
import os

LOGIN_URL = "https://panel.orihost.com/auth/login"

EMAIL = os.getenv("ORIHOST_EMAIL")
PASSWORD = os.getenv("ORIHOST_PASSWORD")


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context()
        page = context.new_page()

        print("🌍 打开登录页")
        page.goto(LOGIN_URL)

        page.fill('input[name="username"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')

        page.wait_for_timeout(5000)

        print("✅ 登录完成")

        # 等 server 列表出来
        page.wait_for_selector("text=Manage Server", timeout=15000)

        print("🎯 点击 Manage Server（关键）")

        # ⭐ 关键点：点按钮，不点整个卡片
        buttons = page.locator("text=Manage Server")

        if buttons.count() == 0:
            print("❌ 没找到按钮")
            return

        # 点击第一个
        buttons.nth(0).click(force=True)

        # 等 SPA 渲染
        page.wait_for_timeout(8000)

        content = page.content()

        if "Something went wrong" in content:
            print("❌ 页面仍然错误")
            return

        print("✅ 成功进入服务器页面")

        # 👉 找 Renew
        try:
            page.click('text=Renew', timeout=5000)
            print("✅ 点击 Renew")
        except:
            print("❌ 没找到 Renew 按钮")

        time.sleep(5)

        browser.close()


if __name__ == "__main__":
    run()