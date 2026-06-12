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
# Telegram
# ==========================================================

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
        print("TG msg error:", e)


def tg_send_photo(path, caption=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        return

    try:
        with open(path, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={
                    "chat_id": chat,
                    "caption": caption or ""
                },
                files={"photo": f},
                timeout=30
            )
    except Exception as e:
        print("TG photo error:", e)


# ==========================================================
# 工具
# ==========================================================

def screenshot(sb, name, send=False):
    try:
        path = f"{SCREENSHOT_DIR}/{int(time.time())}_{name}"
        sb.save_screenshot(path)
        print("📸", path)

        if send:
            tg_send_photo(path, caption=name)

        return path
    except:
        return None


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
# Linkvertise
# ==========================================================

def handle_linkvertise(sb):
    print("🔗 Linkvertise flow...")

    for i in range(80):

        try:
            current_url = sb.get_current_url()
        except:
            current_url = ""

        print("🌐", current_url)
        screenshot(sb, f"lv_{i}.png")

        click_by_text(sb, "button", "get link")
        click_by_text(sb, "div", "watch")
        click_by_text(sb, "button", "continue")
        click_by_text(sb, "button", "skip")
        click_by_text(sb, "span", "skip")

        # ⭐ success → open
        if "success" in current_url:
            print("✅ success 页面")

            if click_by_text(sb, "button", "open") or \
               click_by_text(sb, "a", "open"):

                print("🚀 已点击 Open")
                time.sleep(5)
                return True

        time.sleep(2)

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

        screenshot(sb, "login.png", send=True)

        sb.type(EMAIL_SEL, email)
        sb.type(PASS_SEL, password)
        sb.click(SUBMIT_SEL)

        for _ in range(30):
            if is_logged_in(sb):
                break
            time.sleep(1)
        else:
            screenshot(sb, "login_fail.png", send=True)
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
        screenshot(sb, "server_page.png", send=True)

        body = sb.get_text("body")

        if "Renew Limit Reached" in body:
            return "LIMIT"

        if not click_by_text(sb, "button", "renew"):
            screenshot(sb, "renew_fail.png", send=True)
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

        screenshot(sb, "linkvertise_start.png", send=True)

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