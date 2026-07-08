#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import os
from datetime import datetime, timezone

# ===== 配置 =====
PANEL_URL   = "https://panel.orihost.com"
SERVER_ID   = "670475f5"
SERVER_UUID = "670475f5-1206-48d3-b4ab-e86d75f5a3fd"
RENEWAL_MAX = 21

COOKIE     = os.environ.get("ORI_COOKIE", "")
TG_BOT     = os.environ.get("TG_BOT", "")
GOST_PROXY = os.environ.get("GOST_PROXY", "")

TG_ID, TG_TOKEN = TG_BOT.split(",", 1) if TG_BOT else (None, None)

# ===== 代理 =====
if GOST_PROXY:
    PROXIES = {
        "http":  "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8080"
    }
    print("🛡️ 使用 GOST 代理")
else:
    PROXIES = None
    print("🌐 直连（可能失败）")

# ===== 工具 =====
def send_tg(msg):
    if not TG_ID or not TG_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_ID, "text": msg},
            timeout=10
        )
    except:
        pass

def make_session(cookie):
    s = requests.Session()

    if PROXIES:
        s.proxies.update(PROXIES)

    s.headers.update({"User-Agent": "Mozilla/5.0"})

    for c in cookie.split(";"):
        if "=" in c:
            k, v = c.strip().split("=", 1)
            s.cookies.set(k, v, domain="panel.orihost.com")

    s.get(f"{PANEL_URL}/server/{SERVER_ID}")

    xsrf = s.cookies.get("XSRF-TOKEN")
    if not xsrf:
        raise Exception("XSRF 获取失败")

    return s, requests.utils.unquote(xsrf)

def headers(xsrf):
    return {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": xsrf,
        "Referer": f"{PANEL_URL}/server/{SERVER_ID}",
    }

# ===== 信息 =====
def get_info(s, h):
    r = s.get(f"{PANEL_URL}/api/client/servers/{SERVER_ID}", headers=h)
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

# ===== 核心续期 =====
def do_renew(s, h):
    # 1️⃣ begin
    r = s.post(f"{PANEL_URL}/api/client/servers/{SERVER_UUID}/renew/begin", headers=h)

    if not r.ok:
        print("❌ begin失败", r.text[:200])
        return False

    data = r.json()
    ad_url = data["url"]
    wait   = data["dwell_seconds"]

    print(f"🌐 广告: {ad_url}")
    print(f"⏳ 停留: {wait}s")

    # 2️⃣ 打开广告（必须）
    try:
        s.get(ad_url, timeout=20)
    except:
        print("⚠️ 广告访问失败（继续）")

    # 3️⃣ 等待
    time.sleep(wait + 3)

    # 4️⃣ claim
    r2 = s.post(f"{PANEL_URL}/api/client/servers/{SERVER_UUID}/renew/claim", headers=h)

    if r2.status_code in (200,204):
        print("✅ claim成功")
        return True
    else:
        print("❌ claim失败", r2.text[:200])
        return False

# ===== 主 =====
def main():
    if not COOKIE:
        raise Exception("缺少 ORI_COOKIE")

    s, xsrf = make_session(COOKIE)
    h = headers(xsrf)

    # 验证IP
    try:
        ip = s.get("https://api.ipify.org?format=json", timeout=10).json()["ip"]
        print("🌐 当前IP:", ip)
    except:
        print("⚠️ IP检测失败")

    renewal, days = get_info(s, h)
    print(f"📅 当前: {renewal} 次 / {days} 天")

    count = 0

    while renewal < RENEWAL_MAX:
        ok = do_renew(s, h)
        if not ok:
            break

        count += 1
        time.sleep(5)

        renewal, days = get_info(s, h)
        print(f"➡️ 已续: {renewal}")

    print(f"🎉 完成: {count} 次")

    send_tg(f"Orihost续期\n次数: {count}\n剩余: {days}天")

if __name__ == "__main__":
    main()