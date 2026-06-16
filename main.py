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
# 💀 超暴力点击（核心）
# ==========================================================

def extreme_click(sb, keyword):

    return sb.execute_script(f"""
    (() => {{

        function isVisible(el) {{
            const style = window.getComputedStyle(el);
            return style.display !== 'none' && style.visibility !== 'hidden';
        }}

        function killOverlay() {{
            document.querySelectorAll('div,iframe').forEach(el => {{
                const cls = (el.className || '').toString().toLowerCase();
                if (cls.includes('overlay') || cls.includes('mask') || cls.includes('modal')) {{
                    el.style.display = 'none';
                }}
            }});
        }}

        function click(el) {{
            if (!el) return false;

            el.style.pointerEvents = 'auto';
            el.style.zIndex = 999999;

            killOverlay();

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
# 💀 自动关广告（加强版）
# ==========================================================

def auto_close_ads(sb):

    sb.execute_script("""
    (() => {

        const words = ["close", "continue", "skip", "tap"];

        document.querySelectorAll('*').forEach(el => {

            if (!el.innerText) return;

            const txt = el.innerText.toLowerCase();

            for (const w of words) {
                if (txt.includes(w)) {
                    try { el.click(); } catch(e){}
                }
            }
        });

    })();
    """)


# ==========================================================
# 🎯 点击 Open Linkvertise（终极版）
# ==========================================================

def click_open_linkvertise(sb):

    print("🎯 强力点击 Open Linkvertise")

    for _ in range(25):

        auto_close_ads(sb)

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

        # 💀 自动关广告
        auto_close_ads(sb)
        time.sleep(2)

        # 1️⃣ Renew（暴力点击）
        print("🔍 强力点击 Renew")

        for _ in range(5):
            if extreme_click(sb, "renew"):
                break
            time.sleep(1)

        screenshot(sb, "after_renew.png")

        time.sleep(3)

        # 💀 再清广告
        auto_close_ads(sb)

        # 2️⃣ Open Linkvertise
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