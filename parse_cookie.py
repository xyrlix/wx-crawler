#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 解析小工具
把 Fiddler 抓到的 Cookie 字符串转换为 Python 字典格式
"""

def parse_cookie(raw_cookie: str) -> dict:
    """解析 Cookie 字符串"""
    cookies = {}
    for item in raw_cookie.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def main():
    print("=" * 60)
    print("  微信 Cookie 解析工具")
    print("=" * 60)
    print("\n请把 Fiddler 抓到的完整 Cookie 字符串粘贴到下面：")
    print("（一行，格式类似：uin=xxx; skey=@xxx; ...）")
    print()

    raw = input("Cookie: ").strip()
    if not raw:
        print("❌ 输入为空")
        return

    cookies = parse_cookie(raw)
    print("\n✅ 解析结果，复制到 config.py 的 cookies 字段中：\n")
    print("cookies: dict = field(default_factory=lambda: {")
    for k, v in cookies.items():
        print(f'    "{k}": "{v}",')
    print("})")

    print("\n" + "=" * 60)
    print("同时请从 Fiddler 的请求 URL 中找到以下参数：")
    print("  __biz=xxx  →  biz")
    print("  uin=xxx    →  uin")
    print("  key=xxx    →  key")
    print("  pass_ticket=xxx  →  pass_ticket")
    print("  appmsg_token=xxx →  appmsg_token")
    print("=" * 60)


if __name__ == "__main__":
    main()
