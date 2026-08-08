#!/bin/bash
# setup_proxy.sh - 代理节点解析与 xray-core 启动
# 支持协议: vless / vmess / trojan / socks5
# (xray 内核不支持 hysteria2/tuic/anytls，这些是 sing-box 特性)
export LC_ALL=C
set -e

# 默认测试节点（可通过环境变量覆盖）
export NODE_LINK=${NODE_LINK:-''}

if [ -z "$NODE_LINK" ]; then
  echo "[INFO] 未配置代理，直连模式"
  echo "IS_PROXY=false" >> $GITHUB_ENV
  exit 0
fi

if ! command -v jq &> /dev/null; then
  echo "[ERROR] jq 未安装，正在安装..."
  sudo apt-get update && sudo apt-get install -y jq
fi

if ! command -v unzip &> /dev/null; then
  echo "[ERROR] unzip 未安装，正在安装..."
  sudo apt-get update && sudo apt-get install -y unzip
fi

command -v curl &>/dev/null && COMMAND="curl -so" || command -v wget &>/dev/null && COMMAND="wget -qO" || { echo "Error: neither curl nor wget found" >&2; exit 1; }

# 固定 v1.8.24：xray v24+ 移除了 allowInsecure（改 pinnedPeerCertSha256），
# 家宽/自建节点证书多为旧式(CN-only/自签)，必须保留跳过校验能力
echo "[INFO] 使用 xray-core v1.8.24 (兼容 allowInsecure)"
latest_version=1.8.24

ARCH_RAW=$(uname -m)
case "${ARCH_RAW}" in
    'x86_64' | 'amd64')  ASSET='Xray-linux-64.zip' ;;
    'aarch64' | 'arm64') ASSET='Xray-linux-arm64-v8a.zip' ;;
    *) echo "不支持的架构: ${ARCH_RAW}"; exit 1 ;;
esac

$COMMAND xray.zip "https://github.com/XTLS/Xray-core/releases/download/v${latest_version}/${ASSET}"
unzip -o -q xray.zip -d xray-dist
mv xray-dist/xray ./
rm -rf "xray-dist" "xray.zip"
chmod +x xray

proto=$(echo "$NODE_LINK" | cut -d':' -f1)
content="${NODE_LINK#*://}"
content="${content%%#*}"

echo "[INFO] 协议: $proto"

# 初始化变量
outbound_type=""
outbound_server=""
outbound_port=""
outbound_uuid=""
outbound_flow=""
outbound_transport_type="tcp"
outbound_path="/"
outbound_host=""
outbound_security="none"
outbound_sni=""
outbound_fingerprint="chrome"
outbound_reality_pbk=""
outbound_reality_sid=""
outbound_password=""
outbound_username=""
outbound_password2=""
outbound_aid=0
outbound_scy="auto"
outbound_insecure="true"

# 辅助函数：URL 解码
url_decode() {
  local encoded="$1"
  printf '%b' "$(echo "$encoded" | sed 's/%/\\x/g')"
}

case "$proto" in
  vless)
    uuid_host="${content#*://}"
    uuid="${uuid_host%%@*}"
    rest="${uuid_host#*@}"
    if [[ "$rest" == *"?"* ]]; then
      host_port="${rest%%\?*}"
      query="${rest#*\?}"
    else
      host_port="$rest"
      query=""
    fi
    outbound_server="${host_port%:*}"
    outbound_port="${host_port#*:}"
    outbound_uuid="$uuid"
    outbound_type="vless"
    if [ -n "$query" ]; then
      flow=$(echo "$query" | grep -o 'flow=[^&]*' | cut -d= -f2)
      [ -n "$flow" ] && outbound_flow="$flow"
      ttype=$(echo "$query" | grep -o 'type=[^&]*' | cut -d= -f2)
      [ -n "$ttype" ] && outbound_transport_type="$ttype"
      path_raw=$(echo "$query" | grep -o 'path=[^&]*' | cut -d= -f2)
      if [ -n "$path_raw" ]; then
        path_decoded=$(url_decode "$path_raw")
        outbound_path="${path_decoded%%\?*}"
      fi
      host=$(echo "$query" | grep -o 'host=[^&]*' | cut -d= -f2)
      [ -n "$host" ] && outbound_host="$host"
      sec=$(echo "$query" | grep -o 'security=[^&]*' | cut -d= -f2)
      [ -n "$sec" ] && outbound_security="$sec"
      sni=$(echo "$query" | grep -o 'sni=[^&]*' | cut -d= -f2)
      [ -n "$sni" ] && outbound_sni="$sni"
      fp=$(echo "$query" | grep -o 'fp=[^&]*' | cut -d= -f2)
      [ -n "$fp" ] && outbound_fingerprint="$fp"
      pbk=$(echo "$query" | grep -o 'pbk=[^&]*' | cut -d= -f2)
      [ -n "$pbk" ] && outbound_reality_pbk="$pbk"
      sid=$(echo "$query" | grep -o 'sid=[^&]*' | cut -d= -f2)
      [ -n "$sid" ] && outbound_reality_sid="$sid"
      ins=$(echo "$query" | grep -o 'insecure=[^&]*' | cut -d= -f2)
      [ "$ins" = "1" ] || [ "$ins" = "true" ] && outbound_insecure="true"
      alins=$(echo "$query" | grep -o 'allowInsecure=[^&]*' | cut -d= -f2)
      [ "$alins" = "1" ] || [ "$alins" = "true" ] && outbound_insecure="true"
    fi
    [ -z "$outbound_host" ] && outbound_host="$outbound_server"
    [ -z "$outbound_sni" ] && outbound_sni="$outbound_server"
    ;;

  vmess)
    b64="${content}"
    mod=$(( ${#b64} % 4 ))
    if [ $mod -eq 2 ]; then b64="${b64}=="; elif [ $mod -eq 3 ]; then b64="${b64}="; fi
    decoded=$(echo "$b64" | base64 -d 2>/dev/null)
    if [ -z "$decoded" ]; then
      echo "[ERROR] VMess 解码失败"
      exit 1
    fi
    add=$(echo "$decoded" | jq -r '.add // ""')
    port=$(echo "$decoded" | jq -r '.port // 443')
    id=$(echo "$decoded" | jq -r '.id // ""')
    aid=$(echo "$decoded" | jq -r '.aid // 0')
    net=$(echo "$decoded" | jq -r '.net // "tcp"')
    tls=$(echo "$decoded" | jq -r '.tls // ""')
    sni=$(echo "$decoded" | jq -r '.sni // ""')
    host=$(echo "$decoded" | jq -r '.host // ""')
    path_raw=$(echo "$decoded" | jq -r '.path // "/"')
    path_decoded=$(url_decode "$path_raw")
    outbound_path="${path_decoded%%\?*}"
    fp=$(echo "$decoded" | jq -r '.fp // "chrome"')
    scy=$(echo "$decoded" | jq -r '.scy // "auto"')
    outbound_type="vmess"
    outbound_server="$add"
    outbound_port="$port"
    outbound_uuid="$id"
    outbound_aid="$aid"
    outbound_scy="$scy"
    outbound_transport_type="$net"
    outbound_host="${host:-$add}"
    outbound_sni="${sni:-$add}"
    outbound_fingerprint="$fp"
    outbound_security="$tls"
    outbound_flow=""
    ;;

  trojan)
    pass_rest="${content#*://}"
    password="${pass_rest%%@*}"
    rest="${pass_rest#*@}"
    if [[ "$rest" == *"?"* ]]; then
      host_port="${rest%%\?*}"
      query="${rest#*\?}"
    else
      host_port="$rest"
      query=""
    fi
    outbound_server="${host_port%:*}"
    outbound_port="${host_port#*:}"
    outbound_password="$password"
    outbound_type="trojan"
    if [ -n "$query" ]; then
      ttype=$(echo "$query" | grep -o 'type=[^&]*' | cut -d= -f2)
      [ -n "$ttype" ] && outbound_transport_type="$ttype"
      path_raw=$(echo "$query" | grep -o 'path=[^&]*' | cut -d= -f2)
      if [ -n "$path_raw" ]; then
        path_decoded=$(url_decode "$path_raw")
        outbound_path="${path_decoded%%\?*}"
      fi
      host=$(echo "$query" | grep -o 'host=[^&]*' | cut -d= -f2)
      [ -n "$host" ] && outbound_host="$host"
      sni=$(echo "$query" | grep -o 'sni=[^&]*' | cut -d= -f2)
      [ -n "$sni" ] && outbound_sni="$sni"
      fp=$(echo "$query" | grep -o 'fp=[^&]*' | cut -d= -f2)
      [ -n "$fp" ] && outbound_fingerprint="$fp"
      ins=$(echo "$query" | grep -o 'insecure=[^&]*' | cut -d= -f2)
      [ "$ins" = "1" ] || [ "$ins" = "true" ] && outbound_insecure="true"
      alins=$(echo "$query" | grep -o 'allowInsecure=[^&]*' | cut -d= -f2)
      [ "$alins" = "1" ] || [ "$alins" = "true" ] && outbound_insecure="true"
    fi
    [ -z "$outbound_host" ] && outbound_host="$outbound_server"
    [ -z "$outbound_sni" ] && outbound_sni="$outbound_server"
    ;;

  socks5|socks)
    if [[ "$content" == *"@"* ]]; then
      user_pass="${content%%@*}"
      host_port="${content#*@}"
      decoded=$(echo "$user_pass" | base64 -d 2>/dev/null || true)
      if [ -n "$decoded" ] && [[ "$decoded" == *":"* ]]; then
        outbound_username="${decoded%:*}"
        outbound_password2="${decoded#*:}"
      else
        if [[ "$user_pass" == *":"* ]]; then
          outbound_username="${user_pass%:*}"
          outbound_password2="${user_pass#*:}"
        else
          outbound_username="$user_pass"
          outbound_password2=""
        fi
      fi
    else
      host_port="$content"
    fi
    outbound_server="${host_port%:*}"
    outbound_port="${host_port#*:}"
    outbound_type="socks"
    ;;

  *)
    echo "[ERROR] 不支持的协议: $proto (xray 内核仅支持 vless/vmess/trojan/socks5)"
    exit 1
    ;;
esac

if [ -z "$outbound_server" ] || [ -z "$outbound_port" ]; then
  echo "[ERROR] 无法解析服务器地址或端口"
  exit 1
fi

# ============ xray outbound 生成 ============
# 生成 streamSettings（传输层 + TLS/Reality）
gen_stream() {
  local net="$1" sec="$2"
  local stream="{\"network\":\"$net\""
  case "$net" in
    ws)
      stream="$stream,\"wsSettings\":{\"path\":\"$outbound_path\",\"headers\":{\"Host\":\"$outbound_host\"}}"
      ;;
    grpc)
      stream="$stream,\"grpcSettings\":{\"serviceName\":\"$outbound_path\"}"
      ;;
    kcp)
      [ -n "$outbound_path" ] && [ "$outbound_path" != "/" ] && stream="$stream,\"kcpSettings\":{\"seed\":\"$outbound_path\"}"
      ;;
    http|h2)
      stream="$stream,\"httpSettings\":{\"host\":[\"$outbound_host\"],\"path\":\"$outbound_path\"}"
      ;;
  esac
  case "$sec" in
    tls)
      stream="$stream,\"security\":\"tls\",\"tlsSettings\":{\"serverName\":\"$outbound_sni\",\"allowInsecure\":true,\"fingerprint\":\"$outbound_fingerprint\"}"
      ;;
    reality)
      stream="$stream,\"security\":\"reality\",\"realitySettings\":{\"serverName\":\"$outbound_sni\",\"fingerprint\":\"$outbound_fingerprint\",\"publicKey\":\"$outbound_reality_pbk\",\"shortId\":\"$outbound_reality_sid\"}"
      ;;
    *)
      stream="$stream,\"security\":\"none\""
      ;;
  esac
  stream="$stream}"
  echo "$stream"
}

case "$outbound_type" in
  vless)
    users="{\"id\":\"$outbound_uuid\",\"encryption\":\"none\""
    [ -n "$outbound_flow" ] && users="$users,\"flow\":\"$outbound_flow\""
    users="$users}"
    jq_outbound="{\"protocol\":\"vless\",\"settings\":{\"vnext\":[{\"address\":\"$outbound_server\",\"port\":$outbound_port,\"users\":[$users]}]},\"streamSettings\":$(gen_stream "$outbound_transport_type" "$outbound_security")}"
    ;;
  vmess)
    jq_outbound="{\"protocol\":\"vmess\",\"settings\":{\"vnext\":[{\"address\":\"$outbound_server\",\"port\":$outbound_port,\"users\":[{\"id\":\"$outbound_uuid\",\"alterId\":$outbound_aid,\"security\":\"$outbound_scy\"}]}]},\"streamSettings\":$(gen_stream "$outbound_transport_type" "$outbound_security")}"
    ;;
  trojan)
    jq_outbound="{\"protocol\":\"trojan\",\"settings\":{\"servers\":[{\"address\":\"$outbound_server\",\"port\":$outbound_port,\"password\":\"$outbound_password\",\"level\":0}]},\"streamSettings\":$(gen_stream "$outbound_transport_type" "$outbound_security")}"
    ;;
  socks)
    if [ -n "$outbound_username" ]; then
      jq_outbound="{\"protocol\":\"socks\",\"settings\":{\"servers\":[{\"address\":\"$outbound_server\",\"port\":$outbound_port,\"users\":[{\"user\":\"$outbound_username\",\"pass\":\"$outbound_password2\"}]}]}}"
    else
      jq_outbound="{\"protocol\":\"socks\",\"settings\":{\"servers\":[{\"address\":\"$outbound_server\",\"port\":$outbound_port}]}}"
    fi
    ;;
esac

# 生成 xray 配置
cat << EOF > xray-config.json
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {"listen": "127.0.0.1", "port": 1080, "protocol": "socks", "settings": {"udp": true, "auth": "noauth"}},
    {"listen": "127.0.0.1", "port": 1081, "protocol": "http"}
  ],
  "outbounds": [$jq_outbound]
}
EOF

if ! jq empty xray-config.json 2>/dev/null; then
  echo "[ERROR] 生成的 xray 配置无效"
  exit 1
fi

echo "[INFO] ✅ xray 配置已生成"

# 清理旧进程
echo "[INFO] 清理旧进程..."
pkill -f xray 2>/dev/null || true
fuser -k 1080/tcp 2>/dev/null || true
sleep 2

./xray run -c xray-config.json > xray.log 2>&1 &
sleep 5

if ! pgrep -f xray > /dev/null; then
  echo "[ERROR] xray 进程启动失败，查看日志:"
  cat xray.log
  exit 1
fi

echo "[INFO] 测试代理连接..."
for i in {1..3}; do
  if curl -x socks5://127.0.0.1:1080 -s --max-time 15 https://api.ipify.org > /dev/null 2>&1; then
    echo "[INFO] ✅ 代理连接成功"
    echo "IS_PROXY=true" >> $GITHUB_ENV
    echo "PROXY_SERVER=socks5://127.0.0.1:1080" >> $GITHUB_ENV
    exit 0
  fi
  echo "[WARN] 尝试 $i/3..."
  sleep 3
done

echo "[ERROR] ❌ 代理连接失败"
echo "---- xray 日志 ----"
cat xray.log
exit 1
