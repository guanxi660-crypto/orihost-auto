# -*- coding: utf-8 -*-

import os
import time
import random
import re
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


def is_cf(sb):
    try:
        body = sb.get_text("body").lower()
        return "checking your browser" in body or "just a moment" in body
    except:
        return False


def wait_cf(sb, timeout=120):
    start = time.time()

    while time.time() - start < timeout:
        if not is_cf(sb):
            return True

        try:
            sb.uc_gui_click_captcha()
        except:
            pass

        time.sleep(5)

    return False


def is_logged_in(sb):
    try:
        text = sb.get_text("body")
        return "Welcome back" in text
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

    for _ in range(60):

        url = sb.get_current_url()

        # Get Link
        try:
            if sb.is_element_visible('button:contains("Get Link")'):
                sb.click('button:contains("Get Link")')
                time.sleep(3)
        except:
            pass

        # Watch Ads
        try:
            if sb.is_element_visible('div:contains("Watch Ads")'):
                sb.click('div:contains("Watch Ads")')
                time.sleep(2)
        except:
            pass

        # Continue
        try:
            if sb.is_element_visible('button:contains("Continue")'):
                sb.click('button:contains("Continue")')
                time.sleep(3)
        except:
            pass

        # Skip Ad
        try:
            if sb.is_element_visible('span:contains("Skip Ad")'):
                sb.click('span:contains("Skip Ad")')
                time.sleep(2)
        except:
            pass

        # success -> Open
        try:
            if "/success" in url:
                if sb.is_element_visible('button:contains("Open")'):
                    sb.click('button:contains("Open")')
                    time.sleep(3)
                    break
        except:
            pass

        time.sleep(3)


# ==========================================================
# 主流程
# ==========================================================

def run():

    email = os.getenv("ORIHOST_EMAIL")
    password = os.getenv("ORIHOST_PASSWORD")

    with SB(uc=True, test=True, locale="en") as sb:

        print("🌍 打开登录页")
        sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=5)
        time.sleep(5)

        # Cloudflare
        if is_cf(sb):
            print("🛡️ CF验证")
            if not wait_cf(sb):
                return "CF_FAIL"

        screenshot(sb, "login.png")

        # 输入账号
        sb.type(EMAIL_SEL, email)
        sb.type(PASS_SEL, password)

        sb.click(SUBMIT_SEL)

        time.sleep(5)

        # 登录验证
        for _ in range(30):
            if is_logged_in(sb):
                break
            time.sleep(1)
        else:
            screenshot(sb, "login_fail.png")
            return "LOGIN_FAIL"

        print("✅ 登录成功")

        # 获取服务器ID
        time.sleep(3)
        server_id = extract_server_id(sb)

        if not server_id:
            return "NO_SERVER"

        print("🎮 Server:", server_id)

        server_url = f"https://panel.orihost.com/server/{server_id}"
        sb.open(server_url)

        time.sleep(5)

        # Renew Limit 检测
        if "Renew Limit Reached" in sb.get_text("body"):
            return "LIMIT"

        # 点击 Renew
        try:
            sb.click('button:contains("Renew")')
            time.sleep(3)
        except:
            screenshot(sb, "renew_fail.png")
            return "NO_RENEW_BTN"

        # 弹窗 → Open Linkvertise
        try:
            sb.click('button:contains("Open Linkvertise")')
        except:
            pass

        time.sleep(5)

        # 切换窗口
        if len(sb.driver.window_handles) > 1:
            sb.switch_to_window(1)

        handle_linkvertise(sb)

        # 回到主页面
        sb.switch_to_window(0)
        sb.open(HOME_URL)

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
"""

    print(report)
    tg_send(report)


if __name__ == "__main__":
    main()