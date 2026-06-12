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
                return txt.replace("#", "")
    except:
        pass
    return None


# ==========================================================
# JS 注入（核心）
# ==========================================================

def inject_orihost_js(sb):
    try:
        with open("orihost.js", "r", encoding="utf-8") as f:
            js = f.read()

        sb.execute_script(js)
        print("✅ orihost.js 已注入")
    except Exception as e:
        print("❌ JS 注入失败:", e)


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

        # 等待登录
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

        print("🎮 Server:", server_id)

        server_url = f"https://panel.orihost.com/server/{server_id}"

        # =========================
        # 3. 打开 Server 页面
        # =========================
        sb.open(server_url)

        sb.wait_for_element("body", timeout=30)
        time.sleep(6)

        body = sb.get_text("body")

        # =========================
        # 4. 页面错误处理
        # =========================
        if "Something went wrong" in body:

            print("⚠️ 页面异常，重新加载...")

            sb.open(server_url)
            time.sleep(8)

            body = sb.get_text("body")

            if "Something went wrong" in body:
                return "PAGE_ERROR"

        # =========================
        # 5. 检查登录状态是否丢失
        # =========================
        if "login" in sb.get_current_url().lower():
            return "LOGIN_EXPIRED"

        # =========================
        # 6. 等待 UI 加载
        # =========================
        sb.wait_for_element("body", timeout=30)
        time.sleep(3)

        # =========================
        # 7. 等待 Renew 按钮出现
        # =========================
        renew_btn_ok = False

        for _ in range(25):
            try:
                if sb.is_element_visible('button:contains("Renew")'):
                    renew_btn_ok = True
                    break
            except:
                pass
            time.sleep(1)

        if not renew_btn_ok:
            return "NO_RENEW_BTN"

        # =========================
        # 8. 点击 Renew
        # =========================
        sb.click('button:contains("Renew")')
        time.sleep(3)

        # =========================
        # 9. 打开 Linkvertise
        # =========================
        try:
            sb.click('button:contains("Open Linkvertise")')
        except:
            pass

        time.sleep(5)

        # =========================
        # 10. 切换窗口
        # =========================
        handles = safe_window_handles(sb)

        if len(handles) > 1:

            try:
                sb.switch_to_window(1)
            except:
                return "BROWSER_CRASH"

            # =========================
            # 🚀 注入 JS（接管 Linkvertise）
            # =========================
            inject_orihost_js(sb)

            print("🚀 Linkvertise 已交给 JS 自动处理")

            # 给 JS 足够运行时间
            time.sleep(180)

        # =========================
        # 11. 回主页面
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