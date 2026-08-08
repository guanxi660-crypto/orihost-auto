#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from curl_cffi import requests
import urllib.parse
import time
import os
import random
from datetime import datetime, timezone

# ===== 配置 =====
PANEL_URL   = "https://panel.orihost.com"
SERVER_ID   = "aeffa7b5"
SERVER_UUID = "aeffa7b5-f855-4361-9983-b919771e619a"
RENEWAL_MAX = 21

REMEMBER_TOKEN = os.environ.get("ORI_COOKIE", "")
TG_BOT         = os.environ.get("TG_BOT", "")
GOST_PROXY     = os.environ.get("ORIHOST_GOST_PROXY", "")

TG_ID, TG_TOKEN = TG_BOT.split(",", 1) if TG_BOT else (None, None)

# ===== 代理 =====
if GOST_PROXY:
    PROXIES = {"http": GOST_PROXY, "https": GOST_PROXY}
    print("🛡️ 代理:", GOST_PROXY)
else:
    PROXIES = None
    print("🌐 直连")

# ===== 工具 =====
def send_tg(msg):
    if not TG_ID or not TG_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_ID, "text": msg},
            timeout=10,
            impersonate="chrome120"
        )
    except:
        pass

def make_session(token):
    s = requests.Session(impersonate="chrome120")

    if PROXIES:
        s.proxies.update(PROXIES)

    s.headers.update({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    s.cookies.set(
        "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d",
        token,
        domain="panel.orihost.com"
    )

    for i in range(5):
        try:
            r = s.get(f"{PANEL_URL}/dashboard", timeout=20)
            xsrf = s.cookies.get("XSRF-TOKEN")
            if xsrf:
                return s, urllib.parse.unquote(xsrf)
            time.sleep(2)
        except:
            time.sleep(2)

    raise Exception("❌ XSRF失败")

def build_headers(xsrf):
    return {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": xsrf,
        "Referer": f"{PANEL_URL}/server/{SERVER_ID}",
    }

def refresh_xsrf(s):
    try:
        s.get(f"{PANEL_URL}/dashboard", timeout=10)
        xsrf = s.cookies.get("XSRF-TOKEN")
        if xsrf:
            return urllib.parse.unquote(xsrf)
    except:
        pass
    return None

# ===== 信息 =====
def get_info(s, h):
    r = s.get(f"{PANEL_URL}/api/client/servers/{SERVER_ID}", headers=h)
    if not r.ok:
        raise Exception("获取信息失败")

    data = r.json()["attributes"]

    renewal = data.get("renewal", 0)

    expires = data.get("expires_at")
    if expires:
        exp = datetime.fromisoformat(expires.replace("Z","+00:00"))
        now = datetime.now(timezone.utc)
        days = round((exp-now).total_seconds()/86400,1)
    else:
        days = None

    return renewal, days

# ===== cooldown =====
def check_cooldown(s, h):
    try:
        r = s.get(f"{PANEL_URL}/api/client/servers/{SERVER_UUID}/renew/cooldown", headers=h, timeout=10)
        if r.ok:
            sec = r.json().get("seconds", 0)
            return sec
    except:
        pass
    return 999

# ===== 广告模拟 =====
def visit_ad(s, url, wait):
    try:
        s.get(url, timeout=20)
    except:
        pass

    # 模拟停留
    t = wait + random.randint(2,5)
    print(f"⏳ 停留 {t}s")
    time.sleep(t)

# ===== 核心续期 =====
def do_renew(s, h):
    try:
        # cooldown检查
        cd = check_cooldown(s, h)
        if cd > 0:
            print(f"⏳ 冷却中: {cd}s")
            time.sleep(cd)
            return False

        # begin
        r = s.post(f"{PANEL_URL}/api/client/servers/{SERVER_UUID}/renew/begin", headers=h, timeout=20)

        if not r.ok:
            print("❌ begin失败")
            return False

        data = r.json()
        ad_url = data.get("url")
        wait   = data.get("dwell_seconds", 15)

        if not ad_url:
            print("⚠️ 无广告")
            return False

        print("🌐 广告已获取")

        visit_ad(s, ad_url, wait)

        # claim（带重试）
        for i in range(3):
            r2 = s.get(f"{PANEL_URL}/api/client/renewal/complete", headers=h, timeout=20)

            if r2.status_code in (200,204):
                print("✅ 成功")
                return True

            # 尝试刷新XSRF
            new_xsrf = refresh_xsrf(s)
            if new_xsrf:
                h["X-XSRF-TOKEN"] = new_xsrf

            time.sleep(2)

        print("❌ claim失败")
        return False

    except Exception as e:
        print("❌ 异常:", e)
        return False

# ===== 主 =====
def main():
    if not REMEMBER_TOKEN:
        raise Exception("❌ 未设置 ORI_COOKIE")

    print("🕐", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    s, xsrf = make_session(REMEMBER_TOKEN)
    h = build_headers(xsrf)

    try:
        ip = s.get("https://api.ipify.org?format=json", timeout=10).json()["ip"]
        short_ip = ".".join(ip.split(".")[:2])
        print("🌐 IP:", short_ip)
    except Exception as e:
        print("❌ 获取IP失败:", e)

    renewal, days = get_info(s, h)
    print(f"📅 当前: {renewal} / {days}天")

    if renewal >= RENEWAL_MAX:
        print("⏭️ 已满")
        return

    count = 0

    while renewal < RENEWAL_MAX:
        ok = do_renew(s, h)
        if not ok:
            break

        count += 1
        time.sleep(random.randint(3,7))

        renewal, days = get_info(s, h)
        print(f"➡️ {renewal}")

    print(f"🎉 完成 {count} 次")

    send_tg(f"Orihost续期\n次数:{count}\n剩余:{days}天")

# ===== 入口 =====
if __name__ == "__main__":
    main()
