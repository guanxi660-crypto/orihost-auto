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
# 💀 清 iframe（安全）
# ==========================================================

def clean_ads(sb):
    sb.execute_script("document.querySelectorAll('iframe').forEach(e=>e.remove())")


# ==========================================================
# 🎯 精准点击 Renew
# ==========================================================

def click_real_renew(sb):

    return sb.execute_script("""
    (() => {

        const btns = document.querySelectorAll('button');

        for (const b of btns) {
            if ((b.innerText || '').includes('Renew')) {

                b.scrollIntoView({block:'center'});

                b.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));
                b.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));
                b.dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));
                b.dispatchEvent(new MouseEvent('click',{bubbles:true}));

                return true;
            }
        }

        return false;
    })();
    """)


# ==========================================================
# 🎯 等待弹窗
# ==========================================================

def wait_modal(sb):

    for _ in range(15):

        if sb.execute_script("return !!document.querySelector('#headlessui-dialog-1');"):
            print("✅ 弹窗出现")
            return True

        time.sleep(1)

    return False


# ==========================================================
# 🔥 修复版：点击 Open Linkvertise（核心）
# ==========================================================

def click_modal_open(sb):

    sb.wait_for_element(
        "#headlessui-dialog-1 button.iEubrt",
        timeout=15
    )

    sb.uc_click(
        "#headlessui-dialog-1 button.iEubrt"
    )

    print("✅ Open Linkvertise 已真实点击")

    return True


# ==========================================================
# 🤖 Linkvertise 自动处理（带日志）
# ==========================================================

def inject_linkvertise_bot(sb):

    sb.execute_script("""
    (function(){

        function log(m){ console.log('[AUTO]',m); }

        function find(tag,text){
            return [...document.querySelectorAll(tag)]
                .find(e=>e.innerText && e.innerText.includes(text));
        }

        function click(el,name){
            if(!el) return;
            log('点击 '+name);
            el.click();
            el.dispatchEvent(new MouseEvent('click',{bubbles:true}));
        }

        setInterval(()=>{

            try{

                const url = location.href;
                log('URL: '+url);

                let get = find('button','Get Link');
                if(get) click(get,'Get Link');

                if(url.includes('/access/')){

                    let watch = find('div','Watch Ads');
                    if(watch) click(watch,'Watch Ads');

                    let cont = find('button','Continue');
                    if(cont) click(cont,'Continue');
                }

                let skip = find('button','Skip Ad');
                if(skip) click(skip,'Skip Ad');

                if(url.includes('/success')){
                    let open = find('button','Open');
                    if(open){
                        click(open,'Final Open');
                        setTimeout(()=>window.close(),2000);
                    }
                }

            }catch(e){}

        },2000);

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

        clean_ads(sb)

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

        if not click_modal_open(sb):
            return "OPEN_FAIL"

        time.sleep(5)

        # window handle fallback
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