#!/usr/bin/env python3
"""
获取电信招投标公告详情

使用示例:
python detail.py --id "4793454332945260544" --type "ResultAnnounc" --security-code "973dc112651e05ab97fce08d7e4cad8b"
"""

import argparse
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

API_BASE = 'https://caigou.chinatelecom.com.cn'

# 公告类型对应的API端点
ENDPOINTS = {
    'ResultAnnounc': '/portal/base/resultannounc/view',  # 采购结果
    'PurchaseAnnounceBasic': '/portal/base/purchaseannounce/view',  # 采购公告
    'CompareSelect': '/portal/base/compareselect/view',  # 比选公告
}


def clean_html(html_content: str) -> str:
    """清理HTML标签，提取纯文本"""
    if not html_content:
        return ""

    # 使用BeautifulSoup解析
    soup = BeautifulSoup(html_content, 'html.parser')

    # 获取文本
    text = soup.get_text(separator='\n', strip=True)

    # 清理多余空行
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


async def get_announcement_detail(doc_id: str, doc_type_code: str, security_code: str):
    """通过API获取公告详情"""

    # 获取对应端点
    endpoint = ENDPOINTS.get(doc_type_code, '/portal/base/resultannounc/view')

    ssl_context = __import__('ssl').create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = __import__('ssl').CERT_NONE

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        # 先访问主页获取cookie
        try:
            await session.get(API_BASE)
        except:
            pass

        params = {
            'type': doc_type_code,
            'id': doc_id,
            'securityViewCode': security_code
        }

        headers = {
            'Content-Type': 'application/json',
            'Referer': f'{API_BASE}/search',
            'Origin': API_BASE,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        async with session.post(f'{API_BASE}{endpoint}', json=params, headers=headers) as resp:
            data = await resp.json()
            if data.get('code') == 200:
                return data.get('data', {})
            else:
                raise Exception(f"API返回错误: {data.get('msg', '未知错误')}")


def format_result(data: dict) -> str:
    """格式化输出结果"""
    result = []

    # 基本信息
    result.append("=" * 70)
    result.append("📋 公告详情")
    result.append("=" * 70)

    name = data.get('resultAnnounceName') or data.get('purchaseAnnounceName') or data.get('compareSelectName') or '未知'
    result.append(f"\n项目名称: {name}")

    if data.get('provinceName'):
        result.append(f"省份: {data.get('provinceName')}")

    if data.get('companyName'):
        result.append(f"发布单位: {data.get('companyName')}")

    if data.get('createTime'):
        result.append(f"发布时间: {data.get('createTime')}")

    if data.get('pageView'):
        result.append(f"浏览量: {data.get('pageView')}")

    # 终止状态
    is_cancel = data.get('isCancel', 0)
    result.append(f"状态: {'已终止' if is_cancel == 1 else '正常'}")

    # 正文内容
    context = data.get('context', '')
    if context:
        result.append("\n" + "-" * 70)
        result.append("📄 正文内容")
        result.append("-" * 70)
        result.append(clean_html(context))

    result.append("\n" + "=" * 70)
    return '\n'.join(result)


async def main():
    parser = argparse.ArgumentParser(description='获取电信招投标公告详情')
    parser.add_argument('--id', required=True, help='公告ID (docId)')
    parser.add_argument('--type', required=True, help='公告类型代码 (docTypeCode)')
    parser.add_argument('--security-code', required=True, help='安全验证码 (securityViewCode)')
    parser.add_argument('--raw', action='store_true', help='输出原始JSON数据')

    args = parser.parse_args()

    try:
        data = await get_announcement_detail(args.id, args.type, args.security_code)

        if args.raw:
            import json
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(format_result(data))

    except Exception as e:
        print(f"❌ 获取详情失败: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
