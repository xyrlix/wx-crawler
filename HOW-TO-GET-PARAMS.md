# 如何获取微信公众号抓包参数

这是整个爬虫能否运行的关键步骤，请仔细操作。

---

## 你需要用到的工具

- **微信PC版**（已安装）
- **Fiddler Classic**（免费抓包工具）

### 下载 Fiddler Classic
> https://www.telerik.com/fiddler/fiddler-classic  
> 点击 "Download for free" → 填邮箱 → 下载安装

---

## 第一步：配置 Fiddler 解密 HTTPS

1. 打开 Fiddler → 菜单栏 **Tools → Options**
2. 点击 **HTTPS** 标签页
3. 勾选 **Decrypt HTTPS traffic**
4. 弹出提示框点 **Yes**（安装根证书）
5. 点击 **OK** 保存

---

## 第二步：开始抓包

1. 确保 Fiddler 在运行（左下角显示 `Capturing`）
2. 打开**微信PC版**
3. 进入「依尘骇客」公众号主页
4. 点击**查看历史消息**（右上角 `...` → 查看历史消息）
5. 页面加载后，**在 Fiddler 中搜索** `profile_ext`

---

## 第三步：找到目标请求

在 Fiddler 左侧请求列表中，找到包含以下特征的请求：

```
https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz=...
```

**点击这条请求**，在右侧面板查看：

### 从 URL 中提取参数

点击右侧 **Inspectors → Headers**，URL 中包含：

```
?action=getmsg
&__biz=MzA4ODQ1NTUxMQ==   ← 这是 biz（示例）
&f=json
&offset=0
&count=10
&uin=xxx                    ← 这是 uin
&key=xxx                    ← 这是 key
&pass_ticket=xxx            ← 这是 pass_ticket
&appmsg_token=xxx           ← 这是 appmsg_token
```

**把这几个值记录下来。**

### 从 Cookie 中提取

在右侧 **Headers** 中找到 `Cookie:` 那一行，复制整个 Cookie 字符串。

---

## 第四步：填写 config.py

打开 `config.py`，按下面格式填写：

```python
biz: str = "MzA4ODQ1NTUxMQ=="   # 你抓包到的 __biz 值

uin: str = "xxx"                 # URL 中的 uin
key: str = "xxx"                 # URL 中的 key
pass_ticket: str = "xxx"         # URL 中的 pass_ticket
appmsg_token: str = "xxx"        # URL 中的 appmsg_token

cookies: dict = {
    "uin": "xxx",
    "skey": "@xxx",
    "sid": "xxx",
    "ologin": "xxx",
    # ... 把所有 Cookie 字段都加进来
}
```

### Cookie 转换小技巧

Fiddler 里 Cookie 是一行字符串，格式是：
```
uin=xxx; skey=@xxx; pgv_pvid=xxx; ...
```

可以用下面这段 Python 快速转换：

```python
raw = "uin=xxx; skey=@xxx; pgv_pvid=xxx"  # 粘贴你的完整 Cookie
cookies = dict(item.split("=", 1) for item in raw.split("; "))
print(cookies)
```

---

## 第五步：运行爬虫

```powershell
cd F:\claw\wx-crawler

# 安装依赖（只需一次）
pip install -r requirements.txt

# 运行
python main.py
```

---

## 常见问题

**Q: 微信PC版抓不到包？**  
A: 微信PC版默认使用系统代理，Fiddler 会自动捕获。如果没有，尝试：
- 关闭微信，打开 Fiddler 后再重新打开微信
- 检查 Fiddler 的 `WinConfig` 是否已配置系统代理

**Q: 找不到 `profile_ext` 请求？**  
A: 需要在微信PC里点击「查看历史消息」后，滚动加载更多才会触发这个接口。首次进入可能走缓存。

**Q: 运行后报 `ret=-3`？**  
A: Cookie 已过期，需要重新抓包。Cookie 有效期通常是 1 天左右。

**Q: 文章抓取成功但内容是空的？**  
A: 部分文章需要公众号关注者登录才能查看，Cookie 里要有关注该号的账号信息。

---

## Cookie 有效期说明

微信PC端的 Cookie 通常有效期约为 **1 天**。

如果你有几十篇文章，一次运行即可完成。爬虫支持**断点续爬**：
- 已经下载的文章会自动跳过
- 如果 Cookie 过期了中途中断，重新抓包更新 config.py 再运行即可继续
