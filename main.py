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
# 🔥 终极：清除所有弹窗/广告/遮挡层
# ==========================================================

def nuke_overlays(sb):
    sb.execute_script("""
        console.log('[Auto] 清理弹窗/广告');

        // 删除 iframe（广告核心）
        document.querySelectorAll('iframe').forEach(el => el.remove());

        // 删除 modal / popup
        document.querySelectorAll('[class*="modal"], [class*="popup"], [role="dialog"]').forEach(el => el.remove());

        // 删除 fixed 遮挡层
        document.querySelectorAll('*').forEach(el => {
            const style = window.getComputedStyle(el);

            if (
                style.position === 'fixed' &&
                parseInt(style.zIndex || 0) > 1000
            ) {
                el.remove();
            }
        });

        // 解除 pointer 阻挡
        document.body.style.pointerEvents = 'auto';
    """)


# ==========================================================
# 🔥 稳定点击 Renew（不依赖 selector）
# ==========================================================

def wait_and_click_renew(sb, timeout=30):

    print("🔍 查找 Renew...")

    for i in range(timeout):

        try:
            nuke_overlays(sb)

            clicked = sb.execute_script("""
                const els = [...document.querySelectorAll('*')];

                for (const el of els) {

                    if (!el.innerText) continue;

                    const txt = el.innerText.toLowerCase();

                    if (txt.includes('renew')) {

                        el.scrollIntoView({block:'center'});

                        el.click();

                        return true;
                    }
                }

                return false;
            """)

            if clicked:
                print("✅ 点击 Renew 成功")
                return True

        except Exception as e:
            print("err:", e)

        time.sleep(1)

    return False


# ==========================================================
# Linkvertise 自动脚本（你那版 + 稳定增强）
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

            // 🔥 清广告
            document.querySelectorAll('iframe').forEach(el => el.remove());

            // ====================================================
            // Linkvertise
            // ====================================================

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
                        if (wrapper.textContent?.includes('Watch Ads')) {
                            watchAdsBtn = wrapper;
                            break;
                        }
                    }

                    if (watchAdsBtn) {

                        const priceBox =
                            watchAdsBtn.closest('.membership-plan-option');

                        if (priceBox) {

                            if (!priceBox.classList.contains('active')) {
                                watchAdsBtn.click();
                            } else {

                                const continueBtn =
                                    findByText('button', 'Continue');

                                if (visible(continueBtn) && !window.continueClicked) {
                                    window.continueClicked = true;
                                    continueBtn.click();
                                }
                            }
                        }
                    }
                }

                // Step 3
                const skipAdBtn =
                    findByText('span', 'Skip Ad') ||
                    findByText('button', 'Skip Ad');

                if (visible(skipAdBtn)) {
                    skipAdBtn.click();
                }

                // Step 4
                if (url.includes('/success')) {

                    const lvButtons =
                        document.querySelectorAll('[data-testid="lv-button"]');

                    for (const btn of lvButtons) {
                        if (btn.textContent?.includes('Open')) {

                            setTimeout(() => {
                                btn.click();

                                setTimeout(() => {
                                    window.close();
                                }, 1500);

                            }, 1500);
                        }
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

        server_url = f"https://panel.orihost.com/server/{server_id}"
        sb.open(server_url)

        time.sleep(10)
        screenshot(sb, "server_page.png")

        # 🔥 先清一波广告
        nuke_overlays(sb)

        if "Renew Limit Reached" in sb.get_text("body"):
            return "LIMIT"

        if not wait_and_click_renew(sb):
            screenshot(sb, "renew_fail.png")
            return "NO_RENEW_BTN"

        time.sleep(5)

        # 点击 linkvertise
        sb.execute_script("""
            [...document.querySelectorAll('*')].forEach(el => {
                if (el.innerText && el.innerText.toLowerCase().includes('linkvertise')) {
                    el.click();
                }
            });
        """)

        time.sleep(5)

        handles = sb.driver.window_handles
        if len(handles) > 1:
            sb.switch_to_window(1)

        inject_linkvertise_script(sb)

        time.sleep(120)

        return "OK"


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