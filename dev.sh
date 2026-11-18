#!/usr/bin/env bash
# 本地预览脚本。自动使用已安装的 Node 22.23.5（系统自带 22.22.2 版本过低）。
# 用法：./dev.sh  然后浏览器打开终端显示的地址（通常是 http://localhost:4321/DearMe/）

set -e
cd "$(dirname "$0")"

export PATH="$HOME/.workbuddy/node22/bin:$HOME/.workbuddy/bin:$PATH"
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
export NODE_OPTIONS=""

exec pnpm dev
