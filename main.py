# -*- coding: utf-8 -*-

import os
import time
from seleniumbase import SB
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


LOGIN_URL = "https://panel.orihost.com/auth/login"

EMAIL_SEL = 'input[name="username"]'
PASS_SEL = 'input[name="password"]'
SUBMIT_SEL = 'button[type="submit"]'

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# =========================
# 工具
# =========================

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


# =========================
# 更稳定点击
# =========================

def safe_click(sb, css, text=None, timeout=10):
    """
    统一稳定点击：
    - wait clickable
    - scroll into view
    - ActionChains click（模拟真实用户）
    """

    try:
        if text:
            el = sb.find_element(f"{css}:contains({text})")
        else:
            el = sb.find_element(css)

        sb.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)

        ActionChains(sb.driver).move_to_element(el).pause(0.2).click(el).perform()
        return True

    except Exception as e:
        print("❌ click failed:", css, e)
        return False


def click_renew(sb):
    buttons = sb.find_elements("button")
    for b in buttons:
        try:
            if "Renew" in b.text:
                sb.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                time.sleep(0.3)
                ActionChains(sb.driver).move_to_element(b).click(b).perform()
                return True
        except:
            pass
    return False


# =========================
# modal 等待（替换 polling JS）
# =========================

def wait_modal(sb, timeout=20):
    try:
        WebDriverWait(sb.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[role="dialog"], div.fixed'))
        )
        print("✅ 弹窗出现")
        return True
    except:
        return False


# =========================
# tab / redirect 处理
# =========================

def handle_new_tab(sb, old_handles):
    time.sleep(2)
    new_handles = sb.driver.window_handles

    if len(new_handles) > len(old_handles):
        new_tab = list(set(new_handles) - set(old_handles))[0]
        sb.switch_to_window(new_tab)
        print("✅ 已切换新窗口")
        return True

    return False


# =========================
# 主流程
# =========================

def run():

    email = os.getenv("ORIHOST_EMAIL")
    password = os.getenv("ORIHOST_PASSWORD")

    with SB(uc=True, headless=False, xvfb=True) as sb:

        print("🌍 打开登录页")
        sb.open(LOGIN_URL)
        time.sleep(3)

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
        time.sleep(5)

        screenshot(sb, "server_page.png")

        print("🔍 点击 Renew")
        click_renew(sb)

        time.sleep(2)
        screenshot(sb, "after_renew.png")

        if not wait_modal(sb):
            print("❌ 没检测到弹窗")
            return "NO_MODAL"

        # =========================
        # 点击 Open Link（只做正常点击）
        # =========================

        old_handles = sb.driver.window_handles

        print("🚀 点击 Open Link")
        safe_click(sb, "button", "Open Linkvertise")

        handle_new_tab(sb, old_handles)

        time.sleep(5)

        screenshot(sb, "final.png")

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