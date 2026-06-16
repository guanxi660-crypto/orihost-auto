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
# 💀 只删 iframe
# ==========================================================

def clean_ads(sb):
    sb.execute_script("document.querySelectorAll('iframe').forEach(el=>el.remove())")


# ==========================================================
# 🎯 精准点击 Renew（核心修复）
# ==========================================================

def click_real_renew(sb):

    print("🎯 精准查找 Renew 按钮")

    for _ in range(10):

        clicked = sb.execute_script("""
        (() => {

            const btns = document.querySelectorAll('button');

            for (const btn of btns) {
                const text = btn.innerText || "";
                if (text.includes("Renew")) {

                    btn.scrollIntoView({block:'center'});

                    // 强制 React 触发
                    btn.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true}));
                    btn.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                    btn.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                    btn.dispatchEvent(new MouseEvent('click', {bubbles:true}));

                    return true;
                }
            }

            return false;
        })();
        """)

        if clicked:
            print("✅ 已点击 Renew（真实按钮）")
            return True

        time.sleep(1)

    return False


# ==========================================================
# 🎯 等待 modal
# ==========================================================

def wait_modal(sb):

    print("🎯 等待弹窗...")

    for _ in range(15):

        exists = sb.execute_script("""
        return !!document.querySelector('#headlessui-dialog-1');
        """)

        if exists:
            print("✅ 弹窗出现")
            return True

        time.sleep(1)

    return False


# ==========================================================
# 🎯 点击 Open Linkvertise
# ==========================================================

def click_modal_open(sb):

    return sb.execute_script("""
    (() => {

        const modal = document.querySelector('#headlessui-dialog-1');
        if (!modal) return false;

        const btns = modal.querySelectorAll('button');

        for (const b of btns) {
            if (b.innerText.includes('Open Linkvertise')) {

                b.dispatchEvent(new MouseEvent('click',{bubbles:true}));
                return true;
            }
        }

        return false;

    })();
    """)


# ==========================================================
# 🤖 Linkvertise 自动
# ==========================================================

def inject_linkvertise_bot(sb):

    sb.execute_script("""
    (function(){

        function log(msg){
            console.log("[AUTO]", msg);
        }

        function find(tag, text){
            return [...document.querySelectorAll(tag)]
                .find(e => e.innerText && e.innerText.includes(text));
        }

        function click(el,name){
            if(!el) return;
            log("点击:"+name);
            el.click();
        }

        setInterval(()=>{

            try{
                const url = location.href;

                let btn = find('button','Get Link');
                if(btn) click(btn,"Get Link");

                if(url.includes('/access/')){
                    let watch = find('div','Watch Ads');
                    if(watch) click(watch,"Watch Ads");

                    let cont = find('button','Continue');
                    if(cont) click(cont,"Continue");
                }

                let skip = find('button','Skip Ad');
                if(skip) click(skip,"Skip Ad");

                if(url.includes('/success')){
                    let open = find('button','Open');
                    if(open){
                        click(open,"Final Open");
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

        clean_ads(sb)

        # ===============================
        # Renew
        # ===============================

        if not click_real_renew(sb):
            return "RENEW_CLICK_FAIL"

        time.sleep(2)

        screenshot(sb, "after_renew.png")

        if not wait_modal(sb):
            return "NO_MODAL"

        if not click_modal_open(sb):
            return "OPEN_FAIL"

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