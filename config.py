#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
所有参数都从这里填写
"""

from dataclasses import dataclass, field


@dataclass
class Config:
    # ================================================================
    # 【必填】公众号信息
    # ================================================================

    # 公众号名称（用于输出目录和索引标题）
    account_name: str = "依尘骇客"

    # __biz：公众号唯一标识，从抓包请求 URL 中获取
    # 示例：MzA4ODQ1NTUxMQ==
    biz: str = "YOUR_BIZ_HERE"

    # ================================================================
    # 【必填】从微信PC端抓包获取的参数（有效期约1天）
    # ================================================================

    # 从 Cookie 中提取
    uin: str = ""           # Cookie 中的 uin 字段
    key: str = ""           # URL 参数 key
    pass_ticket: str = ""   # URL 参数 pass_ticket
    appmsg_token: str = ""  # URL 参数 appmsg_token

    # ================================================================
    # 【必填】完整 Cookie 字典（从抓包中复制）
    # ================================================================
    cookies: dict = field(default_factory=lambda: {
        # 把抓包拿到的 Cookie 粘贴到这里，格式如下：
        # "uin": "xxx",
        # "skey": "@xxx",
        # "pgv_pvid": "xxx",
        # "appmsglist_action_3": "card",
        # ... 其他字段
    })

    # ================================================================
    # 输出配置
    # ================================================================

    # 文章输出目录
    output_dir: str = r"F:\claw\wx-crawler\output\依尘骇客"

    # 是否忽略图片（True=不下载图片，只保留文字；False=保留图片链接）
    ignore_images: bool = False

    # 每次请求之间的延迟（秒），避免被封
    request_delay: float = 2.0
