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
# 💀 只删 iframe（安全版）
# ==========================================================

def clean_ads(sb):
    sb.execute_script("""
    document.querySelectorAll('iframe').forEach(el => el.remove());
    """)


# ==========================================================
# 💀 强点击
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
                el.dispatchEvent(new MouseEvent('click', {{bubbles:true}}));
                return true;
            }}
        }}
        return false;
    }})();
    """)


# ==========================================================
# 🎯 点击弹窗里的 Open Linkvertise（关键）
# ==========================================================

def click_modal_open(sb):

    print("🎯 等待弹窗...")

    for _ in range(10):
        exists = sb.execute_script("""
        return !!document.querySelector('#headlessui-dialog-1');
        """)

        if exists:
            print("✅ 检测到弹窗")

            clicked = sb.execute_script("""
            (() => {
                const modal = document.querySelector('#headlessui-dialog-1');
                if (!modal) return false;

                const btns = modal.querySelectorAll('button');

                for (const b of btns) {
                    if (b.innerText.includes('Open Linkvertise')) {
                        b.click();
                        b.dispatchEvent(new MouseEvent('click',{bubbles:true}));
                        return true;
                    }
                }

                return false;
            })();
            """)

            if clicked:
                print("✅ 已点击 Open Linkvertise")
                return True

        time.sleep(1)

    return False


# ==========================================================
# 🤖 Linkvertise 自动脚本（带日志）
# ==========================================================

def inject_linkvertise_bot(sb):

    print("🤖 注入 Linkvertise 脚本")

    sb.execute_script("""
    (function(){

        function log(msg){
            console.log("[AUTO]", msg);
        }

        function findByText(tag, text) {
            return Array.from(document.querySelectorAll(tag))
                .find(el => el.innerText && el.innerText.includes(text));
        }

        function click(el, name){
            if(!el) return;
            log("点击: " + name);
            el.click();
            el.dispatchEvent(new MouseEvent('click',{bubbles:true}));
        }

        setInterval(()=>{

            try{
                const url = location.href;
                log("当前页面: " + url);

                let btn = findByText('button','Get Link');
                if(btn) click(btn, "Get Link");

                if(url.includes('/access/')){
                    let watch = findByText('div','Watch Ads');
                    if(watch) click(watch, "Watch Ads");

                    let cont = findByText('button','Continue');
                    if(cont) click(cont, "Continue");
                }

                let skip = findByText('button','Skip Ad');
                if(skip) click(skip, "Skip Ad");

                if(url.includes('/success')){
                    let open = findByText('button','Open');
                    if(open){
                        click(open, "Final Open");
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

        # ==================================================
        # Renew
        # ==================================================

        print("🔍 点击 Renew")

        extreme_click(sb, "renew")

        time.sleep(2)

        screenshot(sb, "after_renew.png")

        # 👇 关键：点击弹窗
        if not click_modal_open(sb):
            return "NO_MODAL"

        time.sleep(5)

        # 切窗口（安全）
        try:
            handles = sb.driver.window_handles
            if len(handles) > 1:
                sb.switch_to_window(handles[-1])
        except:
            print("⚠️ 浏览器跳转")

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