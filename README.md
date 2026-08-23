# ABS综合看板静态站点包

本目录由 `scripts/deploy_github_pages.py` 自动生成，用于发布到 GitHub Pages。

- 最新入口：`index.html`
- 最新来源：`deliverables/dashboards/01_latest/ABS综合看板_20260814.html`
- 历史归档：已下线（protected 模式不发布明文历史版本）
- 生成时间：`2026-08-23T10:57:57`
- 加密模式：`True`

安全说明：站点包为**客户端加密**门禁版本，`index.html` 只包含密文和本地解密逻辑，不包含明文看板。
注意：这是客户端加密而非服务端鉴权——密文、salt、IV 均随页面下发，访问者可离线尝试口令，无身份校验、撤销与审计能力。请使用高熵口令并定期轮换；若需身份级管控请迁移至 Cloudflare Access 等方案。
