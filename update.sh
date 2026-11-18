#!/usr/bin/env bash
# 一键把本地改动推送到 GitHub，触发自动部署。
# 用法：
#   ./update.sh                    # 自动生成带时间戳的提交说明
#   ./update.sh "修改了首页文案"   # 自定义提交说明

set -e
cd "$(dirname "$0")"

MSG="${1:-Update site $(date '+%Y-%m-%d %H:%M')}"

if [ -z "$(git status --porcelain)" ]; then
  echo "没有需要提交的改动。"
  exit 0
fi

git add -A
git commit -m "$MSG"
git push origin main

echo ""
echo "推送完成，GitHub Actions 正在自动构建部署（约 1 分钟）。"
echo "页面地址：https://RiverDriven.github.io/DearMe/"
echo "查看部署状态：gh run list --repo RiverDriven/DearMe"
