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
# 🚫 clean (safe)
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
                b.focus();
                b.dispatchEvent(new MouseEvent('click',{bubbles:true}));
                return true;
            }
        }
        return false;
    })();
    """)


# ==========================================================
# 🎯 modal detect（稳定）
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
# 💥 超强点击（核心修复）
# ==========================================================

def ultra_click(sb, text):

    return sb.execute_script(f"""
    (() => {{

        const btn = [...document.querySelectorAll('button')]
            .find(b => (b.innerText || '').includes("{text}"));

        if (!btn) return false;

        btn.scrollIntoView({{block:'center'}});

        // 强制 focus
        btn.focus();

        // 获取真实点击点
        const rect = btn.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        const el = document.elementFromPoint(x, y);
        if (el) el.focus();

        const events = [
            new PointerEvent('pointerdown', {{bubbles:true}}),
            new MouseEvent('mousedown', {{bubbles:true}}),
            new MouseEvent('mouseup', {{bubbles:true}}),
            new MouseEvent('click', {{bubbles:true}})
        ];

        for (const e of events) {{
            btn.dispatchEvent(e);
        }}

        // fallback native click
        btn.click();

        return true;

    }})();
    """)


# ==========================================================
# 🎯 Linkvertise click + jump detection
# ==========================================================

def click_modal_open(sb):

    print("🚀 点击 Open Linkvertise（增强版）")

    old_url = sb.get_current_url()

    ultra_click(sb, "Open Linkvertise")

    # ======================================================
    # jump detection (3-layer)
    # ======================================================

    print("⏳ 等待跳转...")

    for _ in range(25):

        try:
            url = sb.get_current_url()

            # 1. URL change
            if url != old_url:
                print("✅ URL 已变化:", url)
                return True

            # 2. linkvertise detect
            if "linkvertise" in url:
                print("✅ 已进入 Linkvertise")
                return True

            # 3. new tab detect
            handles = sb.driver.window_handles
            if len(handles) > 1:
                sb.switch_to_window(handles[-1])
                print("✅ 新窗口已切换")
                return True

        except:
            pass

        time.sleep(1)

    print("❌ 未检测到跳转（click 被拦截 or window.open blocked）")
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
            el.dispatchEvent(new MouseEvent('click',{bubbles:true}));
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