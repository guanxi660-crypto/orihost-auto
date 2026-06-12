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
        path = f"{SCREENSHOT_DIR}/{int(time.time())}_{name}"
        sb.save_screenshot(path)
        print("📸", path)
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
# 通用点击
# ==========================================================

def click_by_text(sb, tag, keyword):
    try:
        els = sb.find_elements(tag)
        for e in els:
            if keyword.lower() in e.text.lower():
                e.click()
                print(f"🖱 点击: {keyword}")
                return True
    except:
        pass
    return False


# ==========================================================
# Linkvertise（完整版）
# ==========================================================

def handle_linkvertise(sb):
    print("🔗 Linkvertise flow...")

    for i in range(80):

        current_url = ""
        try:
            current_url = sb.get_current_url()
        except:
            pass

        print("🌐", current_url)

        screenshot(sb, f"lv_{i}.png")

        # ---------------------------
        # Get Link
        # ---------------------------
        click_by_text(sb, "button", "get link")

        # ---------------------------
        # Watch Ads / Continue
        # ---------------------------
        click_by_text(sb, "div", "watch")
        click_by_text(sb, "button", "continue")

        # ---------------------------
        # Skip Ad
        # ---------------------------
        click_by_text(sb, "button", "skip")
        click_by_text(sb, "span", "skip")

        # ---------------------------
        # SUCCESS → ⭐ 关键补充
        # ---------------------------
        if "success" in current_url:

            print("✅ 进入 success 页面")

            if click_by_text(sb, "button", "open") or \
               click_by_text(sb, "a", "open"):

                print("🚀 已点击 Open，流程完成")
                time.sleep(5)
                return True

        time.sleep(2)

    print("❌ Linkvertise 超时")
    return False


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

        time.sleep(3)
        server_id = extract_server_id(sb)

        if not server_id:
            return "NO_SERVER"

        print("🎮 Server:", server_id)

        server_url = f"https://panel.orihost.com/server/{server_id}"
        sb.open(server_url)

        time.sleep(8)
        screenshot(sb, "server_page.png")

        if "Renew Limit Reached" in sb.get_text("body"):
            return "LIMIT"

        if not click_by_text(sb, "button", "renew"):
            screenshot(sb, "renew_fail.png")
            return "NO_RENEW_BTN"

        time.sleep(3)

        click_by_text(sb, "button", "linkvertise")

        time.sleep(5)

        handles = safe_window_handles(sb)

        if len(handles) > 1:
            try:
                sb.switch_to_window(1)
            except:
                return "BROWSER_CRASH"

        screenshot(sb, "linkvertise_start.png")

        handle_linkvertise(sb)

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
"""

    print(report)
    tg_send(report)


if __name__ == "__main__":
    main()