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
# 🚫 safe cleanup
# ==========================================================

def clean_ads_once(sb):
    sb.execute_script("""
        (() => {
            document.querySelectorAll('iframe').forEach(e => e.remove());
        })();
    """)


# ==========================================================
# 🎯 Renew
# ==========================================================

def click_real_renew(sb):

    return sb.execute_script("""
    (() => {
        const btns = document.querySelectorAll('button');

        for (const b of btns) {
            if ((b.innerText || '').includes('Renew')) {
                b.scrollIntoView({block:'center'});
                b.click();
                return true;
            }
        }
        return false;
    })();
    """)


# ==========================================================
# 🎯 modal detect
# ==========================================================

def wait_modal(sb):

    for _ in range(25):

        found = sb.execute_script("""
        (() => {
            return !!(
                document.querySelector('[role="dialog"]') ||
                document.querySelector('div[class*="fixed"]')
            );
        })();
        """)

        if found:
            print("✅ 弹窗出现")
            return True

        time.sleep(1)

    return False


# ==========================================================
# 💀 超级真实点击（最终版）
# ==========================================================

def human_level_click(sb, text):

    return sb.execute_script(f"""
    (() => {{

        const el = [...document.querySelectorAll('button')]
            .find(b => (b.innerText || '').includes("{text}"));

        if (!el) return false;

        el.scrollIntoView({{block:'center'}});

        const rect = el.getBoundingClientRect();

        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        const realTarget = document.elementFromPoint(x, y);

        if (!realTarget) return false;

        realTarget.focus();

        const opts = {{
            bubbles: true,
            cancelable: true,
            view: window
        }};

        // 🔥 关键：完整 pointer chain
        realTarget.dispatchEvent(new PointerEvent('pointerover', opts));
        realTarget.dispatchEvent(new PointerEvent('pointerenter', opts));
        realTarget.dispatchEvent(new PointerEvent('pointerdown', opts));
        realTarget.dispatchEvent(new MouseEvent('mousedown', opts));
        realTarget.dispatchEvent(new MouseEvent('mouseup', opts));
        realTarget.dispatchEvent(new MouseEvent('click', opts));

        // fallback native
        if (realTarget.click) realTarget.click();

        return true;

    }})();
    """)


# ==========================================================
# 🎯 Linkvertise click + strict verification
# ==========================================================

def click_modal_open(sb):

    print("🚀 尝试 human-level 点击 Open Linkvertise")

    old_url = sb.get_current_url()

    human_level_click(sb, "Open Linkvertise")

    print("⏳ 等待真实跳转...")

    for _ in range(30):

        try:
            url = sb.get_current_url()

            # 1. URL change
            if url != old_url:
                print("✅ URL 变化:", url)
                return True

            # 2. detect linkvertise
            if "linkvertise" in url:
                print("✅ 进入 Linkvertise")
                return True

            # 3. new tab
            handles = sb.driver.window_handles
            if len(handles) > 1:
                sb.switch_to_window(handles[-1])
                print("✅ 新 tab 已切换")
                return True

        except:
            pass

        time.sleep(1)

    print("❌ 完全未跳转 → 100% click 被拦截 (isTrusted / overlay block)")
    return False


# ==========================================================
# 🤖 bot
# ==========================================================

def inject_linkvertise_bot(sb):

    sb.execute_script("""
    (() => {

        function find(tag,text){
            return [...document.querySelectorAll(tag)]
                .find(e => e.innerText && e.innerText.includes(text));
        }

        function click(el){
            if(!el) return;
            el.focus();
            el.click();
        }

        setInterval(() => {

            try {

                const url = location.href;

                let get = find('button','Get Link');
                if(get) click(get);

                if(url.includes('/access/')){

                    let watch = find('div','Watch Ads');
                    if(watch) click(watch);

                    let cont = find('button','Continue');
                    if(cont) click(cont);
                }

                let skip = find('button','Skip Ad');
                if(skip) click(skip);

                if(url.includes('/success')){
                    let open = find('button','Open');
                    if(open){
                        click(open);
                        setTimeout(()=>window.close(),2000);
                    }
                }

            } catch(e) {}

        }, 2000);

    })();
    """)


# ==========================================================
# 主流程
# ==========================================================

def run():

    email = os.getenv("ORIHOST_EMAIL")
    password = os.getenv("ORIHOST_PASSWORD")

    with SB(uc=True, headless=False, xvfb=True) as sb:

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

        clean_ads_once(sb)

        print("🔍 点击 Renew")
        click_real_renew(sb)

        time.sleep(2)

        screenshot(sb, "after_renew.png")

        if not wait_modal(sb):
            return "NO_MODAL"

        click_modal_open(sb)

        time.sleep(5)

        try:
            handles = sb.driver.window_handles
            if len(handles) > 1:
                sb.switch_to_window(handles[-1])
        except:
            pass

        inject_linkvertise_bot(sb)

        time.sleep(40)

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