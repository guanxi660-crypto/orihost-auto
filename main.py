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
# 💀 清广告（终极）
# ==========================================================

def nuke_ads(sb):
    sb.execute_script("""
    document.querySelectorAll('iframe').forEach(el => el.remove());

    document.querySelectorAll('div,section').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.position === 'fixed' && parseInt(style.zIndex) > 1000) {
            el.remove();
        }
    });

    document.body.style.pointerEvents = 'auto';
    document.querySelectorAll('*').forEach(el=>{
        el.style.pointerEvents='auto';
    });
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
# 🚀 注入 Linkvertise 自动脚本
# ==========================================================

def inject_linkvertise_bot(sb):

    print("🤖 注入 Linkvertise 自动处理")

    sb.execute_script("""
    (function(){

        function findByText(tag, text) {
            return Array.from(document.querySelectorAll(tag))
                .find(el => el.innerText && el.innerText.includes(text));
        }

        function click(el){
            if(!el) return;
            el.click();
            el.dispatchEvent(new MouseEvent('click',{bubbles:true}));
        }

        setInterval(()=>{

            try{
                const url = location.href;

                // Get Link
                let btn = findByText('button','Get Link') || findByText('a','Get Link');
                if(btn) click(btn);

                // Watch Ads
                if(url.includes('/access/')){
                    let watch = findByText('div','Watch Ads');
                    if(watch) click(watch);

                    let cont = findByText('button','Continue');
                    if(cont) click(cont);
                }

                // Skip
                let skip = findByText('button','Skip Ad');
                if(skip) click(skip);

                // Success
                if(url.includes('/success')){
                    let open = findByText('button','Open');
                    if(open){
                        click(open);
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

        for _ in range(5):
            nuke_ads(sb)
            time.sleep(1)

        # Renew
        print("🔍 点击 Renew")
        for _ in range(10):
            nuke_ads(sb)
            if extreme_click(sb, "renew"):
                print("✅ Renew 成功")
                break
            time.sleep(1)

        screenshot(sb, "after_renew.png")

        time.sleep(3)

        for _ in range(5):
            nuke_ads(sb)
            time.sleep(1)

        # Open
        print("🎯 点击 Open")
        extreme_click(sb, "open")

        time.sleep(5)

        # 👇 关键：尝试切窗口（防炸）
        try:
            handles = sb.driver.window_handles
            if len(handles) > 1:
                sb.switch_to_window(handles[-1])
        except:
            print("⚠️ 浏览器已跳转或关闭，继续执行")

        # 👇 注入 Linkvertise 自动处理
        inject_linkvertise_bot(sb)

        print("⏳ 等待 Linkvertise 自动完成...")
        time.sleep(30)

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