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
# 🚫 轻量去广告（只做一次）
# ==========================================================

def clean_ads_once(sb):
    # 只移除 iframe，不做其他 DOM 干预
    sb.execute_script("""
        document.querySelectorAll('iframe').forEach(e => {
            try { e.remove(); } catch(e) {}
        });
    """)


# ==========================================================
# 🎯 点击 Renew（稳定版）
# ==========================================================

def click_real_renew(sb):

    return sb.execute_script("""
    (() => {
        const btns = document.querySelectorAll('button');

        for (const b of btns) {
            const t = (b.innerText || '').trim();

            if (t.includes('Renew')) {
                b.scrollIntoView({block:'center'});

                b.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                return true;
            }
        }
        return false;
    })();
    """)


# ==========================================================
# 🎯 等待 modal（不依赖固定 id）
# ==========================================================

def wait_modal(sb):

    for _ in range(20):
        modal = sb.execute_script("""
            return document.querySelector('[role="dialog"]') ||
                   document.querySelector('div[class*="fixed"]');
        """)
        if modal:
            print("✅ 弹窗出现")
            return True

        time.sleep(1)

    return False


# ==========================================================
# 🎯 点击 Open Linkvertise（稳定增强版）
# ==========================================================

def click_modal_open(sb):

    # 直接找按钮文本（比 class 稳）
    sb.wait_for_element_visible("button", timeout=15)

    ok = sb.execute_script("""
    (() => {
        const btns = [...document.querySelectorAll('button')];

        const target = btns.find(b =>
            (b.innerText || '').includes('Open Linkvertise')
        );

        if (target) {
            target.scrollIntoView({block:'center'});
            target.click();
            return true;
        }

        return false;
    })();
    """)

    if not ok:
        # fallback class
        sb.uc_click("button.iEubrt")

    print("✅ Open Linkvertise 已点击")
    return True


# ==========================================================
# 🤖 Linkvertise bot（保持）
# ==========================================================

def inject_linkvertise_bot(sb):

    sb.execute_script("""
    (function(){

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

        # ✅ 只在这里清一次
        clean_ads_once(sb)

        # ===========================
        # Renew
        # ===========================

        print("🔍 点击 Renew")

        click_real_renew(sb)

        time.sleep(2)

        screenshot(sb, "after_renew.png")

        # ===========================
        # Modal
        # ===========================

        if not wait_modal(sb):
            return "NO_MODAL"

        click_modal_open(sb)

        time.sleep(5)

        # window switch fallback
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