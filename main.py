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
            return txt.replace("#", "")
    return None


# ==========================================================
# 💀 杀广告（核心修复）
# ==========================================================

def kill_ads(sb):

    print("💀 清理广告")

    sb.execute_script("""
        // 删除常见广告节点
        document.querySelectorAll('[id*="ad"], [class*="ad"], iframe')
            .forEach(el => {
                el.remove();
            });

        // 删除全屏遮罩
        document.querySelectorAll('*').forEach(el => {
            const z = window.getComputedStyle(el).zIndex;
            if (z && parseInt(z) > 9999) {
                el.remove();
            }
        });
    """)

    # 再尝试点击 Close / Continue
    for word in ["close", "continue", "tap"]:
        sb.execute_script(f"""
            document.querySelectorAll('*').forEach(el => {{
                if (el.innerText &&
                    el.innerText.toLowerCase().includes("{word}")) {{
                    el.click();
                }}
            }});
        """)


# ==========================================================
# 💀 点击
# ==========================================================

def click_text(sb, text):

    return sb.execute_script(f"""
        const els = document.querySelectorAll('*');
        for (const el of els) {{
            if (el.innerText &&
                el.innerText.toLowerCase().includes("{text.lower()}")) {{
                el.click();
                return true;
            }}
        }}
        return false;
    """)


# ==========================================================
# 🎯 点击 Open Linkvertise（加强版）
# ==========================================================

def click_open_linkvertise(sb):

    print("🎯 点击 Open Linkvertise")

    for _ in range(20):

        # 再清一遍广告
        kill_ads(sb)

        result = sb.execute_script("""
            const dialog = document.querySelector('[role="dialog"]');

            if (dialog) {
                const buttons = dialog.querySelectorAll('button');

                for (const btn of buttons) {
                    if (btn.innerText &&
                        btn.innerText.toLowerCase().includes('open')) {
                        btn.click();
                        return true;
                    }
                }
            }
            return false;
        """)

        if result:
            print("✅ 点击成功 Open Linkvertise")
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

        # 💀 第一步：先杀广告
        kill_ads(sb)
        time.sleep(2)

        # 1️⃣ Renew
        print("🔍 点击 Renew")
        click_text(sb, "renew")

        time.sleep(3)

        screenshot(sb, "after_renew.png")  # ✅你要的截图

        # 💀 再杀广告（弹窗前）
        kill_ads(sb)

        # 2️⃣ Open Linkvertise
        if not click_open_linkvertise(sb):
            screenshot(sb, "open_lv_fail.png")
            return "NO_OPEN_LINKVERTISE"

        time.sleep(5)

        # 切窗口
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