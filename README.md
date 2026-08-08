# Orihost Auto Renew

基于 [yanyumm1/orihost-auto](https://github.com/yanyumm1/orihost-auto) fork 改进的 **Orihost 免费服务器自动续期** 脚本。

> 通过模拟"访问广告"为 Orihost 面板上的免费服务器续期，由 GitHub Actions 定时执行，全程无需人工干预。

## ✨ 本 fork 的改进

- ✅ **修复 GOST 代理失效 bug**：原版 `if: ${{ env.ORIHOST_GOST_PROXY != '' }}` 读的是 step 自己的 env（恒为 false），代理步骤从未执行过；改为 Secret 提升到 job 级 env、`if` 用 `env.X` 判断（`if` 条件不能用 `secrets` 上下文，GHA 硬限制）
- ✅ **新增 xray 代理**（`scripts/setup_proxy.sh`，收编自 eooce 系四协议解析脚本）：支持 vless / vmess / trojan / socks5 分享链接，自动起本地 SOCKS5:1080 + HTTP:1081 双入站
- ✅ **代理优先级**：`NODE_LINK`（xray）→ `ORIHOST_GOST_PROXY`（GOST 兜底）→ 直连
- ✅ **修复 xray 证书校验坑**：锁 v1.8.24（v24+ 移除 `allowInsecure`），家宽/自建 CN-only 证书可正常连接，默认 `insecure=true`
- ✅ 简化 checkout（不再拉取"自己仓库"），Secrets 一律走 env 块不内联进脚本

## 🚀 使用方法

### 1. Fork 本仓库（或直接使用）

### 2. 配置 Secrets

仓库 → **Settings → Secrets and variables → Actions**，添加：

| Secret | 必填 | 说明 |
|---|---|---|
| `ORI_COOKIE` | ✅ | Orihost 面板登录 cookie。浏览器登录 `panel.orihost.com` → F12 → Application → Cookies → 复制 `remember_web_59ba36...` 的 **value** |
| `NODE_LINK` | 🟡 | 代理节点分享链接（vless/vmess/trojan/socks5 四协议），xray 出口，**推荐**（防面板按 IP 限制） |
| `ORIHOST_GOST_PROXY` | 🟡 | 备用代理地址（`NODE_LINK` 未配置时生效） |
| `TG_BOT` | 🟡 | 续期结果推送，格式 `chat_id,token`（逗号分隔） |

> ⚠️ `NODE_LINK` 与 `ORIHOST_GOST_PROXY` **至少配一个**，否则以 GitHub 机房 IP 直连，续期可能被面板限制。

### 3. 按需修改服务器配置

编辑 `main.py` 顶部：

```python
PANEL_URL   = "https://panel.orihost.com"
SERVER_ID   = "670475f5"                     # 面板 URL 中的短 ID
SERVER_UUID = "670475f5-1206-48d3-b4ab-e86d75f5a3fd"  # API 用的完整 UUID
RENEWAL_MAX = 21                             # 最多续期次数
```

### 4. 运行

- **手动**：Actions → **Orihost-Renew** → **Run workflow**
- **定时**：工作流已配置 cron `0 19 */12 * *`（每 12 天 19:00 UTC，可在 `.github/workflows/main.yml` 调整）

日志里看到 `✅ 代理连接成功` 即代理链路正常；`📅 当前: N / N天` 显示续期进度。

## 🧹 自动清理

`.github/workflows/Cleanup-Old-Workflow.yml` 每周自动清理旧 workflow 运行记录与 7 天前的 Artifacts，清理日志写入 `CLEANUP_LOG.md`（不再覆盖本 README）。

## 🙏 致谢

- [yanyumm1/orihost-auto](https://github.com/yanyumm1/orihost-auto) —— 原始续期脚本与工作流
- [eooce](https://github.com/eooce) —— 免费托管续期方案与 xray 四协议解析脚本
- [ginuerzh/gost](https://github.com/ginuerzh/gost) —— GOST 代理
- [XTLS/Xray-core](https://github.com/XTLS/Xray-core) —— xray 内核
