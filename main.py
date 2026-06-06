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
# Linkvertise 自动流程
# ==========================================================

def handle_linkvertise(sb):
    print("🔗 Linkvertise flow...")

    for _ in range(40):
        try:
            if sb.is_element_visible('button:contains("Get Link")'):
                sb.click('button:contains("Get Link")')
                time.sleep(3)
        except:
            pass

        try:
            if sb.is_element_visible('div:contains("Watch Ads")'):
                sb.click('div:contains("Watch Ads")')
                time.sleep(2)
        except:
            pass

        try:
            if sb.is_element_visible('button:contains("Continue")'):
                sb.click('button:contains("Continue")')
                time.sleep(3)
        except:
            pass

        try:
            if sb.is_element_visible('span:contains("Skip Ad")'):
                sb.click('span:contains("Skip Ad")')
                time.sleep(2)
        except:
            pass

        time.sleep(3)


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
        disable_gpu=True,
        no_sandbox=True,
        disable_dev_shm_usage=True,
    ) as sb:

        print("🌍 打开登录页")
        sb.open(LOGIN_URL)
        time.sleep(5)

        screenshot(sb, "login.png")

        sb.type(EMAIL_SEL, email)
        sb.type(PASS_SEL, password)
        sb.click(SUBMIT_SEL)

        time.sleep(5)

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
        time.sleep(5)

        if "Renew Limit Reached" in sb.get_text("body"):
            return "LIMIT"

        try:
            sb.click('button:contains("Renew")')
            time.sleep(3)
        except:
            screenshot(sb, "renew_fail.png")
            return "NO_RENEW_BTN"

        try:
            sb.click('button:contains("Open Linkvertise")')
        except:
            pass

        time.sleep(5)

        # ✅ 安全切换窗口
        handles = safe_window_handles(sb)

        if len(handles) > 1:
            try:
                sb.switch_to_window(1)
            except:
                return "BROWSER_CRASH"

        handle_linkvertise(sb)

        # 回主页面
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
CF_FAIL = CF验证失败
BROWSER_CRASH = 浏览器崩溃
"""

    print(report)
    tg_send(report)


if __name__ == "__main__":
    main()