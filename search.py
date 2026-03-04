#!/usr/bin/env python3
"""
中国电信招投标信息查询 - Skill版本

支持场景：
1. 查看某省近x天的招投标信息
2. 查看某些省某关键字的招投标信息
3. 查看某关键字全国的招投标信息
4. 查看某个具体标的中标及公示信息
5. 查看某关键字全国的中标及公示信息
"""

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_BASE_URL = "https://caigou.chinatelecom.com.cn"
TENDER_SEARCH_ENDPOINT = "/portal/base/announcementJoin/queryListNew"

# 省份编码映射
PROVINCE_CODES = {
    "北京": "01", "天津": "21", "河北": "27", "山西": "28", "内蒙古": "31",
    "辽宁": "26", "吉林": "25", "黑龙江": "24", "上海": "03", "江苏": "04",
    "浙江": "02", "安徽": "11", "福建": "22", "江西": "23", "山东": "29",
    "河南": "30", "湖北": "06", "湖南": "05", "广东": "09", "广西": "10",
    "海南": "08", "重庆": "12", "四川": "13", "云南": "14", "贵州": "18",
    "西藏": "15", "陕西": "07", "甘肃": "16", "宁夏": "17", "青海": "19",
    "新疆": "20", "全国": ""
}

# 公告分类代码映射
CATEGORY_CODES = {
    "全部": "", "资格预审公告": "xi9s", "招标公告": "e2no", "询比公告": "e3erht",
    "谈判采购公告": "e8vif", "评价检测公告": "ds3fd2s", "政企合作招募公告": "f1f7e",
    "IPTV内容合作招募公告": "sxax8", "采购结果公示": "n0eves", "直接采购公示": "ow7t",
    "澄清公示": "th4gie", "政企合作招募结果公示": "s1x5e", "IPTV内容合作评审结果公示": "rasxq"
}


class HTTPClient:
    """HTTP客户端"""
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def __aenter__(self):
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(timeout=self.timeout, connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with self.session.get(API_BASE_URL) as response:
                pass
        except Exception:
            pass

        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": API_BASE_URL,
            "Referer": f"{API_BASE_URL}/search",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        async with self.session.post(url, json=data, headers=headers) as response:
            return await response.json()


class TenderSearcher:
    """招投标搜索器"""

    def __init__(self):
        self.http_client = None

    async def __aenter__(self):
        self.http_client = HTTPClient()
        await self.http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.__aexit__(exc_type, exc_val, exc_tb)

    async def search(self, keyword: str = "", province: str = "全国",
                     category: str = "", page_num: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """搜索招投标信息"""
        province_code = PROVINCE_CODES.get(province, "")
        category_code = CATEGORY_CODES.get(category, "")

        search_params = {
            "pageNum": page_num,
            "pageSize": page_size,
            "title": keyword,
            "provinceCode": province_code,
            "noticeSummary": "1"
        }

        if category_code:
            search_params["type"] = category_code

        response = await self.http_client.post(TENDER_SEARCH_ENDPOINT, search_params)

        if response.get('code') == 200:
            data = response.get('data', {}) or {}
            page_info = data.get('pageInfo', {}) or {}
            items = page_info.get('list', [])
            total = page_info.get('total', 0)

            return {
                "success": True,
                "total": total,
                "page_num": page_num,
                "page_size": page_size,
                "items": items
            }
        else:
            return {
                "success": False,
                "error": response.get('message', '未知错误'),
                "items": []
            }

    async def search_all(self, keyword: str = "", province: str = "全国",
                         category: str = "", max_items: int = 100) -> List[Dict[str, Any]]:
        """搜索所有结果（支持分页）"""
        all_items = []
        page_num = 1

        while len(all_items) < max_items:
            result = await self.search(keyword, province, category, page_num, 50)

            if not result["success"]:
                break

            items = result["items"]
            if not items:
                break

            all_items.extend(items)

            if len(all_items) >= result['total'] or len(items) < 50:
                break

            page_num += 1
            await asyncio.sleep(0.3)

        return all_items[:max_items]


def truncate_text(text: str, max_length: int = 40) -> str:
    """截断文本"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text


def format_markdown_table(items: List[Dict[str, Any]], show_category: bool = True) -> str:
    """格式化为Markdown表格"""
    if not items:
        return "暂无数据"

    # 表头
    headers = ["序号", "标题", "省份", "分类", "日期"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join([" --- " for _ in headers]) + "|"
    ]

    # 数据行
    for i, item in enumerate(items, 1):
        title = truncate_text(item.get('docTitle', ''), 35).replace('|', '｜')
        province = item.get('provinceName', '')
        category = item.get('docType', '')
        date = item.get('createDate', '')[:10]  # 只取日期部分

        row = f"| {i} | {title} | {province} | {category} | {date} |"
        lines.append(row)

    return "\n".join(lines)


def format_detail_markdown(item: Dict[str, Any]) -> str:
    """格式化为详细Markdown"""
    lines = []

    title = item.get('docTitle', '无标题')
    doc_type = item.get('docType', '未知类型')
    doc_code = item.get('docCode', '')
    province = item.get('provinceName', '未知省份')
    date = item.get('createDate', '未知日期')
    company = item.get('companyName', '')

    lines.append(f"## {title}\n")
    lines.append(f"**项目编号**: {doc_code or '无'}  ")
    lines.append(f"**公告类型**: {doc_type}  ")
    lines.append(f"**省份**: {province}  ")
    lines.append(f"**发布日期**: {date}  ")
    if company:
        lines.append(f"**采购人**: {company}  ")

    lines.append("\n---\n")

    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description='中国电信招投标信息查询')
    parser.add_argument('--province', '-p', type=str, default='全国', help='省份名称（如：河南、北京、全国）')
    parser.add_argument('--keyword', '-k', type=str, default='', help='搜索关键词')
    parser.add_argument('--category', '-c', type=str, default='', help='公告分类（如：招标公告、采购结果公示）')
    parser.add_argument('--days', '-d', type=int, help='近X天的数据')
    parser.add_argument('--max-items', '-m', type=int, default=20, help='最大返回条数')
    parser.add_argument('--output', '-o', type=str, help='输出JSON文件路径')
    parser.add_argument('--detail', action='store_true', help='显示详细信息格式')

    args = parser.parse_args()

    # 如果指定了days，计算日期范围（但目前API不支持日期筛选，仅作记录）
    date_filter = ""
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        date_filter = f"（近{args.days}天）"

    # 执行查询
    async with TenderSearcher() as searcher:
        items = await searcher.search_all(
            keyword=args.keyword,
            province=args.province,
            category=args.category,
            max_items=args.max_items
        )

        # 如果指定了days，手动过滤日期
        if args.days and items:
            cutoff_date = datetime.now() - timedelta(days=args.days)
            filtered_items = []
            for item in items:
                date_str = item.get('createDate', '')
                if date_str:
                    try:
                        item_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        if item_date >= cutoff_date:
                            filtered_items.append(item)
                    except:
                        filtered_items.append(item)
            items = filtered_items

        # 输出结果
        print(f"\n### 查询结果：{args.province} {args.keyword} {args.category} {date_filter}\n")
        print(f"**共找到 {len(items)} 条记录**\n")

        if items:
            if args.detail:
                # 详细格式
                for item in items:
                    print(format_detail_markdown(item))
            else:
                # 表格格式
                print(format_markdown_table(items))

        # 保存JSON
        if args.output and items:
            output_data = {
                "query": {
                    "province": args.province,
                    "keyword": args.keyword,
                    "category": args.category,
                    "days": args.days,
                    "timestamp": datetime.now().isoformat()
                },
                "total": len(items),
                "items": items
            }
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存至: {args.output}")

        # 返回适合skill解析的格式
        print(f"\n<!-- SKILL_RESULT: total={len(items)} province={args.province} keyword={args.keyword} -->")


if __name__ == "__main__":
    asyncio.run(main())
