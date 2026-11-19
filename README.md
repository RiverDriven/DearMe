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
copy/
  copy.json           214 条双语文案的汇总表（从 index.html 导出）
  snapshots/latest.json  上一次的快照，用来算 diff
  history.json        每次改动记录（新增/修改/删除 + 前后文）
docs/
  copy-review.html    可浏览的文案对照页（中英左右对照 + 搜索 + 版本记录）
  copy-changelog.md   版本记录（Markdown，便于直接看 diff）
tools/copy.py         文案表工具（extract / verify / diff / report）
preview.sh / update.sh
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

## 文案表与版本记录

文案仍然只写在 `index.html` 的 `data-zh` / `data-en` 上，`data-key` 是它的身份证（形如 `home.hero.05`、`features.feat2.03`）。`copy/copy.json` 是从页面导出的镜像，用来汇总、比对、留痕。

```bash
python3 tools/copy.py all "改了首屏主标题"   # 抽文案 → 算 diff → 刷新对照页
python3 tools/copy.py verify                # 校验页面与文案表是否同步（CI 也跑这个）
python3 tools/copy.py report                # 只重新生成 docs/copy-review.html
```

改完文案后的标准动作：`all` → 打开 `docs/copy-review.html` 看一眼 → `./update.sh`。

`docs/copy-review.html` 里能看三样东西：全站 214 条中英对照（带搜索）、**重复文案**（同一句话出现在几个 key 上，双语站最容易只改一处）、**版本记录**（每次改了哪条、前后原文、对应 commit）。`docs/copy-changelog.md` 是同一份记录的 Markdown 版。

## 部署

推送 `main` 即触发 `.github/workflows/deploy.yml`：把 `index.html` 与 `assets/` 打包成 Pages 产物发布，不走构建。

```bash
./update.sh "改了什么"    # 提交并推送
```

首次切换到静态站时，如果仓库的 Pages 来源设的是 "GitHub Actions" 就不用动；如果设成了 "Deploy from a branch"，要在仓库 Settings → Pages 里改成 **GitHub Actions**。

## 归档的旧工程

原来的 Astro（AppPage 模板）工程整体在 `_archive-astro/`，仍可直接 `pnpm install && pnpm dev` 跑起来；确认不再需要后删掉即可。
