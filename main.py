#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主入口：运行爬虫
"""

from config import Config
from crawler import WxCrawler


def main():
    cfg = Config()

    # 检查必填项
    if cfg.biz == "YOUR_BIZ_HERE":
        print("❌ 请先在 config.py 中填写 biz 参数！")
        print("   参考 HOW-TO-GET-PARAMS.md 获取抓包步骤")
        return

    if not cfg.cookies:
        print("❌ 请先在 config.py 中填写 cookies！")
        return

    crawler = WxCrawler(cfg)
    crawler.run()


if __name__ == "__main__":
    main()
