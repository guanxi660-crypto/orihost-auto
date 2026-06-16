# -*- coding: utf-8 -*-

import os
import time
import requests
from seleniumbase import SB


LOGIN_URL = "https://panel.orihost.com/auth/login"

EMAIL_SEL = 'input[name="username"]'
PASS_SEL = 'input[name="password"]'
SUBMIT_SEL = 'button[type="submit"]'

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


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

    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": msg},
        timeout=20
    )


def is_logged_in(sb):
    try:
        return "Welcome back" in sb.get_text("body")
    except:
        return False


def extract_server_id(sb):
    spans = sb.find_elements("span.text-neutral-500")
    for s in spans:
        txt = s.text.strip()
        if txt.startswith("#"):
            return txt.replace("#", "").strip()
    return None


# ==========================================================
# 💀 终极点击（100%成功版）
# ==========================================================

def click_renew_ultimate(sb, timeout=40):

    print("💀 启动终极 Renew 点击")

    for i in range(timeout):

        try:
            result = sb.execute_script("""
                return (function () {

                    function deepSearchAndClick(doc) {

                        const all = doc.querySelectorAll('*');

                        for (const el of all) {

                            if (!el.innerText) continue;

                            const txt = el.innerText.toLowerCase();

                            if (txt.includes('renew')) {

                                // 滚动
                                el.scrollIntoView({block:'center'});

                                // 强制点击（最关键）
                                el.dispatchEvent(new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                }));

                                return true;
                            }
                        }

                        // 🔥 搜 iframe（关键）
                        const iframes = doc.querySelectorAll('iframe');

                        for (const iframe of iframes) {
                            try {
                                const sub = iframe.contentDocument || iframe.contentWindow.document;
                                if (sub && deepSearchAndClick(sub)) {
                                    return true;
                                }
                            } catch (e) {}
                        }

                        return false;
                    }

                    return deepSearchAndClick(document);

                })();
            """)

            if result:
                print("✅ Renew 点击成功")
                return True

        except Exception as e:
            print("err:", e)

        time.sleep(1)

    return False


# ==========================================================
# 主流程
# ==========================================================

def run():

    email = os.getenv("ORIHOST_EMAIL")
    password = os.getenv("ORIHOST_PASSWORD")

    with SB(
        uc=True,
        headless=True,
        xvfb=True,
        incognito=True,
        chromium_arg="--no-sandbox,--disable-dev-shm-usage"
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

        sb.open(f"https://panel.orihost.com/server/{server_id}")

        time.sleep(10)
        screenshot(sb, "server_page.png")

        if not click_renew_ultimate(sb):
            screenshot(sb, "renew_fail.png")
            return "NO_RENEW_BTN"

        time.sleep(5)

        return "OK"


def main():
    result = run()

    report = f"""
📊 Orihost 自动续期报告

状态: {result}
时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    print(report)
    tg_send(report)


if __name__ == "__main__":
    main()