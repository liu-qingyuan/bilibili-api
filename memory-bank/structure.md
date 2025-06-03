# Bilibili-API 项目结构

## 项目整体结构

```
bilibili-api/
├── bilibili_api/            # 主模块目录
│   ├── __init__.py          # 模块初始化及公共导出
│   ├── _pyinstaller/        # PyInstaller支持
│   ├── clients/             # 客户端实现
│   ├── data/                # API数据及静态资源
│   ├── exceptions/          # 异常类定义
│   ├── tools/               # 工具集
│   ├── utils/               # 工具函数
│   ├── activity.py          # 活动相关API
│   ├── app.py               # 移动端应用相关API
│   ├── article.py           # 专栏文章相关API
│   ├── article_category.py  # 专栏分类相关API
│   ├── ass.py               # ASS字幕处理
│   ├── audio.py             # 音频相关API
│   ├── audio_uploader.py    # 音频上传功能
│   ├── bangumi.py           # 番剧相关API
│   ├── black_room.py        # 小黑屋相关API
│   ├── channel_series.py    # 频道相关API
│   ├── cheese.py            # 课程相关API
│   ├── client.py            # 客户端相关
│   ├── comment.py           # 评论相关API
│   ├── creative.py          # 创作中心相关API
│   ├── creative_center.py   # 创作中心相关API
│   ├── customer_service.py  # 客服相关API
│   ├── danmaku.py           # 弹幕相关API
│   ├── dynamic.py           # 动态相关API
│   ├── favorite_list.py     # 收藏夹相关API
│   ├── game.py              # 游戏相关API
│   ├── gaoqing.py           # 高清资源相关API
│   ├── guard.py             # 舰长相关API
│   ├── history.py           # 历史记录相关API
│   ├── homepage.py          # 主页相关API
│   ├── hot.py               # 热门相关API
│   ├── live.py              # 直播相关API
│   ├── login.py             # 登录相关功能
│   ├── manga.py             # 漫画相关API
│   ├── member.py            # 会员相关API
│   ├── message.py           # 消息相关API
│   ├── note.py              # 笔记相关API
│   ├── opus.py              # 文集相关API
│   ├── pay.py               # 支付相关API
│   ├── rank.py              # 排行榜相关API
│   ├── read.py              # 阅读相关API
│   ├── search.py            # 搜索相关API
│   ├── session.py           # 会话相关API
│   ├── settings.py          # 设置相关API
│   ├── show.py              # 展示相关API
│   ├── space.py             # 用户空间相关API
│   ├── user.py              # 用户相关API
│   ├── v_resource.py        # V资源相关API
│   ├── video.py             # 视频相关API
│   ├── video_uploader.py    # 视频上传功能
├── bilibili_sensitive_crawler/  # 敏感视频爬虫项目
│   ├── config/                  # 配置文件目录
│   │   ├── config.yaml          # 主配置文件
│   ├── data/                    # 数据存储目录
│   │   ├── json/                # JSON数据存储目录
│   │   ├── videos/              # 视频文件存储目录
│   ├── logs/                    # 日志文件目录
│   ├── scripts/                 # 脚本文件目录
│   ├── utils/                   # 工具模块目录
│   │   ├── __init__.py          # 工具包初始化文件
│   │   ├── crawler.py           # 视频信息采集模块
│   │   ├── dataset.py           # 数据集管理模块
│   │   ├── downloader.py        # 视频下载模块
│   │   ├── login.py             # 登录模块
│   │   ├── search.py            # 搜索模块
│   ├── main.py                  # 主入口文件
│   ├── README.md                # 项目说明文档
│   ├── requirements.txt         # 依赖配置文件
├── CHANGELOGS/           # 更新日志目录
├── design/               # 设计相关文档
├── docs/                 # 文档目录
├── memory-bank/          # 项目记忆库
├── scripts/              # 脚本目录
├── tests/                # 测试目录
├── .editorconfig         # 编辑器配置
├── .gitattributes        # Git属性配置
├── .gitignore            # Git忽略配置
├── install.py            # 安装脚本
├── LICENSE               # 许可证
├── pyproject.toml        # 项目配置
├── README.md             # 项目说明
├── requirements.txt      # 依赖列表
└── SECURITY.md           # 安全策略
```

## 主要模块说明

### 核心模块 (bilibili_api)

* **__init__.py**: 包初始化文件，定义公共变量和导出接口
* **clients/**: 多种HTTP客户端实现，支持不同的请求方式
* **data/**: 存放各种静态数据，如API URL、常量等
* **exceptions/**: 自定义异常类，用于异常处理
* **utils/**: 通用工具函数，如网络请求、参数签名等
* **tools/**: 实用工具集，提供额外功能

### 功能模块 (bilibili_api/*.py)

* **video.py**: 提供视频相关API，如获取视频信息、点赞、投币等
* **user.py**: 提供用户相关API，如获取用户信息、关注等
* **live.py**: 提供直播相关API，如获取直播信息、发送弹幕等
* **dynamic.py**: 提供动态相关API，如获取动态列表、发表动态等
* **login.py**: 提供登录相关功能，如扫码登录、密码登录等
* 其他功能模块: 专栏、评论、消息、收藏夹等

### 敏感视频爬虫项目 (bilibili_sensitive_crawler)

* **main.py**: 爬虫主入口文件，处理命令行参数和程序流程
* **config/**: 配置文件目录，存放项目配置
  * **config.yaml**: 主配置文件，定义爬虫各项参数
* **utils/**: 工具模块目录，包含各功能模块
  * **login.py**: 登录模块，实现B站账号登录功能
  * **search.py**: 搜索模块，实现关键词搜索功能
  * **crawler.py**: 视频信息采集模块，获取视频详情
  * **downloader.py**: 视频下载模块，下载720p视频
  * **dataset.py**: 数据集管理模块，管理视频数据和元数据
* **data/**: 数据存储目录
  * **json/**: 存储视频信息的JSON文件
  * **videos/**: 存储下载的视频文件
* **logs/**: 日志文件目录，存放运行日志

## 文件说明

### Bilibili-API 主要文件

* **pyproject.toml**: Python项目配置文件，定义项目元数据和构建系统
* **requirements.txt**: 项目依赖列表，指定依赖的外部库
* **install.py**: 安装脚本，用于安装和配置项目
* **README.md**: 项目说明文件，提供项目概述和使用方法
* **LICENSE**: 项目许可证，定义使用和分发条款

### 敏感视频爬虫项目文件

* **main.py**: 爬虫入口文件，包含主要执行逻辑
* **requirements.txt**: 爬虫项目依赖列表
* **README.md**: 爬虫项目说明和使用方法 