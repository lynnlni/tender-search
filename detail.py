#!/usr/bin/env python3
"""
获取电信招投标公告详情

使用示例:
python detail.py --id "168755009506461" --type "PurchaseAnnounceBasic" --security-code "4c0e7f52a2a74b163e23ba07b672ac12"
"""

import argparse
import subprocess
import json
import sys

BROWSER_SCRIPT_PATH = "~/.claude/skills/browser/scripts"

def run_browser_command(script, *args):
    """运行浏览器脚本"""
    cmd = ["node", f"{BROWSER_SCRIPT_PATH}/{script}"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr


def get_announcement_detail(doc_id: str, doc_type_code: str, security_code: str):
    """获取公告详情"""

    # 构建URL
    url = f"https://caigou.chinatelecom.com.cn/DeclareDetails?id={doc_id}&type=2&docTypeCode={doc_type_code}&securityViewCode={security_code}"

    print(f"正在获取公告详情...")
    print(f"URL: {url}")
    print("-" * 80)

    # 启动Chrome
    subprocess.run(["node", f"{BROWSER_SCRIPT_PATH}/start.cjs", "--profile"],
                   capture_output=True, timeout=10)

    try:
        # 导航到页面
        subprocess.run(["node", f"{BROWSER_SCRIPT_PATH}/nav.cjs", url],
                       capture_output=True, timeout=30)

        # 等待加载
        import time
        time.sleep(2)

        # 获取页面内容
        result = subprocess.run(
            ["node", f"{BROWSER_SCRIPT_PATH}/eval.cjs",
             'document.querySelector("body").innerText'],
            capture_output=True, text=True, timeout=30
        )

        content = result.stdout.strip()

        # 关闭Chrome
        subprocess.run(["pkill", "-f", "remote-debugging-port=9222"],
                       capture_output=True)

        return content

    except Exception as e:
        # 确保关闭Chrome
        subprocess.run(["pkill", "-f", "remote-debugging-port=9222"],
                       capture_output=True)
        raise e


def main():
    parser = argparse.ArgumentParser(description='获取电信招投标公告详情')
    parser.add_argument('--id', required=True, help='公告ID (docId)')
    parser.add_argument('--type', required=True, help='公告类型代码 (docTypeCode)')
    parser.add_argument('--security-code', required=True, help='安全验证码 (securityViewCode)')

    args = parser.parse_args()

    try:
        content = get_announcement_detail(args.id, args.type, args.security_code)
        print(content)
    except Exception as e:
        print(f"获取详情失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
