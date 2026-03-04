#!/usr/bin/env python3
"""列出所有公告分类"""

CATEGORY_CODES = {
    "全部": "",
    "资格预审公告": "xi9s",
    "招标公告": "e2no",
    "询比公告": "e3erht",
    "谈判采购公告": "e8vif",
    "评价检测公告": "ds3fd2s",
    "政企合作招募公告": "f1f7e",
    "IPTV内容合作招募公告": "sxax8",
    "采购结果公示": "n0eves",
    "直接采购公示": "ow7t",
    "澄清公示": "th4gie",
    "政企合作招募结果公示": "s1x5e",
    "IPTV内容合作评审结果公示": "rasxq"
}

print("### 支持的公告分类\n")
print("| 分类名称 | 代码 |")
print("|----------|------|")

for name, code in CATEGORY_CODES.items():
    code_display = f"`{code}`" if code else "(全部)"
    print(f"| {name} | {code_display} |")
