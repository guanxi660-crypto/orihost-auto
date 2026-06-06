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
    except:
        pass


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
# ⭐ 防 crash
# ==========================================================

def is_driver_alive(sb):
    try:
        _ = sb.driver.current_url
        return True
    except:
        return False


def safe_window_handles(sb):
    try:
        return sb.driver.window_handles
    except:
        return []


# ==========================================================
# 点击 server（安全版）
# ==========================================================

def open_server_via_click(sb, server_id):
    print("👉 尝试点击进入服务器")

    for i in range(3):
        try:
            sb.open(HOME_URL)
            time.sleep(5)

            spans = sb.find_elements("span.text-neutral-500")

            for s in spans:
                if server_id in s.text:
                    print("✅ 找到 server，点击进入")

                    try:
                        s.click()
                    except:
                        sb.driver.execute_script("arguments[0].click();", s)

                    time.sleep(5)

                    # ⭐ 检查浏览器是否还活着
                    if not is_driver_alive(sb):
                        print("💥 浏览器已崩溃")
                        return False

                    return True

        except Exception as e:
            print("click server error:", e)

        time.sleep(3)

    return False


# ==========================================================
# 页面检测
# ==========================================================

def ensure_server_ok(sb):
    for i in range(3):
        try:
            body = sb.get_text("body")

            if "Something went wrong" in body:
                print(f"⚠️ 页面异常，刷新 {i+1}")
                sb.refresh()
                time.sleep(5)
            else:
                return True
        except:
            return False

    return False


# ==========================================================
# Linkvertise
# ==========================================================

def handle_linkvertise(sb):
    print("🔗 Linkvertise flow...")

    for _ in range(40):
        if not is_driver_alive(sb):
            return False

        try:
            if sb.is_element_visible('button:contains("Get Link")'):
                sb.click('button:contains("Get Link")')
        except:
            pass

        try:
            if sb.is_element_visible('div:contains("Watch Ads")'):
                sb.click('div:contains("Watch Ads")')
        except:
            pass

        try:
            if sb.is_element_visible('button:contains("Continue")'):
                sb.click('button:contains("Continue")')
        except:
            pass

        try:
            if sb.is_element_visible('span:contains("Skip Ad")'):
                sb.click('span:contains("Skip Ad")')
        except:
            pass

        time.sleep(3)

    return True


# ==========================================================
# 主流程（单次）
# ==========================================================

def run_once():

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

        print("🌍 打开登录页")
        sb.open(LOGIN_URL)
        time.sleep(5)

        sb.type(EMAIL_SEL, email)
        sb.type(PASS_SEL, password)
        sb.click(SUBMIT_SEL)

        time.sleep(5)

        for _ in range(30):
            if is_logged_in(sb):
                break
            time.sleep(1)
        else:
            return "LOGIN_FAIL"

        print("✅ 登录成功")

        server_id = extract_server_id(sb)

        if not server_id:
            return "NO_SERVER"

        print("🎮 Server:", server_id)

        if not open_server_via_click(sb, server_id):
            return "BROWSER_CRASH"

        if not ensure_server_ok(sb):
            return "SERVER_LOAD_FAIL"

        try:
            sb.click('button:contains("Renew")')
        except:
            return "NO_RENEW_BTN"

        try:
            sb.click('button:contains("Open Linkvertise")')
        except:
            pass

        time.sleep(5)

        handles = safe_window_handles(sb)

        if len(handles) > 1:
            sb.switch_to_window(1)

        handle_linkvertise(sb)

        return "OK"


# ==========================================================
# ⭐ 总控（自动重试）
# ==========================================================

def run():
    for i in range(3):
        print(f"🚀 尝试运行 {i+1}/3")

        result = run_once()

        if result == "OK":
            return result

        if result == "BROWSER_CRASH":
            print("♻️ 浏览器崩溃，重试...")
            time.sleep(5)
            continue

        return result

    return "FAILED_AFTER_RETRY"


# ==========================================================
# MAIN
# ==========================================================

def main():
    result = run()

    report = f"""
📊 *Orihost 自动续期报告*

状态: `{result}`

时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    print(report)
    tg_send(report)


if __name__ == "__main__":
    main()