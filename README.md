# 中国电信招投标查询 Skill

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 查询中国电信阳光采购网招投标信息的 Claude Skill，支持省份、关键词、公告分类筛选。

## ✨ 功能特性

- 🔍 **多维度查询** - 支持省份、关键词、公告分类组合筛选
- 📅 **时间筛选** - 支持查询近 X 天的最新招投标信息
- 📊 **分类齐全** - 涵盖招标公告、询比公告、采购结果公示等 13 类公告
- 🗺️ **全国覆盖** - 支持全国及 31 个省市自治区
- 📋 **友好输出** - 默认 Markdown 表格，支持详细模式和 JSON 导出
- 🔍 **详情查看** - 支持通过API获取公告完整内容
- 🌐 **智能绕过** - 对招标公告类型自动使用浏览器回退策略绕过BotSec拦截

## 🚀 快速开始

### 安装依赖

```bash
pip install aiohttp beautifulsoup4
```

### 基础用法

```bash
# 1. 查看某省近7天的招投标信息
python search.py --province "河南" --days 7

# 2. 查看某省某关键字的招投标信息
python search.py --province "北京" --keyword "大模型"

# 3. 查看某关键字全国的招投标信息
python search.py --province "全国" --keyword "服务器" --max-items 50

# 4. 查看具体标的中标及公示信息
python search.py --keyword "郑州大模型" --category "采购结果公示"

# 5. 查看某关键字全国的中标及公示信息
python search.py --keyword "大模型" --category "采购结果公示"
```

## 📖 详细文档

### search.py - 主查询脚本

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--province` | `-p` | 省份名称 | `"河南"`, `"北京"`, `"全国"` |
| `--keyword` | `-k` | 搜索关键词 | `"大模型"`, `"服务器"` |
| `--category` | `-c` | 公告分类 | `"招标公告"`, `"采购结果公示"` |
| `--days` | `-d` | 近X天的数据 | `7`, `30` |
| `--max-items` | `-m` | 最大返回条数 | 默认 `20` |
| `--output` | `-o` | 输出JSON文件 | `results.json` |
| `--detail` | - | 详细格式 | 显示完整项目信息，**自动获取公告正文** |

### detail.py - 获取公告详情

| 参数 | 说明 | 示例 |
|------|------|------|
| `--id` | 公告ID (docId) | `"4793454332945260544"` |
| `--type` | 公告类型代码 | `"ResultAnnounc"`, `"PurchaseAnnounceBasic"` |
| `--security-code` | 安全验证码 | `"973dc112651e05ab97fce08d7e4cad8b"` |
| `--raw` | 输出原始JSON | （可选）|

### 支持的省份

```bash
python list_provinces.py
```

全国、北京、天津、河北、山西、内蒙古、辽宁、吉林、黑龙江、上海、江苏、浙江、安徽、福建、江西、山东、河南、湖北、湖南、广东、广西、海南、重庆、四川、贵州、云南、西藏、陕西、甘肃、青海、宁夏、新疆

### 支持的公告分类

```bash
python list_categories.py
```

| 分类名称 | 说明 |
|---------|------|
| 资格预审公告 | 项目前期资格审查 |
| 招标公告 | 正式招标信息 |
| 询比公告 | 询价比较 |
| 谈判采购公告 | 竞争性谈判 |
| **采购结果公示** | **中标结果公示** |
| 直接采购公示 | 单一来源采购 |
| 澄清公示 | 招标澄清说明 |

## 💡 使用示例

### 查看河南省最近3天的采购结果

```bash
python search.py --province "河南" --days 3 --category "采购结果公示"
```

输出：
```markdown
### 查询结果：河南  采购结果公示 （近3天）

**共找到 5 条记录**

| 序号 | 标题 | 省份 | 分类 | 日期 |
| --- | --- | --- | --- | --- |
| 1 | 中国电信郑州分公司... | 河南 | 采购结果 | 2026-03-01 |
```

### 查看全国大模型相关招标公告

```bash
python search.py --keyword "大模型" --province "全国" --category "招标公告" --max-items 50
```

### 查看具体项目的详细信息

```bash
python search.py --keyword "郑州分公司2026年大模型" --detail
```

### 保存结果到JSON文件

```bash
python search.py --keyword "服务器" --province "全国" --output results.json
```

### 获取公告详情

先通过搜索获取公告的 `docId`、`docTypeCode` 和 `securityViewCode`，然后使用 detail.py：

```bash
# 查看公告详情（格式化输出）
python detail.py --id "4793454332945260544" --type "ResultAnnounc" --security-code "973dc112651e05ab97fce08d7e4cad8b"

# 查看原始JSON数据
python detail.py --id "4793454332945260544" --type "ResultAnnounc" --security-code "973dc112651e05ab97fce08d7e4cad8b" --raw
```

**支持的通知类型：**
- `ResultAnnounc` - 采购结果公示
- `PurchaseAnnounceBasic` - 采购公告
- `CompareSelect` - 比选公告
- `TenderAnnouncement` - 招标公告
- `Prequalfication` - 资格预审

## 🔧 技术实现

### 混合策略详情获取

由于中国电信阳光采购网对招标公告类型启用了BotSec防护，Python直接请求会被拦截（403错误）。本工具实现了智能混合策略：

1. **API优先**: 首先尝试使用Python aiohttp直接请求API
2. **浏览器回退**: 对于招标公告类型或被拦截的请求，自动切换到浏览器执行fetch
3. **数据统一**: 无论通过哪种方式获取，返回的数据格式保持一致

### 浏览器自动化依赖

使用浏览器回退功能需要：
1. Chrome浏览器已安装
2. 启动Chrome时启用远程调试端口（`--remote-debugging-port=9222`）
3. `browser` skill可用（位于 `~/.claude/skills/browser`）

启动Chrome：
```bash
cd ~/.claude/skills/browser

# 有图形界面模式（适合本地开发）
node scripts/start.cjs --profile

# 无头模式（适合服务器环境，无图形界面）
node scripts/start.cjs --headless --profile
```

## 🔧 作为 Claude Skill 使用

将本项目克隆到 Claude skills 目录：

```bash
cd ~/.claude/skills
git clone https://github.com/你的用户名/tender-search.git
```

然后在 Claude 中可以直接说：

- "查一下河南最近7天的招投标信息"
- "搜索全国大模型的中标公示"
- "看看北京服务器项目的招标公告"

## 📁 项目结构

```
tender-search/
├── README.md              # 本文件
├── SKILL.md               # Claude Skill 说明
├── search.py              # 主查询脚本
├── detail.py              # 获取公告详情
├── list_provinces.py      # 列出省份
└── list_categories.py     # 列出公告分类
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
