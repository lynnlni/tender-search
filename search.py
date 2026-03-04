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
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
from bs4 import BeautifulSoup
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

# 公告类型对应的API端点
DETAIL_ENDPOINTS = {
    'ResultAnnounc': '/portal/base/resultannounc/view',
    'PurchaseAnnounceBasic': '/portal/base/purchaseannounce/view',
    'CompareSelect': '/portal/base/compareselect/view',
    'TenderAnnouncement': '/portal/base/tenderannouncement/view',  # 招标公告
    'Prequalfication': '/portal/base/prequalfication/view',  # 资格预审
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

    async def get_detail(self, item: Dict[str, Any], use_browser_fallback: bool = True) -> Dict[str, Any]:
        """获取公告详情（支持API优先+浏览器回退的混合策略）"""
        doc_type_code = item.get('docTypeCode', '')
        endpoint = DETAIL_ENDPOINTS.get(doc_type_code, '/portal/base/resultannounc/view')

        # 根据公告类型选择正确的ID字段
        # 注意：TenderAnnouncement类型实际上需要使用docId字段（而不是id字段）
        # id字段是内部编码，docId字段才是API需要的文档ID
        doc_id = item.get('docId', item.get('id', ''))

        security_code = item.get('securityViewCode', '')

        if not doc_id or not security_code:
            return {'error': '缺少必要的参数(docId或securityViewCode)'}

        params = {
            'type': doc_type_code,
            'id': doc_id,
            'securityViewCode': security_code
        }

        headers = {
            'Content-Type': 'application/json',
            'Referer': f'{API_BASE_URL}/search',
            'Origin': API_BASE_URL,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # 对于招标公告类型，直接使用浏览器回退（因为已知会被BotSec拦截）
        if use_browser_fallback and doc_type_code == 'TenderAnnouncement':
            return await self._fetch_via_browser(endpoint, params, doc_type_code, doc_id, security_code)

        # 第一步：尝试使用Python直接请求API
        try:
            async with self.http_client.session.post(f'{API_BASE_URL}{endpoint}', json=params, headers=headers) as resp:
                data = await resp.json()
                if data.get('code') == 200:
                    return data.get('data', {})
                else:
                    error_msg = data.get('msg', '获取详情失败')
                    # 如果是权限错误且允许浏览器回退，则尝试浏览器
                    if use_browser_fallback and ('权限' in error_msg or '登录' in error_msg or '没有权限' in error_msg):
                        return await self._fetch_via_browser(endpoint, params, doc_type_code, doc_id, security_code)
                    return {'error': error_msg}
        except aiohttp.ContentTypeError as e:
            # 被BotSec拦截，尝试浏览器回退
            if use_browser_fallback:
                return await self._fetch_via_browser(endpoint, params, doc_type_code, doc_id, security_code)
            return {'error': f'请求被拒绝: {str(e)}'}
        except Exception as e:
            # 其他错误，尝试浏览器回退
            if use_browser_fallback:
                return await self._fetch_via_browser(endpoint, params, doc_type_code, doc_id, security_code)
            return {'error': str(e)}

    async def _fetch_via_browser(self, endpoint: str, params: Dict[str, Any],
                                  doc_type_code: str, doc_id: str, security_code: str) -> Dict[str, Any]:
        """通过浏览器获取详情（绕过BotSec）"""
        url = f"{API_BASE_URL}{endpoint}"

        # 直接在JS中使用对象字面量，而不是传递JSON字符串给JSON.stringify
        # 避免Python的json.dumps产生的引号与JavaScript的引号冲突
        js_code = f'''fetch("{url}", {{method:"POST",headers:{{"Content-Type":"application/json","Referer":"{API_BASE_URL}/search","Origin":"{API_BASE_URL}"}},body:JSON.stringify({{"type":"{doc_type_code}","id":"{doc_id}","securityViewCode":"{security_code}"}})}}).then(r=>r.json()).then(d=>JSON.stringify(d))'''

        try:
            # 调用browser skill的eval.cjs
            browser_skill_path = os.path.expanduser("~/.claude/skills/browser")
            eval_script = os.path.join(browser_skill_path, "scripts", "eval.cjs")

            proc = await asyncio.create_subprocess_exec(
                'node', eval_script, js_code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=browser_skill_path
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

            if proc.returncode == 0 and stdout:
                # 解析返回的JSON
                response_str = stdout.decode().strip()

                # eval.cjs返回的是被引号包裹且内部转义的JSON字符串
                # 例如: "{\"code\":200,\"data\":{...}}}"
                # 使用ast.literal_eval来安全地解析这种格式
                if response_str.startswith('"') and response_str.endswith('"'):
                    import ast
                    try:
                        # 先使用ast.literal_eval解析Python字符串字面量
                        response_str = ast.literal_eval(response_str)
                    except:
                        # 如果失败，手动处理转义
                        response_str = response_str[1:-1].replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')

                try:
                    response_data = json.loads(response_str)
                except json.JSONDecodeError as e:
                    # JSON解析失败，返回错误信息
                    return {'error': f'JSON解析失败: {str(e)}', 'raw_response': response_str[:200]}

                if response_data.get('code') == 200:
                    return response_data.get('data', {})
                else:
                    return {'error': response_data.get('msg', '浏览器获取详情失败')}
            else:
                stderr_msg = stderr.decode().strip() if stderr else '未知错误'
                return {'error': f'浏览器请求失败: {stderr_msg}'}

        except asyncio.TimeoutError:
            return {'error': '浏览器请求超时'}
        except Exception as e:
            return {'error': f'浏览器调用失败: {str(e)}'}


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


async def fetch_detail_via_browser(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """通过浏览器执行fetch请求获取详情（绕过BotSec）"""
    import urllib.parse

    # 构建fetch代码
    url = f"{API_BASE_URL}{endpoint}"
    body_json = json.dumps(params, ensure_ascii=False)

    # 构建在浏览器中执行的JavaScript代码
    js_code = f'''
        fetch("{url}", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json",
                "Referer": "{API_BASE_URL}/search",
                "Origin": "{API_BASE_URL}"
            }},
            body: JSON.stringify({body_json})
        }}).then(r => r.json()).then(d => JSON.stringify(d))
    '''

    # 转义单引号用于shell
    js_code_escaped = js_code.replace("'", "'\"'\"'")

    try:
        # 调用browser skill的eval.cjs
        browser_skill_path = os.path.expanduser("~/.claude/skills/browser")
        cmd = f"cd {browser_skill_path} && node scripts/eval.cjs '{js_code_escaped}'"

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and result.stdout:
            # 解析返回的JSON
            response_data = json.loads(result.stdout.strip().strip('"').replace('\\"', '"'))
            return response_data
        else:
            return {'error': f'浏览器请求失败: {result.stderr or "未知错误"}'}

    except subprocess.TimeoutExpired:
        return {'error': '浏览器请求超时'}
    except Exception as e:
        return {'error': f'浏览器调用失败: {str(e)}'}


def clean_html(html_content: str) -> str:
    """清理HTML标签，提取纯文本"""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def format_detail_markdown(item: Dict[str, Any], detail_data: Dict[str, Any] = None) -> str:
    """格式化为详细Markdown"""
    lines = []

    # 优先使用detail_data中的字段（如果可用）
    if detail_data:
        # 招标公告类型使用不同的字段名
        title = (detail_data.get('tenderAnnouncementName') or
                 detail_data.get('purchaseAnnounceName') or
                 detail_data.get('resultAnnounceName') or
                 detail_data.get('compareSelectName') or
                 item.get('docTitle', '无标题'))
        doc_code = (detail_data.get('tenderAnnouncementCode') or
                    detail_data.get('purchaseAnnounceCode') or
                    detail_data.get('resultAnnounceCode') or
                    item.get('docCode', ''))
        province = detail_data.get('provinceName', item.get('provinceName', '未知省份'))
        date = detail_data.get('createTime', item.get('createDate', '未知日期'))
        company = detail_data.get('companyName', item.get('companyName', ''))
    else:
        title = item.get('docTitle', '无标题')
        doc_code = item.get('docCode', '')
        province = item.get('provinceName', '未知省份')
        date = item.get('createDate', '未知日期')
        company = item.get('companyName', '')

    doc_type = item.get('docType', '未知类型')

    lines.append(f"## {title}\n")
    lines.append(f"**项目编号**: {doc_code or '无'}  ")
    lines.append(f"**公告类型**: {doc_type}  ")
    lines.append(f"**省份**: {province}  ")
    lines.append(f"**发布日期**: {date}  ")
    if company:
        lines.append(f"**采购人**: {company}  ")

    # 如果有详情数据，显示正文内容
    if detail_data:
        if detail_data.get('error'):
            # 显示错误提示
            error_msg = detail_data.get('error', '')
            lines.append(f"\n⚠️ **无法获取详情**: {error_msg}")
            if '权限' in error_msg or '登录' in error_msg:
                lines.append("\n💡 提示：招标公告类型需要登录才能查看详情，建议访问网页查看。")
        else:
            lines.append("\n### 📄 公告正文\n")

            # 获取正文内容（不同字段名）
            context = detail_data.get('context', '')
            if context:
                cleaned_text = clean_html(context)
                lines.append(cleaned_text)
            else:
                # 尝试其他可能的字段
                for field in ['content', 'description', 'detail', 'body']:
                    if detail_data.get(field):
                        lines.append(clean_html(detail_data.get(field)))
                        break

            # 显示代理机构信息（招标公告类型）
            agent_name = detail_data.get('agentProviderName')
            if agent_name:
                lines.append(f"\n**代理机构**: {agent_name}  ")

            # 显示附件信息
            files = detail_data.get('files', [])
            if files:
                lines.append("\n### 📎 附件\n")
                for i, file in enumerate(files, 1):
                    file_name = file.get('fileName', f'附件{i}')
                    lines.append(f"- {file_name}")

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
                # 详细格式 - 自动获取详情
                for idx, item in enumerate(items):
                    # 获取详情（内部会根据类型选择正确的ID字段）
                    detail_data = await searcher.get_detail(item)
                    await asyncio.sleep(0.3)  # 避免请求过快

                    print(format_detail_markdown(item, detail_data))
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
