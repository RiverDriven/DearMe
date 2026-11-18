#!/usr/bin/env bash
# 本地预览。纯静态站，只需要一个 HTTP 服务。
# 用法：./preview.sh  然后打开 http://localhost:4321/
# 线上是子路径 https://RiverDriven.github.io/DearMe/，页面内全是相对路径，两边一致。
set -e
cd "$(dirname "$0")"
PORT="${1:-4321}"
echo "预览地址：http://localhost:${PORT}/"
exec python3 -m http.server "$PORT"
