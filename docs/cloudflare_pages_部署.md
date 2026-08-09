# Cloudflare Pages 国内加速部署

> 看板国内访问慢的根因:`codebluce.github.io` 走 GitHub CDN,国内常被墙/丢包,6MB 级单文件首字节很慢。
> 解决:在 Cloudflare Pages 上做一份镜像,指向 `gh-pages` 分支自动同步,国内走 CF 边缘节点免代理直连。
> **加密门禁不受影响**:`--protected` 模式的解密逻辑全在浏览器端,CF Pages 只托管加密壳 HTML,不接触明文看板与密码。

## 架构

```
deploy_github_pages.py --protected   ──►   gh-pages 分支(加密壳 HTML)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                                                   ▼
          GitHub Pages(海外/备用)                    Cloudflare Pages(国内主入口)
     codebluce.github.io/ABS-Toolbox/                  abs-toolbox.pages.dev
```

- 两条入口内容**完全一致**(都来自 gh-pages 的加密壳)。
- 发布流程不变:照旧跑 `deploy_github_pages.py --protected`,推到 gh-pages 后 CF Pages 自动构建同步。
- 国内用户走 `https://abs-toolbox.pages.dev`(免代理快),海外/备用走 GitHub Pages。

## 一次性接入(Cloudflare 控制台,人工操作)

1. 登录 Cloudflare Dashboard → Workers & Pages → Create application → Pages → Connect to Git。
2. 授权并选择 GitHub 仓库 `codebluce/ABS-Toolbox`。
3. 配置项:

   | 配置项 | 值 | 说明 |
   |---|---|---|
   | Project name | `ABS-Toolbox` | 决定 URL:`https://abs-toolbox.pages.dev`(CF 会自动补随机后缀,以控制台实际为准) |
   | Production branch | `gh-pages` | **不是 main**。发布内容在 gh-pages 分支 |
   | Framework preset | None | 纯静态,无框架 |
   | Build command | 留空 | gh-pages 已是产物,无需构建 |
   | Build output directory | `/`(或 `.`) | 直接用分支根目录 |
   | Root directory | 留空 | — |

4. Save and Deploy。首次构建会拉取 gh-pages 当前内容,1~2 分钟生成。
5. 构建完成后拿到实际 URL(形如 `https://abs-toolbox-xxxx.pages.dev`),回填到本文档「访问入口」与 `scripts/deploy_github_pages.py` 的 `CF_PAGES_URL`。

## 访问入口

> 以 Cloudflare 控制台实际分配的 URL 为准,创建后回填。

- **国内主入口**:`https://abs-toolbox.pages.dev`(待回填实际 URL)
- 海外/备用入口:`https://codebluce.github.io/ABS-Toolbox/`

两个入口都需要输入同一个访问密码(密码由 `deploy_github_pages.py --protected` 通过 `ABS_DASHBOARD_PASSWORD` 环境变量传入,只在发布时用于加密,不进仓库、不传 CF/GitHub)。

## 发布流程(不变)

```bash
# 发布加密门禁版到 gh-pages(GitHub Pages + Cloudflare Pages 同时更新)
ABS_DASHBOARD_PASSWORD="<访问密码>" PYTHONUTF8=1 .venv/bin/python \
  scripts/deploy_github_pages.py --protected
```

- 脚本推 gh-pages 后,GitHub Pages 即时生效;Cloudflare Pages 检测到 gh-pages push,自动触发一次构建(约 1~2 分钟)。
- 两边内容相同(同一 commit 的加密壳),密码一致即可在任一入口解锁。

## 为何选 CF Pages Git 集成(指向 gh-pages)

- `deliverables/dashboard_site/` 在 `.gitignore` 内,不进 main;真正发布内容在 gh-pages 分支。
- 加密密码每次由环境变量传入,不可能进仓库被 CF 读到——所以 CF 不能"读 main 目录自动构建",必须读**已是产物的 gh-pages 分支**。
- 指向 gh-pages + 无构建命令 = CF 纯做静态镜像同步,零脚本依赖、零密码泄漏面。

## 故障排查

| 现象 | 排查 |
|---|---|
| CF Pages 迟迟不更新 | 控制台 → 该 Pages 项目 → Deployments 看最近构建状态;确认 Production branch 仍是 `gh-pages` |
| CF URL 解不出看板(白屏/密码错误) | gh-pages 分支当前是否为 protected 版;密码是否与发布时一致 |
| CF 构建报"output directory 为空" | 确认 Build output directory 填的是 `/` 而非 `dashboard_site` |
| GitHub Pages 正常但 CF 404 | gh-pages 分支是否有 `.nojekyll`(有则 CF 同样不需要构建,正常);确认 CF 已授权私有/公开仓库读取 |

## 回滚

- 撤掉 CF Pages 镜像:Cloudflare 控制台删除该项目即可,GitHub Pages 入口不受影响。
- 本仓库无任何与 CF 强绑定的代码,删除后无残留。
