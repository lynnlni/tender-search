# 中国电信招投标查询 Skill

查询中国电信阳光采购网的招投标信息，支持省份、关键词、分类筛选。

## 支持的查询场景

1. **查看某省近x天的招投标信息**
2. **查看某些省某关键字的招投标信息**
3. **查看某关键字全国的招投标信息**
4. **查看某个具体标的中标及公示信息**（通过关键词精确匹配）
5. **查看某关键字全国的中标及公示信息**

## 脚本

### search.py - 主查询脚本

**用途**: 查询招投标公告信息

**参数**:
- `--province`, `-p`: 省份名称（如：河南、北京、全国）
- `--keyword`, `-k`: 搜索关键词（如：大模型、服务器）
- `--category`, `-c`: 公告分类（如：招标公告、询比公告、采购结果公示）
- `--days`, `-d`: 近X天的数据（自动计算日期范围并过滤）
- `--max-items`, `-m`: 最大返回条数（默认20）
- `--output`, `-o`: 输出JSON文件路径（可选）
- `--detail`: 显示详细信息格式（可选）

**使用示例**:

```bash
# 1. 查看某省近x天的招投标信息
python search.py --province "河南" --days 7

# 2. 查看某些省某关键字的招投标信息
python search.py --province "北京" --keyword "大模型"
python search.py --province "河南" --keyword "服务器" --category "招标公告"

# 3. 查看某关键字全国的招投标信息
python search.py --province "全国" --keyword "服务器" --max-items 50

# 4. 查看某个具体标的中标及公示信息（通过关键词精确匹配）
python search.py --keyword "郑州分公司2026年大模型" --category "采购结果公示"

# 5. 查看某关键字全国的中标及公示信息
python search.py --keyword "大模型" --province "全国" --category "采购结果公示"

# 其他示例
# 查看河南最近3天的采购结果公示
python search.py --province "河南" --days 3 --category "采购结果公示"

# 查看全国大模型相关招标公告（前50条）
python search.py --keyword "大模型" --province "全国" --category "招标公告" --max-items 50

# 查看具体项目的详细信息
python search.py --keyword "郑州分公司2026年大模型" --detail

# 保存结果到JSON文件
python search.py --keyword "服务器" --province "全国" --output results.json
```

**返回格式**:
脚本输出 Markdown 表格到控制台，包含：序号、标题、省份、分类、日期。
可配合 `--output` 保存完整 JSON 数据。

### list_provinces.py - 列出省份

**用途**: 显示所有支持的省份代码

```bash
python list_provinces.py
```

### list_categories.py - 列出分类

**用途**: 显示所有公告分类代码

```bash
python list_categories.py
```

## 支持的省份（32个）

全国、北京、天津、河北、山西、内蒙古、辽宁、吉林、黑龙江、上海、
江苏、浙江、安徽、福建、江西、山东、河南、湖北、湖南、广东、
广西、海南、重庆、四川、贵州、云南、西藏、陕西、甘肃、青海、宁夏、新疆

## 支持的公告分类（13类）

| 分类名称 | 说明 |
|---------|------|
| 全部 | 所有类型 |
| 资格预审公告 | 项目前期资格审查 |
| 招标公告 | 正式招标信息 |
| 询比公告 | 询价比较 |
| 谈判采购公告 | 竞争性谈判 |
| 评价检测公告 | 评估检测类 |
| 政企合作招募公告 | 政企合作项目 |
| IPTV内容合作招募公告 | IPTV内容合作 |
| **采购结果公示** | **中标结果公示** |
| 直接采购公示 | 单一来源采购 |
| 澄清公示 | 招标澄清说明 |
| 政企合作招募结果公示 | 政企合作结果 |
| IPTV内容合作评审结果公示 | IPTV评审结果 |

## 依赖

```bash
pip install aiohttp
```

## 提示词示例

当使用此 skill 时，可以直接说：

- "查一下河南最近7天的招投标信息"
- "搜索全国大模型相关的中标公示"
- "看看北京服务器项目的招标公告"
- "找一下郑州大模型项目的采购结果"
