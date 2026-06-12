# -*- coding: utf-8 -*-

import os
import time
import requests
from seleniumbase import SB


LOGIN_URL = "https://panel.orihost.com/auth/login"
HOME_URL = "https://panel.orihost.com/"

EMAIL_SEL = 'input[name="username"]'
PASS_SEL = 'input[name="password"]'
SUBMIT_SEL = 'button[type="submit"]'

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ==========================================================
# 工具
# ==========================================================

def screenshot(sb, name):
    try:
        sb.save_screenshot(f"{SCREENSHOT_DIR}/{name}")
    except:
        pass


def tg_send(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat,
                "text": msg,
                "parse_mode": "Markdown"
            },
            timeout=20
        )
    except Exception as e:
        print("TG error:", e)


def safe_window_handles(sb):
    try:
        return sb.driver.window_handles
    except:
        return []


def is_logged_in(sb):
    try:
        return "Welcome back" in sb.get_text("body")
    except:
        return False


def extract_server_id(sb):
    try:
        spans = sb.find_elements("span.text-neutral-500")
        for s in spans:
            txt = s.text.strip()
            if txt.startswith("#"):
                return txt.replace("#", "").strip()
    except:
        pass
    return None


# ==========================================================
# JS 注入
# ==========================================================

def inject_orihost_js(sb):
    try:
        with open("orihost.js", "r", encoding="utf-8") as f:
            js = f.read()

        sb.execute_script(js)
        print("✅ JS 已注入")
    except Exception as e:
        print("❌ JS 注入失败:", e)


# ==========================================================
# 页面是否异常
# ==========================================================

def is_page_error(sb):
    try:
        body = sb.get_text("body")
        return "Something went wrong" in body
    except:
        return True


# ==========================================================
# 主流程
# ==========================================================

def run():

    email = os.getenv("ORIHOST_EMAIL")
    password = os.getenv("ORIHOST_PASSWORD")

    with SB(
        uc=True,
        test=True,
        locale="en",
        headless=True,
        xvfb=True,
        incognito=True,
        chromium_arg="--no-sandbox,--disable-dev-shm-usage,--disable-gpu"
    ) as sb:

        # =========================
        # 1. 登录
        # =========================
        print("🌍 打开登录页")
        sb.open(LOGIN_URL)
        time.sleep(5)

        screenshot(sb, "login.png")

        sb.type(EMAIL_SEL, email)
        sb.type(PASS_SEL, password)
        sb.click(SUBMIT_SEL)

        for _ in range(30):
            if is_logged_in(sb):
                break
            time.sleep(1)
        else:
            screenshot(sb, "login_fail.png")
            return "LOGIN_FAIL"

        print("✅ 登录成功")

        # =========================
        # 2. 获取 Server ID
        # =========================
        time.sleep(3)
        server_id = extract_server_id(sb)

        if not server_id:
            return "NO_SERVER"

        server_id = server_id.strip()  # 🔥 关键修复

        print("🎮 Server:", server_id)

        server_url = f"https://panel.orihost.com/server/{server_id.strip()}"

        # =========================
        # 3. 打开 Server 页面（带重试）
        # =========================
        for attempt in range(3):

            print(f"🌐 打开服务器页 (尝试 {attempt+1})")
            sb.open(server_url)

            sb.wait_for_element("body", timeout=30)
            time.sleep(8)

            if not is_page_error(sb):
                break

            print("⚠️ 页面异常，重试中...")
            time.sleep(3)

        else:
            screenshot(sb, "page_error.png")
            return "PAGE_ERROR"

        # =========================
        # 4. 登录失效检测
        # =========================
        if "login" in sb.get_current_url().lower():
            return "LOGIN_EXPIRED"

        # =========================
        # 5. 等待 Renew 按钮
        # =========================
        renew_btn_ok = False

        for _ in range(25):
            try:
                buttons = sb.find_elements("button")
                for b in buttons:
                    if "Renew" in b.text:
                        renew_btn_ok = True
                        b.click()
                        break
                if renew_btn_ok:
                    break
            except:
                pass
            time.sleep(1)

        if not renew_btn_ok:
            return "NO_RENEW_BTN"

        time.sleep(3)

        # =========================
        # 6. 打开 Linkvertise
        # =========================
        try:
            buttons = sb.find_elements("button")
            for b in buttons:
                if "Linkvertise" in b.text:
                    b.click()
                    break
        except:
            pass

        time.sleep(5)

        # =========================
        # 7. 切换窗口
        # =========================
        handles = safe_window_handles(sb)

        if len(handles) > 1:
            try:
                sb.switch_to_window(1)
            except:
                return "BROWSER_CRASH"

            inject_orihost_js(sb)

            print("🚀 JS 接管 Linkvertise")
            time.sleep(180)

        # =========================
        # 8. 回主页面
        # =========================
        try:
            sb.switch_to_window(0)
            sb.open(HOME_URL)
        except:
            return "BROWSER_CRASH"

        time.sleep(5)

        return "OK"


# ==========================================================
# MAIN
# ==========================================================

def main():
    result = run()

    report = f"""
📊 *Orihost 自动续期报告*

状态: `{result}`

时间: {time.strftime("%Y-%m-%d %H:%M:%S")}

说明:
OK = 成功续期
LIMIT = 达到续期上限
LOGIN_FAIL = 登录失败
BROWSER_CRASH = 浏览器崩溃
"""

    print(report)
    tg_send(report)


if __name__ == "__main__":
    main()