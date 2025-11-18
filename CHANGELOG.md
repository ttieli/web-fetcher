# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-11-18

### Added
- **Google搜索优化**: 完整的搜索结果提取（含snippet、图片、相关搜索）
- **Snippet提取**: 优化snippet提取逻辑，提供纯净的描述性文字
- **图片展示**: 提取3+张搜索结果图片及缩略图
- **URL格式化**: 所有链接格式化为Markdown超链接
- **项目文档**: 重构README.md，添加徽章、FAQ、贡献指南

### Changed
- 清理output文件夹的测试输出文件
- 整理docs文件夹结构，移除空文件夹
- 移动开发文档到docs/目录

### Fixed
- Google搜索snippet提取过滤条件过严问题
- 文档结构混乱，难以导航问题

## [1.0.0] - 2025-11-17

### Added
- **CDP集成**: 完整的Chrome DevTools Protocol支持
- **三级回退**: urllib → CDP → Selenium智能回退机制
- **模块化重组**: 清晰的项目结构
- **一键部署**: bootstrap.sh/ps1自动安装脚本
- **智能路由**: 基于域名和内容类型的自动路由

### Features
- 微信公众号内容提取
- 小红书图文内容提取
- Wikipedia多语言支持
- 通用网站自动适配
- YAML模板系统

## [0.9.0] - Initial Release

- 基础网页抓取功能
- Selenium集成
- Markdown输出
