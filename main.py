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

REMEMBER_TOKEN      = os.environ.get("ORI_COOKIE", "")
TG_BOT              = os.environ.get("TG_BOT", "")
ORIHOST_GOST_PROXY  = os.environ.get("ORIHOST_GOST_PROXY", "")

TG_ID, TG_TOKEN = TG_BOT.split(",", 1) if TG_BOT else (None, None)

# ===== 代理 =====
if ORIHOST_GOST_PROXY:
    PROXIES = {
        "http":  "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8080"
    }
    print("🛡️ 使用 GOST 代理")
else:
    PROXIES = None
    print("🌐 直连模式（可能失败）")

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

def make_session(token):
    s = requests.Session()

    if PROXIES:
        s.proxies.update(PROXIES)

    s.headers.update({"User-Agent": "Mozilla/5.0"})

    # 只设置 remember_web
    s.cookies.set(
        "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d",
        token,
        domain="panel.orihost.com"
    )

    # 刷页面拿 XSRF
    s.get(f"{PANEL_URL}/server/{SERVER_ID}", timeout=15)

    xsrf = s.cookies.get("XSRF-TOKEN")
    if not xsrf:
        raise Exception("❌ XSRF 获取失败（Cookie失效）")

    return s, requests.utils.unquote(xsrf)

def build_headers(xsrf):
    return {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": xsrf,
        "Referer": f"{PANEL_URL}/server/{SERVER_ID}",
    }

# ===== 查询 =====
def get_info(s, h):
    r = s.get(f"{PANEL_URL}/api/client/servers/{SERVER_ID}", headers=h, timeout=15)
    if not r.ok:
        raise Exception("获取服务器信息失败")

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

# ===== 续期 =====
def do_renew(s, h):
    try:
        # begin
        r = s.post(f"{PANEL_URL}/api/client/servers/{SERVER_UUID}/renew/begin", headers=h, timeout=15)

        if not r.ok:
            print("❌ begin失败:", r.text[:100])
            return False

        data = r.json()

        ad_url = data.get("url")
        wait   = data.get("dwell_seconds", 15)

        if not ad_url:
            print("⚠️ 没有广告（IP被识别）")
            return False

        print(f"🌐 广告: {ad_url}")
        print(f"⏳ 停留: {wait}s")

        # 打开广告
        try:
            s.get(ad_url, timeout=20)
        except:
            print("⚠️ 广告访问失败（继续）")

        time.sleep(wait + 3)

        # claim
        r2 = s.post(f"{PANEL_URL}/api/client/servers/{SERVER_UUID}/renew/claim", headers=h, timeout=15)

        if r2.status_code in (200, 204):
            print("✅ claim成功")
            return True
        else:
            print("❌ claim失败:", r2.text[:120])
            return False

    except Exception as e:
        print("❌ 异常:", e)
        return False

# ===== 主 =====
def main():
    if not REMEMBER_TOKEN:
        raise Exception("❌ 未设置 ORI_COOKIE")

    print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    s, xsrf = make_session(REMEMBER_TOKEN)
    h = build_headers(xsrf)

    # IP检测
    try:
        ip = s.get("https://api.ipify.org?format=json", timeout=10).json()["ip"]
        print("🌐 当前IP:", ip)
    except:
        print("⚠️ IP检测失败")

    renewal, days = get_info(s, h)
    print(f"📅 当前: {renewal} 次 / {days} 天")

    if renewal >= RENEWAL_MAX:
        print("⏭️ 已满21天，跳过")
        return

    count = 0

    while renewal < RENEWAL_MAX:
        ok = do_renew(s, h)
        if not ok:
            print("🛑 停止续期（IP可能不行）")
            break

        count += 1
        time.sleep(5)

        renewal, days = get_info(s, h)
        print(f"➡️ 当前续期: {renewal}")

    print(f"🎉 完成: {count} 次")

    send_tg(f"🎮 Orihost续期\n次数: {count}\n剩余: {days}天")

if __name__ == "__main__":
    main()