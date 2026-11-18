# DearMe 官网

DearMe 的单页静态宣传站：一个 `index.html` + `assets/`，没有构建步骤，没有依赖。

线上地址：<https://RiverDriven.github.io/DearMe/>

## 结构

```
index.html            整站（三个视图 + 样式 + 脚本，全部内联）
assets/
  dearme-icon-256.png   导航与页脚图标
  dearme-icon-512.png   首屏大图标（圆形透明底）
  clay-clouds.jpg       首屏云海背景
  clay-door.jpg         故事区配图
  clay-objects.jpg      故事页配图
_preview 相关：preview.sh / update.sh
_archive-astro/       原 Astro 模板工程（本地保留，已在 .gitignore 中忽略）
```

## 三个视图（hash 路由，两级导航）

| 路径 | 内容 |
|---|---|
| `/` | 首页：首屏 + 三条价值 + 功能预览 + 四步闭环 + 引言 + 故事预告 + 下载 |
| `/#/features` | 功能：六个模块（心愿 / 计划 / 记录 / 关怀日志 / 星图 / 记录页双视图）+ 设计原则 |
| `/#/story` | 故事：lobus 与 RiverDriven、产品由来、时间线、联系 |

右上角「中 / EN」切换语言，选择记在 `localStorage`。

## 本地预览

```bash
./preview.sh          # 默认 http://localhost:4321/
```

## 需要替换的三处占位

1. **下载链接**：现在点「App Store 下载」会弹出「正在审核 + 留邮箱」弹层。上架后把按钮改成直链即可——把 `data-open-dl` 属性换成 `onclick="location.href='https://apps.apple.com/...'"`，或直接在弹层里放链接。
2. **邮箱订阅**：弹层表单只做前端提示，不保存、不发送（页面底部有说明）。要真订阅就接一个表单服务，改 `#dlForm` 的 submit 逻辑。
3. **联系邮箱**：故事页与页脚的 `hello@lobus.studio` 是占位，换成你的真实邮箱。

## 部署

推送 `main` 即触发 `.github/workflows/deploy.yml`：把 `index.html` 与 `assets/` 打包成 Pages 产物发布，不走构建。

```bash
./update.sh "改了什么"    # 提交并推送
```

首次切换到静态站时，如果仓库的 Pages 来源设的是 "GitHub Actions" 就不用动；如果设成了 "Deploy from a branch"，要在仓库 Settings → Pages 里改成 **GitHub Actions**。

## 归档的旧工程

原来的 Astro（AppPage 模板）工程整体在 `_archive-astro/`，仍可直接 `pnpm install && pnpm dev` 跑起来；确认不再需要后删掉即可。
