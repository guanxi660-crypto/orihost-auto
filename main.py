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
# 🚫 clean ads（只一次）
# ==========================================================

def clean_ads_once(sb):
    sb.execute_script("""
        (() => {
            document.querySelectorAll('iframe').forEach(e => {
                try { e.remove(); } catch(e) {}
            });
        })();
    """)


# ==========================================================
# 🎯 Renew 点击
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

    for _ in range(20):
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
# 💥 超真实点击（关键修复）
# ==========================================================

def force_real_click(sb, selector):

    sb.execute_script(f"""
    (() => {{
        const el = document.querySelector("{selector}");
        if (!el) return false;

        el.scrollIntoView({{block:'center'}});

        el.dispatchEvent(new PointerEvent('pointerdown', {{bubbles:true}}));
        el.dispatchEvent(new MouseEvent('mousedown', {{bubbles:true}}));
        el.dispatchEvent(new MouseEvent('mouseup', {{bubbles:true}}));
        el.dispatchEvent(new MouseEvent('click', {{bubbles:true}}));

        return true;
    }})();
    """)


# ==========================================================
# 🎯 Open Linkvertise（增强稳定版）
# ==========================================================

def click_modal_open(sb):

    print("🚀 尝试点击 Open Linkvertise")

    # 先记录 URL
    old_url = sb.get_current_url()

    ok = sb.execute_script("""
    (() => {

        const btns = [...document.querySelectorAll('button')];

        const target = btns.find(b =>
            (b.innerText || '').includes('Open Linkvertise')
        );

        if (!target) return false;

        target.scrollIntoView({block:'center'});

        target.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true}));
        target.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
        target.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
        target.dispatchEvent(new MouseEvent('click', {bubbles:true}));

        return true;

    })();
    """)

    if not ok:
        sb.uc_click("button.iEubrt")

    # ======================================================
    # 等待跳转 / 新 tab
    # ======================================================

    print("⏳ 等待 Linkvertise 跳转...")

    for _ in range(20):
        try:
            url = sb.get_current_url()

            if "linkvertise" in url or url != old_url:
                print("✅ 已跳转:", url)
                return True

            handles = sb.driver.window_handles
            if len(handles) > 1:
                sb.switch_to_window(handles[-1])
                print("✅ 切换到新窗口")
                return True

        except:
            pass

        time.sleep(1)

    print("⚠️ 未检测到跳转（可能 click 被拦截）")
    return False


# ==========================================================
# 🤖 bot（保持）
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