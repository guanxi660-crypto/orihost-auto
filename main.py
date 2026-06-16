# -*- coding: utf-8 -*-

import os
import time
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
    path = f"{SCREENSHOT_DIR}/{int(time.time())}_{name}"
    sb.save_screenshot(path)
    print("📸", path)


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
# 💀 超强点击
# ==========================================================

def extreme_click(sb, keyword):
    return sb.execute_script(f"""
    (() => {{

        function isVisible(el) {{
            const style = window.getComputedStyle(el);
            return style.display !== 'none' && style.visibility !== 'hidden';
        }}

        function click(el) {{
            if (!el) return false;

            el.style.pointerEvents = 'auto';
            el.style.zIndex = 999999;

            el.scrollIntoView({{block:'center'}});

            try {{ el.click(); }} catch(e){{}}

            const evt = {{ bubbles:true, cancelable:true, view:window }};
            el.dispatchEvent(new MouseEvent('mousedown', evt));
            el.dispatchEvent(new MouseEvent('mouseup', evt));
            el.dispatchEvent(new MouseEvent('click', evt));

            return true;
        }}

        const els = document.querySelectorAll('*');

        for (const el of els) {{
            if (!el.innerText) continue;

            const txt = el.innerText.toLowerCase();

            if (txt.includes("{keyword.lower()}") && isVisible(el)) {{
                return click(el);
            }}
        }}

        return false;

    }})();
    """)


# ==========================================================
# 💀 点击 iframe 里的 Close（已修复）
# ==========================================================

def click_iframe_close(sb):

    iframes = sb.find_elements("iframe")

    for idx, iframe in enumerate(iframes):
        try:
            sb.switch_to_frame(iframe)

            clicked = sb.execute_script("""
            (() => {

                const keys = ["close", "×", "skip"];

                const els = document.querySelectorAll("*");

                for (const el of els) {

                    const txt = (el.innerText || "").toLowerCase();

                    for (const k of keys) {
                        if (txt.includes(k)) {

                            el.style.zIndex = 999999;
                            el.style.pointerEvents = 'auto';

                            try { el.click(); } catch(e){}

                            const evt = { bubbles:true, cancelable:true };
                            el.dispatchEvent(new MouseEvent('click', evt));

                            return true;
                        }
                    }
                }

                return false;

            })();
            """)

            sb.switch_to_default_content()

            if clicked:
                print(f"✅ iframe[{idx}] Close 已点击")
                return True

        except Exception as e:
            print(f"⚠️ iframe[{idx}] 失败:", e)
            sb.switch_to_default_content()

    return False


# ==========================================================
# 💀 多次清广告
# ==========================================================

def clean_ads(sb, rounds=5):
    for _ in range(rounds):
        click_iframe_close(sb)
        time.sleep(1)


# ==========================================================
# 🎯 点击 Open Linkvertise
# ==========================================================

def click_open_linkvertise(sb):

    print("🎯 点击 Open Linkvertise")

    for _ in range(20):

        clean_ads(sb, 1)

        if extreme_click(sb, "open linkvertise"):
            print("✅ 命中 Open Linkvertise")
            return True

        if extreme_click(sb, "open"):
            print("✅ 命中 Open")
            return True

        time.sleep(1)

    return False


# ==========================================================
# 主流程
# ==========================================================

def run():

    email = os.getenv("ORIHOST_EMAIL")
    password = os.getenv("ORIHOST_PASSWORD")

    with SB(uc=True, headless=True, xvfb=True) as sb:

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

        server_id = extract_server_id(sb)
        print("🎮 Server:", server_id)

        sb.open(f"https://panel.orihost.com/server/{server_id}")
        time.sleep(8)

        screenshot(sb, "server_page.png")

        print("💀 初始清广告")
        clean_ads(sb, 5)

        # ==================================================
        # 1️⃣ 点击 Renew
        # ==================================================

        print("🔍 点击 Renew")

        for _ in range(5):
            clean_ads(sb, 1)

            if extreme_click(sb, "renew"):
                print("✅ Renew 成功")
                break

            time.sleep(1)

        screenshot(sb, "after_renew.png")

        time.sleep(3)

        print("💀 Renew 后清广告")
        clean_ads(sb, 5)

        # ==================================================
        # 2️⃣ Open Linkvertise
        # ==================================================

        if not click_open_linkvertise(sb):
            screenshot(sb, "open_lv_fail.png")
            return "NO_OPEN_LINKVERTISE"

        time.sleep(5)

        handles = sb.driver.window_handles
        if len(handles) > 1:
            sb.switch_to_window(handles[-1])

        screenshot(sb, "linkvertise.png")

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