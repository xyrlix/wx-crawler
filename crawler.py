#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章爬虫
目标：抓取指定公众号的全部文章，导出为 Markdown 文档
"""

import os
import re
import time
import json
import requests
import html2text
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from config import Config


class WxCrawler:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c11) XWEB/13655",
            "Referer": "https://mp.weixin.qq.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        # 注入 Cookie
        for k, v in cfg.cookies.items():
            self.session.cookies.set(k, v)

        self.output_dir = Path(cfg.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = cfg.ignore_images
        self.h2t.body_width = 0  # 不自动换行

    # ------------------------------------------------------------------ #
    #  获取文章列表
    # ------------------------------------------------------------------ #
    def fetch_article_list(self) -> list[dict]:
        """
        通过公众号历史消息接口分页拉取文章列表。
        接口：https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&...
        """
        articles = []
        offset = 0
        page = 1

        print(f"\n🔍 开始拉取「{self.cfg.account_name}」文章列表...")

        while True:
            params = {
                "action": "getmsg",
                "__biz": self.cfg.biz,
                "f": "json",
                "offset": offset,
                "count": 10,
                "is_ok": 1,
                "scene": 124,
                "uin": self.cfg.uin,
                "key": self.cfg.key,
                "pass_ticket": self.cfg.pass_ticket,
                "wxtoken": "",
                "appmsg_token": self.cfg.appmsg_token,
                "x5": 0,
            }

            try:
                resp = self.session.get(
                    "https://mp.weixin.qq.com/mp/profile_ext",
                    params=params,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"  ❌ 第{page}页请求失败: {e}")
                break

            # 解析返回数据
            ret = data.get("ret", -1)
            if ret != 0:
                errmsg = data.get("errmsg", "未知错误")
                print(f"  ❌ 接口返回错误 ret={ret}: {errmsg}")
                print("  💡 可能是 Cookie 已过期，请重新抓包获取")
                break

            msg_list_str = data.get("general_msg_list", "{}")
            try:
                msg_list = json.loads(msg_list_str)
            except json.JSONDecodeError:
                print("  ❌ 解析文章列表 JSON 失败")
                break

            items = msg_list.get("list", [])
            if not items:
                print(f"  ✅ 已到达最后一页（共获取 {len(articles)} 篇）")
                break

            for item in items:
                comm_msg_info = item.get("comm_msg_info", {})
                app_msg_ext_info = item.get("app_msg_ext_info", {})

                # 提取主文章
                article = self._parse_article_item(comm_msg_info, app_msg_ext_info)
                if article:
                    articles.append(article)

                # 多图文的子文章
                multi_items = app_msg_ext_info.get("multi_app_msg_item_list", [])
                for sub in multi_items:
                    sub_article = self._parse_sub_article(comm_msg_info, sub)
                    if sub_article:
                        articles.append(sub_article)

            print(f"  📄 第{page}页：获取 {len(items)} 条，累计 {len(articles)} 篇")

            # 是否还有更多
            can_msg_continue = data.get("can_msg_continue", 0)
            if not can_msg_continue:
                print(f"  ✅ 已获取全部文章（共 {len(articles)} 篇）")
                break

            offset += 10
            page += 1
            time.sleep(self.cfg.request_delay)

        return articles

    def _parse_article_item(self, comm_info: dict, ext_info: dict) -> dict | None:
        title = ext_info.get("title", "").strip()
        url = ext_info.get("content_url", "").strip()
        if not title or not url:
            return None

        timestamp = comm_info.get("datetime", 0)
        date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d") if timestamp else "unknown"

        return {
            "title": title,
            "url": url,
            "date": date_str,
            "digest": ext_info.get("digest", "").strip(),
            "cover": ext_info.get("cover", "").strip(),
        }

    def _parse_sub_article(self, comm_info: dict, sub: dict) -> dict | None:
        title = sub.get("title", "").strip()
        url = sub.get("content_url", "").strip()
        if not title or not url:
            return None

        timestamp = comm_info.get("datetime", 0)
        date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d") if timestamp else "unknown"

        return {
            "title": title,
            "url": url,
            "date": date_str,
            "digest": sub.get("digest", "").strip(),
            "cover": sub.get("cover", "").strip(),
        }

    # ------------------------------------------------------------------ #
    #  抓取文章正文
    # ------------------------------------------------------------------ #
    def fetch_article_content(self, url: str) -> str:
        """抓取单篇文章正文，返回 Markdown 字符串"""
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            html = resp.text
        except Exception as e:
            return f"> ⚠️ 文章内容抓取失败: {e}\n"

        soup = BeautifulSoup(html, "lxml")

        # 微信文章正文容器
        content_div = (
            soup.find("div", id="js_content")
            or soup.find("div", class_="rich_media_content")
        )

        if not content_div:
            return "> ⚠️ 未找到文章正文，可能需要登录或文章已删除\n"

        # 清理多余元素
        for tag in content_div.find_all(["script", "style", "iframe"]):
            tag.decompose()

        # 转换为 Markdown
        content_html = str(content_div)
        md = self.h2t.handle(content_html)

        # 清理多余空行
        md = re.sub(r'\n{3,}', '\n\n', md).strip()
        return md

    # ------------------------------------------------------------------ #
    #  导出 Markdown
    # ------------------------------------------------------------------ #
    def export_article(self, article: dict, content: str):
        """将单篇文章保存为 Markdown 文件"""
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', article["title"])
        safe_title = safe_title[:80]  # 文件名长度限制
        filename = f"{article['date']}-{safe_title}.md"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {article['title']}\n\n")
            f.write(f"> **发布时间**：{article['date']}  \n")
            f.write(f"> **原文链接**：[点击查看]({article['url']})  \n")
            if article.get("digest"):
                f.write(f"> **摘要**：{article['digest']}  \n")
            f.write("\n---\n\n")
            f.write(content)
            f.write("\n")

        return filepath

    def export_index(self, articles: list[dict]):
        """生成文章索引文件"""
        index_path = self.output_dir / "README.md"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(f"# {self.cfg.account_name} 文章归档\n\n")
            f.write(f"> 共 {len(articles)} 篇文章，抓取时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("## 文章列表\n\n")
            f.write("| 日期 | 标题 | 摘要 |\n")
            f.write("|------|------|------|\n")
            for a in sorted(articles, key=lambda x: x["date"], reverse=True):
                safe_title = re.sub(r'[\\/:*?"<>|]', '_', a["title"])[:80]
                fname = f"{a['date']}-{safe_title}.md"
                digest = a.get("digest", "")[:50].replace("|", "｜")
                f.write(f"| {a['date']} | [{a['title']}]({fname}) | {digest} |\n")
        return index_path

    # ------------------------------------------------------------------ #
    #  主流程
    # ------------------------------------------------------------------ #
    def run(self):
        # 1. 获取文章列表
        articles = self.fetch_article_list()
        if not articles:
            print("\n❌ 未获取到任何文章，请检查配置")
            return

        # 保存文章列表 JSON（方便断点续爬）
        list_cache = self.output_dir / "_article_list.json"
        with open(list_cache, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"\n💾 文章列表已缓存到: {list_cache}")

        # 2. 逐篇抓取正文
        print(f"\n📥 开始抓取文章正文（共 {len(articles)} 篇）...")
        success, failed = 0, 0

        for i, article in enumerate(articles, 1):
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', article["title"])[:40]
            print(f"  [{i:03d}/{len(articles)}] {article['date']} {safe_title}...", end="", flush=True)

            # 已抓取则跳过（断点续爬）
            filename = f"{article['date']}-{re.sub(r'[\\/:*?\"<>|]', '_', article['title'])[:80]}.md"
            filepath = self.output_dir / filename
            if filepath.exists():
                print(" ⏭ 已存在，跳过")
                success += 1
                continue

            content = self.fetch_article_content(article["url"])
            self.export_article(article, content)
            success += 1
            print(" ✅")

            time.sleep(self.cfg.request_delay)

        # 3. 生成索引
        index_path = self.export_index(articles)
        print(f"\n📋 索引文件: {index_path}")
        print(f"\n🎉 完成！成功 {success} 篇，失败 {failed} 篇")
        print(f"📁 输出目录: {self.output_dir.resolve()}")
