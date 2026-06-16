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
            json={"chat_id": chat, "text": msg},
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
                return txt.replace("#", "").strip()
    except:
        pass
    return None


# ==========================================================
# 💀 点击（通用 + iframe）
# ==========================================================

def click_by_text_ultimate(sb, keyword, timeout=30):

    print(f"🔍 点击: {keyword}")

    for _ in range(timeout):
        try:
            result = sb.execute_async_script(f"""
                var callback = arguments[arguments.length - 1];

                function clickDeep(doc) {{

                    const all = doc.querySelectorAll('*');

                    for (const el of all) {{

                        if (!el.innerText) continue;

                        if (el.innerText.toLowerCase().includes("{keyword.lower()}")) {{

                            el.scrollIntoView({{block:'center'}});

                            el.dispatchEvent(new MouseEvent('click', {{
                                bubbles: true,
                                cancelable: true,
                                view: window
                            }}));

                            return true;
                        }}
                    }}

                    const iframes = doc.querySelectorAll('iframe');

                    for (const iframe of iframes) {{
                        try {{
                            const sub = iframe.contentDocument || iframe.contentWindow.document;
                            if (sub && clickDeep(sub)) return true;
                        }} catch(e) {{}}
                    }}

                    return false;
                }}

                try {{
                    callback(clickDeep(document));
                }} catch(e) {{
                    callback(false);
                }}
            """)

            if result:
                print(f"✅ 点击成功: {keyword}")
                return True

        except Exception as e:
            print("err:", e)

        time.sleep(1)

    return False


# ==========================================================
# 🚀 Linkvertise JS（你的原版）
# ==========================================================

def inject_linkvertise_script(sb):

    print("🚀 注入 Linkvertise 脚本")

    sb.execute_script(r"""
    (function () {

        function visible(el) {
            return el && el.offsetParent !== null;
        }

        function findByText(tag, text) {
            const els = document.querySelectorAll(tag);
            for (const el of els) {
                if (el.textContent && el.textContent.includes(text)) {
                    return el;
                }
            }
            return null;
        }

        setInterval(() => {

            const url = location.href;

            if (url.includes('linkvertise.com')) {

                // Step 1
                const getLinkLink = document
                    .querySelector('[dusk="fullsize-get-content-btn"]')
                    ?.closest('a');

                if (getLinkLink && !window.getLinkClicked) {
                    window.getLinkClicked = true;
                    location.href = getLinkLink.href;
                }

                // Step 2
                if (url.includes('/access/')) {

                    const wrappers = document.querySelectorAll(
                        '[dusk="lv-membership-plan-option-wrapper-btn"]'
                    );

                    let watchAdsBtn = null;

                    for (const wrapper of wrappers) {
                        if (wrapper.textContent &&
                            wrapper.textContent.includes('Watch Ads')) {
                            watchAdsBtn = wrapper;
                            break;
                        }
                    }

                    const waitText =
                        findByText('div', 'Wait') ||
                        findByText('span', 'Wait');

                    if (watchAdsBtn) {

                        const priceBox =
                            watchAdsBtn.closest('.membership-plan-option');

                        if (priceBox) {

                            if (!priceBox.classList.contains('active')) {
                                watchAdsBtn.click();
                            } else {

                                const continueBtn =
                                    findByText('button', 'Continue');

                                if (visible(continueBtn) &&
                                    !window.continueClicked) {

                                    window.continueClicked = true;
                                    continueBtn.click();
                                }
                            }
                        }

                    } else if (waitText) {

                        if (!window.waitTimerStarted) {

                            window.waitTimerStarted = true;

                            setTimeout(() => {
                                location.reload();
                            }, 5 * 60 * 1000);
                        }
                    }
                }

                // Step 3
                const skipAdBtn =
                    findByText('span', 'Skip Ad') ||
                    findByText('button', 'Skip Ad');

                if (visible(skipAdBtn)) {

                    if (!window.lastSkipClick ||
                        Date.now() - window.lastSkipClick > 3000) {

                        skipAdBtn.click();
                        window.lastSkipClick = Date.now();
                    }
                }

                // Step 4
                if (url.includes('/success')) {

                    const lvButtons =
                        document.querySelectorAll('[data-testid="lv-button"]');

                    let openBtn = null;

                    for (const btn of lvButtons) {
                        if (btn.textContent &&
                            btn.textContent.includes('Open')) {
                            openBtn = btn;
                            break;
                        }
                    }

                    if (visible(openBtn) && !window.openClicked) {

                        window.openClicked = true;

                        setTimeout(() => {

                            openBtn.click();

                            setTimeout(() => {
                                window.close();
                            }, 1500);

                        }, 1500);
                    }
                }
            }

        }, 2000);

    })();
    """)


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

        print("🎮 Server:", server_id)

        sb.open(f"https://panel.orihost.com/server/{server_id}")

        time.sleep(10)
        screenshot(sb, "server_page.png")

        # 1️⃣ 点击 Renew
        if not click_by_text_ultimate(sb, "renew"):
            screenshot(sb, "renew_fail.png")
            return "NO_RENEW_BTN"

        time.sleep(5)

        # 2️⃣ 点击 Open Linkvertise（弹窗）
        if not click_by_text_ultimate(sb, "open linkvertise"):
            screenshot(sb, "open_lv_fail.png")
            return "NO_OPEN_LINKVERTISE"

        time.sleep(5)

        # 3️⃣ 切换新窗口
        handles = sb.driver.window_handles
        if len(handles) > 1:
            sb.switch_to_window(handles[-1])

        screenshot(sb, "linkvertise_start.png")

        # 4️⃣ 注入自动脚本
        inject_linkvertise_script(sb)

        time.sleep(120)

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