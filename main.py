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
# 关键修复：关闭弹窗
# ==========================================================

def close_popups(sb):
    try:
        sb.execute_script("""
            const selectors = [
                '[aria-label="Close"]',
                '.modal button',
                '.popup button',
                'button[aria-label="close"]'
            ];

            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(btn => {
                    if (btn.innerText.toLowerCase().includes('close') || btn.innerHTML.includes('×')) {
                        btn.click();
                    }
                });
            });
        """)
    except:
        pass


# ==========================================================
# 强力点击（修复 Renew）
# ==========================================================

def force_click(sb, keyword):
    try:
        sb.execute_script(f"""
            const els = [...document.querySelectorAll('button, a')];

            for (const el of els) {{
                if (el.innerText && el.innerText.toLowerCase().includes('{keyword.lower()}')) {{
                    el.scrollIntoView({{block:'center'}});
                    el.click();
                    return true;
                }}
            }}
            return false;
        """)
        return True
    except:
        return False


# ==========================================================
# Linkvertise（JS注入版）
# ==========================================================

def inject_linkvertise_script(sb):
    print("🚀 注入 Linkvertise 自动脚本")

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

            // ====================================================
            // Linkvertise 页面
            // ====================================================

            if (url.includes('linkvertise.com')) {

                // Step 1: Get Link
                const getLinkLink = document
                    .querySelector('[dusk="fullsize-get-content-btn"]')
                    ?.closest('a');

                if (getLinkLink && !window.getLinkClicked) {
                    window.getLinkClicked = true;
                    console.log('[Auto] Get Link');
                    location.href = getLinkLink.href;
                }

                // Step 2: Watch Ads
                if (url.includes('/access/')) {

                    const wrappers = document.querySelectorAll(
                        '[dusk="lv-membership-plan-option-wrapper-btn"]'
                    );

                    let watchAdsBtn = null;

                    for (const wrapper of wrappers) {
                        if (wrapper.textContent?.includes('Watch Ads')) {
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
                                console.log('[Auto] 选择 Watch Ads');
                                watchAdsBtn.click();
                            } else {
                                const continueBtn =
                                    findByText('button', 'Continue');

                                if (visible(continueBtn) && !window.continueClicked) {
                                    window.continueClicked = true;
                                    console.log('[Auto] Continue');
                                    continueBtn.click();
                                }
                            }
                        }

                    } else if (waitText) {

                        if (!window.waitTimerStarted) {
                            window.waitTimerStarted = true;

                            console.log('[Auto] Wait detected');

                            setTimeout(() => {
                                location.reload();
                            }, 5 * 60 * 1000);
                        }
                    }
                }

                // Step 3: Skip Ad
                const skipAdBtn =
                    findByText('span', 'Skip Ad') ||
                    findByText('button', 'Skip Ad');

                if (visible(skipAdBtn)) {

                    if (!window.lastSkipClick || Date.now() - window.lastSkipClick > 3000) {
                        console.log('[Auto] Skip Ad');
                        skipAdBtn.click();
                        window.lastSkipClick = Date.now();
                    }
                }

                // Step 4: Success
                if (url.includes('/success')) {

                    const lvButtons =
                        document.querySelectorAll('[data-testid="lv-button"]');

                    let openBtn = null;

                    for (const btn of lvButtons) {
                        if (btn.textContent?.includes('Open')) {
                            openBtn = btn;
                            break;
                        }
                    }

                    if (visible(openBtn) && !window.openClicked) {
                        window.openClicked = true;

                        console.log('[Auto] Open');

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

        close_popups(sb)

        if "Renew Limit Reached" in sb.get_text("body"):
            return "LIMIT"

        # 🔥 强力点击 Renew（修复点）
        if not force_click(sb, "renew"):
            screenshot(sb, "renew_fail.png")
            return "NO_RENEW_BTN"

        print("🔁 点击 Renew 成功")

        time.sleep(5)

        force_click(sb, "linkvertise")

        time.sleep(5)

        handles = safe_window_handles(sb)

        if len(handles) > 1:
            sb.switch_to_window(1)

        screenshot(sb, "linkvertise_start.png")

        # 🚀 注入自动脚本
        inject_linkvertise_script(sb)

        # 等待自动跑
        time.sleep(120)

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