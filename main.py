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
# 💀 终极清广告（新版）
# ==========================================================

def nuke_ads(sb):

    sb.execute_script("""
    // 删除 iframe
    document.querySelectorAll('iframe').forEach(el => el.remove());

    // 删除遮罩层
    document.querySelectorAll('div,section').forEach(el => {
        const style = window.getComputedStyle(el);

        if (
            style.position === 'fixed' &&
            parseInt(style.zIndex) > 1000
        ) {
            el.remove();
        }
    });

    // 解锁点击
    document.body.style.pointerEvents = 'auto';

    document.querySelectorAll('*').forEach(el=>{
        el.style.pointerEvents='auto';
    });
    """)


# ==========================================================
# 💀 强力点击（升级版）
# ==========================================================

def extreme_click(sb, keyword):

    return sb.execute_script(f"""
    (() => {{

        const els = document.querySelectorAll('*');

        for (const el of els) {{

            const txt = (el.innerText || "").toLowerCase();

            if (txt.includes("{keyword.lower()}")) {{

                el.scrollIntoView({{block:'center'}});

                try {{ el.click(); }} catch(e){{}}

                el.dispatchEvent(new MouseEvent('click', {{
                    bubbles:true,
                    cancelable:true
                }}));

                return true;
            }}
        }}

        return false;

    }})();
    """)


# ==========================================================
# 🎯 点击 Linkvertise（强化）
# ==========================================================

def click_open_linkvertise(sb):

    print("🎯 开始点击 Linkvertise")

    for i in range(30):

        nuke_ads(sb)

        if extreme_click(sb, "open linkvertise"):
            print("✅ 命中 Open Linkvertise")
            return True

        if extreme_click(sb, "linkvertise"):
            print("✅ 命中 Linkvertise")
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
        for _ in range(5):
            nuke_ads(sb)
            time.sleep(1)

        # ==================================================
        # 点击 Renew
        # ==================================================

        print("🔍 点击 Renew")

        for _ in range(10):
            nuke_ads(sb)

            if extreme_click(sb, "renew"):
                print("✅ Renew 成功")
                break

            time.sleep(1)

        screenshot(sb, "after_renew.png")

        time.sleep(3)

        print("💀 Renew 后清广告")
        for _ in range(5):
            nuke_ads(sb)
            time.sleep(1)

        # ==================================================
        # Linkvertise
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