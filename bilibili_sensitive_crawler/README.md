# 哔哩哔哩敏感视频爬虫

一个专门用于构建视觉大语言模型评测数据集的 B 站视频爬虫工具，支持敏感内容检测和自动化数据采集。

## 📋 项目概述

本项目是 `bilibili-api` 项目的子模块，专门针对特定关键词（如敏感内容相关词汇）进行视频搜索、信息爬取和视频下载，用于构建视觉大语言模型（VLM）的评测数据集。

### 🎯 核心功能

- **智能登录系统**：支持扫码登录和 Cookie 登录，自动处理认证流程
- **关键词搜索**：基于特定关键词搜索相关视频内容
- **信息爬取**：批量获取视频详细信息和元数据
- **视频下载**：支持多种清晰度的视频下载（360P-1080P）
- **数据集管理**：完整的数据集构建、管理和统计功能
- **视频过滤**：基于时长等条件的智能视频过滤和清理 ⭐ **新功能**
- **文件分析**：视频文件与元数据的匹配分析和孤立文件检测 ⭐ **新功能**
- **索引管理**：自动维护和同步 index.json 索引文件 ⭐ **新功能**
- **异常处理**：完善的错误处理和重试机制
- **并发控制**：支持并发下载，提高采集效率

### 🏗️ 项目架构

```
bilibili_sensitive_crawler/
├── main.py                  # 主入口文件，提供命令行界面
├── config/                  # 配置管理模块
│   ├── config.json         # 主配置文件（JSON格式）
│   ├── config.yaml         # 备用配置文件（YAML格式）
│   └── settings.py         # 配置加载和管理逻辑
├── utils/                   # 核心功能模块
│   ├── __init__.py         # 模块初始化文件
│   ├── login.py            # B站登录模块（扫码/Cookie登录）
│   ├── search.py           # 视频搜索模块
│   ├── crawler.py          # 视频信息爬取模块
│   ├── downloader.py       # 视频下载模块
│   ├── dataset.py          # 数据集管理模块
│   ├── video_filter.py     # 视频过滤模块 ⭐ **新模块**
│   └── file_analyzer.py    # 文件分析模块 ⭐ **新模块**
├── data/                    # 数据存储目录
│   ├── json/               # 视频元数据存储（JSON格式）
│   │   └── index.json      # 索引文件 ⭐ **重要文件**
│   └── videos/             # 下载的视频文件存储
├── logs/                    # 日志文件存储
├── tests/                   # 测试代码
│   ├── test_data/          # 测试数据
│   └── run_tests.py        # 测试运行脚本
├── examples/                # 使用示例
│   └── basic_usage.py      # 基本使用示例
├── scripts/                 # 辅助脚本
├── docs/                    # 详细文档 ⭐ **新增**
│   ├── video_filter.md     # 视频过滤模块文档
│   ├── file_analyzer.md    # 文件分析模块文档
│   └── ...                 # 其他模块文档
├── requirements.txt         # 项目依赖列表
└── README.md               # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 稳定的网络连接
- 足够的存储空间（建议至少 10GB）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/bilibili-api.git
cd bilibili-api/bilibili_sensitive_crawler
```

2. **创建虚拟环境**（推荐）
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **生成配置文件**
```bash
python main.py --generate-config
```

### 基本使用

#### 1. 默认配置运行
```bash
python main.py
```

#### 2. 自定义关键词搜索
```bash
python main.py --keywords "关键词1" "关键词2" --limit 50
```

#### 3. 仅爬取信息，不下载视频
```bash
python main.py --info-only --keywords "测试关键词"
```

#### 4. 指定视频质量和并发数
```bash
python main.py --quality 64 --concurrent 5 --max-videos 200
```

## 🔧 数据集管理功能 ⭐ **新功能**

### 视频过滤功能

#### 1. 下载时时长过滤 ⭐ **新功能**
```bash
# 启用下载时时长过滤，限制30秒
python main.py --keywords "测试关键词" --download --max-duration 30

# 自定义时长限制为60秒
python main.py --keywords "测试关键词" --download --max-duration 60

# 设置其他时长限制，比如120秒
python main.py --keywords "测试关键词" --download --max-duration 120

# 结合其他参数使用
python main.py --keywords "关键词1" "关键词2" --download --max-duration 45 --quality 64 --limit 100

# 仅爬取信息，不下载，但仍然过滤（保存元数据时会记录是否超时长）
python main.py --keywords "测试" --info-only --max-duration 30
```

**功能说明：**
- 只要指定了 `--max-duration` 参数，就会自动在下载前检查视频时长
- 超过时长限制的视频会跳过下载，但仍保存元数据文件
- 如果不指定 `--max-duration`，则不进行时长过滤，下载所有视频

#### 2. 删除超长视频
```bash
# 删除超过30秒的视频（试运行）
python main.py --delete-long-videos --max-duration 30 --dry-run

# 实际删除超过30秒的视频
python main.py --delete-long-videos --max-duration 30 --generate-report

# 仅列出超长视频，不删除
python main.py --list-long-videos --max-duration 30
```

#### 3. 生成删除报告
```bash
# 删除超长视频并生成详细报告
python main.py --delete-long-videos --max-duration 60 --generate-report
```

### 文件分析功能

#### 1. 检查索引完整性
```bash
# 检查索引文件的完整性和匹配情况
python main.py --check-index
```

#### 2. 同步索引文件
```bash
# 试运行索引同步
python main.py --sync-index --dry-run

# 实际执行索引同步
python main.py --sync-index
```

#### 3. 分析文件匹配情况
```bash
# 分析文件匹配情况（包含索引检查）
python main.py --analyze-files

# 清理孤立文件并同步索引
python main.py --clean-orphan-videos --clean-orphan-jsons --update-index

# 试运行清理操作
python main.py --clean-orphan-videos --clean-orphan-jsons --update-index --dry-run
```

#### 4. 生成分析报告
```bash
# 生成详细的文件分析报告
python main.py --save-analysis-report
```

## 📖 详细使用说明

### 命令行参数

#### 基本参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--config` | str | `config/config.json` | 配置文件路径 |
| `--generate-config` | flag | - | 生成默认配置文件并退出 |
| `--debug` | flag | - | 启用调试模式，显示详细日志 |
| `--log-file` | str | `logs/bili_crawler.log` | 日志文件路径 |
| `--force-login` | flag | - | 强制重新登录 |
| `--use-cookie` | flag | - | 使用 Cookie 登录 |

#### 搜索和下载参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--keywords` | list | - | 搜索关键词列表 |
| `--limit` | int | 100 | 每个关键词的视频数量限制 |
| `--download` | flag | - | 下载视频文件 |
| `--info-only` | flag | - | 仅爬取视频信息，不下载 |
| `--quality` | int | 32 | 视频质量（16=360P, 32=480P, 64=720P, 80=1080P） |
| `--metadata-dir` | str | - | 元数据保存目录 |
| `--video-dir` | str | - | 视频保存目录 |
| `--max-videos` | int | 1000 | 最大视频数量 |
| `--resume` | flag | - | 恢复上次爬取 |
| `--max-retries` | int | 3 | 最大重试次数 |
| `--interval` | float | 1.0 | 请求间隔时间（秒） |

#### 视频过滤参数 ⭐ **新参数**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--delete-long-videos` | flag | - | 删除超出指定时长的视频及其元数据文件 |
| `--list-long-videos` | flag | - | 列出超出指定时长的视频（不删除） |
| `--max-duration` | int | 30 | 最大允许视频时长（秒），指定后自动启用下载时过滤 |
| `--dry-run` | flag | - | 试运行模式，不实际删除文件 |
| `--generate-report` | flag | - | 生成删除操作报告 |

#### 文件分析参数 ⭐ **新参数**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--analyze-files` | flag | - | 分析视频文件和JSON文件的匹配情况 |
| `--clean-orphan-videos` | flag | - | 清理孤立的视频文件（有视频无JSON） |
| `--clean-orphan-jsons` | flag | - | 清理孤立的JSON文件（有JSON无视频） |
| `--save-analysis-report` | flag | - | 保存文件分析报告到文件 |
| `--sync-index` | flag | - | 同步index.json索引文件与实际文件 |
| `--update-index` | flag | - | 在清理文件时同时更新索引文件 |
| `--check-index` | flag | - | 检查索引文件的完整性和匹配情况 |

### 配置文件说明

项目支持 JSON 和 YAML 两种配置格式，主要配置项包括：

#### 路径配置
```json
{
    "paths": {
        "data_dir": "data",
        "logs_dir": "logs", 
        "metadata_dir": "data/json",
        "videos_dir": "data/videos"
    }
}
```

#### 登录配置
```json
{
    "login": {
        "use_cookie": false,
        "qrcode_in_terminal": true,
        "verify_timeout": 60,
        "max_retries": 3
    }
}
```

#### 搜索配置
```json
{
    "search": {
        "keywords": ["测试"],
        "limit_per_keyword": 100,
        "order_type": "pubdate",
        "min_duration": 30,
        "max_duration": 600
    }
}
```

#### 下载配置
```json
{
    "downloader": {
        "default_quality": 32,
        "concurrent_limit": 3,
        "retry_times": 3,
        "max_size_gb": 800
    }
}
```

#### 视频过滤配置 ⭐ **新配置**
```json
{
    "video_filter": {
        "max_duration": 30,
        "filter_on_download": true,
        "backup_before_delete": true,
        "generate_reports": true,
        "update_index": true
    }
}
```

#### 索引配置 ⭐ **新配置**
```json
{
    "index": {
        "auto_update": true,
        "backup_before_update": true,
        "validate_on_load": true,
        "compress_on_save": false
    }
}
```

## 🔧 核心模块详解

### 1. 登录模块 (`utils/login.py`)

**功能特点：**
- 支持二维码扫码登录
- 支持 Cookie 文件登录
- 自动凭证管理和刷新
- 网络连接检测
- 登录状态验证

**使用示例：**
```python
from utils.login import BiliLogin

login = BiliLogin()
```

### 2. 搜索模块 (`utils/search.py`)

**功能特点：**
- 关键词搜索
- 多种排序方式（发布时间、播放量、弹幕数等）
- 时长筛选
- 分区筛选
- 分页获取

**搜索参数：**
- `order_type`: 排序方式（`pubdate`/`totalrank`/`click`/`dm`）
- `duration_type`: 时长筛选（0=全部, 1=0-10分钟, 2=10-30分钟等）
- `tids`: 分区ID筛选

### 3. 爬取模块 (`utils/crawler.py`)

**功能特点：**
- 批量视频信息获取
- 异步并发处理
- 智能重试机制
- 详细错误记录

**获取信息包括：**
- 视频基本信息（标题、描述、时长等）
- 统计数据（播放量、点赞数、评论数等）
- UP主信息
- 视频标签和分区信息

### 4. 下载模块 (`utils/downloader.py`)

**功能特点：**
- 多清晰度支持（360P-1080P）
- 音视频分离下载和合并
- 并发下载控制
- 断点续传
- 存储空间管理
- 文件完整性验证

**支持的视频质量：**
- 16: 360P
- 32: 480P（默认）
- 64: 720P
- 80: 1080P

### 5. 数据集管理 (`utils/dataset.py`)

**功能特点：**
- 数据集索引管理
- 完整性检查
- 统计报告生成
- 增量更新
- 数据去重

**管理功能：**
```bash
# 检查数据集完整性
python main.py --check-integrity

# 生成统计报告
python main.py --generate-report

# 增量更新数据集
python main.py --increment /path/to/other/dataset
```

## 🛡️ 异常处理系统

项目实现了完善的异常处理机制，能够精确定位和报告各种错误：

### 错误类型
- **网络连接错误**：提供服务器信息和失败原因
- **视频流错误**：包含清晰度和格式详情
- **音频流错误**：标识音频段获取问题
- **合并错误**：包含 FFmpeg 错误代码和信息
- **重试超限错误**：记录尝试次数和最后错误
- **信息获取错误**：视频元数据获取问题
- **磁盘空间错误**：提供所需空间和可用空间信息
- **外部工具错误**：包含工具名称和命令行详情

### 日志记录
所有异常都会记录在日志文件中，包含：
- 时间戳
- 错误类型
- 视频 BV 号
- 详细错误信息
- 堆栈跟踪

## 🧪 测试和开发

### 运行测试
```bash
# 运行所有测试
cd tests
python run_tests.py

# 运行特定模块测试
python run_tests.py downloader dataset

# 性能测试
python test_performance.py --all
```

### 开发环境设置
```bash
# 安装开发依赖
pip install pytest pytest-asyncio black mypy flake8

# 代码格式化
black .

# 类型检查
mypy utils/

# 代码风格检查
flake8 utils/
```

## 📊 使用示例

### 基本爬取示例
```python
import asyncio
from utils.login import BiliLogin
from utils.search import BiliSearch
from utils.crawler import BiliCrawler

async def basic_crawl():
    # 登录
    login = BiliLogin()
    credential = await login.login()
    
    # 搜索
    search = BiliSearch(credential)
    videos = await search.search_videos(["测试关键词"], limit=10)
    
    # 爬取信息
    crawler = BiliCrawler(credential)
    for video in videos:
        info = await crawler.get_video_info(video['bvid'])
        print(f"视频: {info['title']}")

# 运行
asyncio.run(basic_crawl())
```

### 批量下载示例
```bash
# 下载特定关键词的前50个视频（720P）
python main.py --keywords "机器学习" "人工智能" --limit 50 --quality 64 --download

# 使用多线程下载，设置存储限制
python main.py --concurrent 5 --max-size-gb 100 --download
```

## ⚠️ 注意事项和限制

### 使用限制
- **仅用于学习和研究目的**，禁止用于非法用途
- **遵守 B 站用户协议**和相关法律法规
- **避免频繁请求**，防止触发反爬虫机制
- **尊重版权**，下载的视频仅用于研究和评测

### 技术限制
- 依赖 B 站 API 稳定性，API 变更可能影响功能
- 下载速度受网络环境和 B 站服务器限制
- 某些视频可能因版权或地区限制无法下载
- 需要有效的 B 站账号进行登录

### 性能建议
- 建议并发数不超过 5，避免触发限制
- 定期清理日志文件，防止占用过多空间
- 使用 SSD 存储提高下载和处理速度
- 在网络稳定的环境下运行

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 GNU General Public License Version 3 许可证，详见 [LICENSE](../LICENSE) 文件。

## 🔗 相关链接

- [Bilibili-API 主项目](../)
- [B站开发者文档](https://github.com/SocialSisterYi/bilibili-API-collect)
- [项目 Issues](https://github.com/your-username/bilibili-api/issues)

---

**免责声明**：本工具仅供学习和研究使用，使用者需自行承担使用风险，开发者不对任何损失或法律问题负责。
