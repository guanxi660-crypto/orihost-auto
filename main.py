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
# 💀 通用点击（含 iframe）
# ==========================================================

def click_by_text_ultimate(sb, keyword, timeout=20):

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
                            el.click();
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
# 🎯 专杀 Open Linkvertise（关键修复）
# ==========================================================

def click_open_linkvertise(sb):

    print("🎯 点击弹窗 Open Linkvertise")

    for _ in range(20):
        try:
            result = sb.execute_script("""
                const dialogs = document.querySelectorAll('[role="dialog"]');

                for (const dialog of dialogs) {

                    const buttons = dialog.querySelectorAll('button');

                    if (buttons.length >= 2) {

                        const btn = buttons[buttons.length - 1];

                        if (btn.innerText.toLowerCase().includes('open')) {
                            btn.click();
                            return true;
                        }
                    }
                }

                return false;
            """)

            if result:
                print("✅ 已点击 Open Linkvertise")
                return True

        except Exception as e:
            print("err:", e)

        time.sleep(1)

    return False


# ==========================================================
# 🚀 Linkvertise 自动脚本（你的完整版）
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

                const getLinkLink = document
                    .querySelector('[dusk="fullsize-get-content-btn"]')
                    ?.closest('a');

                if (getLinkLink && !window.getLinkClicked) {
                    window.getLinkClicked = true;
                    location.href = getLinkLink.href;
                }

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

    with SB(uc=True, headless=True, xvfb=True, incognito=True) as sb:

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

        print("✅ 登录成功")

        time.sleep(3)

        server_id = extract_server_id(sb)
        print("🎮 Server:", server_id)

        sb.open(f"https://panel.orihost.com/server/{server_id}")
        time.sleep(8)

        screenshot(sb, "server_page.png")

        # 1️⃣ Renew
        click_by_text_ultimate(sb, "renew")

        time.sleep(3)

        # 2️⃣ 点弹窗按钮（关键）
        if not click_open_linkvertise(sb):
            screenshot(sb, "open_lv_fail.png")
            return "NO_OPEN_LINKVERTISE"

        time.sleep(5)

        # 3️⃣ 切新窗口
        handles = sb.driver.window_handles
        if len(handles) > 1:
            sb.switch_to_window(handles[-1])

        screenshot(sb, "linkvertise.png")

        # 4️⃣ 注入脚本
        inject_linkvertise_script(sb)

        time.sleep(120)

        return "OK"


def main():
    result = run()

    print(f"""
📊 Orihost 自动续期报告

状态: {result}
时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
""")


if __name__ == "__main__":
    main()