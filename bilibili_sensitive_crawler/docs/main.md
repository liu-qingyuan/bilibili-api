# 主入口模块 (main.py)

## 模块简介

主入口模块是bilibili_sensitive_crawler项目的核心控制器，提供完整的命令行界面和工作流程管理。该模块整合了登录、搜索、爬取、下载、过滤和数据集管理等所有功能，支持灵活的参数配置和多种运行模式。

### 主要特性

- **统一入口**: 提供单一命令行入口，整合所有功能模块
- **灵活配置**: 支持配置文件和命令行参数双重配置方式
- **多种模式**: 支持完整爬取、仅信息获取、文件清理等多种运行模式
- **错误处理**: 完善的异常处理和重试机制
- **日志管理**: 详细的日志记录和多级别日志输出
- **跨平台**: 支持Windows、Linux、macOS等多平台运行

## 功能一览

### 1. 命令行参数管理
- **基本参数**: 配置文件路径、调试模式、日志设置
- **登录参数**: 强制登录、Cookie登录选项
- **搜索参数**: 关键词列表、数量限制设置
- **下载参数**: 视频质量、下载控制选项
- **过滤参数**: 时长过滤、文件清理选项
- **执行控制**: 重试机制、间隔控制、恢复功能

### 2. 工作流程控制
- **初始化流程**: 日志配置、参数解析、配置加载
- **登录流程**: 自动登录、凭证验证、状态检查
- **搜索流程**: 关键词搜索、结果去重、分页处理
- **爬取流程**: 信息获取、数据保存、进度跟踪
- **下载流程**: 视频下载、质量选择、并发控制
- **清理流程**: 文件过滤、孤立文件清理、报告生成

### 3. 配置管理
- **配置加载**: 从JSON/YAML文件加载配置
- **参数覆盖**: 命令行参数优先级处理
- **默认配置**: 自动生成默认配置文件
- **配置验证**: 参数有效性检查和错误提示

### 4. 错误处理与日志
- **异常捕获**: 全局异常处理和错误分类
- **重试机制**: 网络错误自动重试
- **日志记录**: 多级别日志输出和文件记录
- **进度报告**: 实时进度显示和统计信息

## 使用示例

### 基本使用

```bash
# 基本爬取（使用默认配置）
python main.py --keywords "测试关键词" --limit 50

# 生成默认配置文件
python main.py --generate-config

# 启用调试模式
python main.py --debug --keywords "测试" --limit 10
```

### 登录相关

```bash
# 强制重新登录
python main.py --force-login --keywords "测试"

# 使用Cookie登录
python main.py --use-cookie --keywords "测试"

# 指定配置文件
python main.py --config custom_config.json --keywords "测试"
```

### 搜索和爬取

```bash
# 多关键词搜索
python main.py --keywords "关键词1" "关键词2" "关键词3" --limit 100

# 仅获取视频信息，不下载
python main.py --info-only --keywords "测试" --limit 50

# 指定视频质量下载
python main.py --download --quality 64 --keywords "测试" --limit 20

# 设置最大视频数量
python main.py --keywords "测试" --max-videos 500
```

### 文件管理

```bash
# 删除超长视频（超过30秒）
python main.py --delete-long-videos --max-duration 30

# 列出超长视频（不删除）
python main.py --list-long-videos --max-duration 60

# 试运行模式（不实际删除）
python main.py --delete-long-videos --dry-run --max-duration 30

# 生成删除报告
python main.py --delete-long-videos --generate-report --max-duration 30
```

### 文件分析和清理

```bash
# 分析文件匹配情况
python main.py --analyze-files

# 清理孤立的视频文件
python main.py --clean-orphan-videos

# 清理孤立的JSON文件
python main.py --clean-orphan-jsons

# 保存分析报告
python main.py --analyze-files --save-analysis-report
```

### 高级用法

```bash
# 完整工作流程
python main.py \
    --keywords "敏感内容" "测试视频" \
    --limit 200 \
    --download \
    --quality 32 \
    --max-duration 30 \
    --generate-report \
    --verbose

# 恢复上次爬取
python main.py --resume --keywords "测试"

# 自定义目录和参数
python main.py \
    --metadata-dir "custom/json" \
    --video-dir "custom/videos" \
    --keywords "测试" \
    --limit 100 \
    --max-retries 5 \
    --interval 2.0
```

## 配置说明

### 命令行参数详解

```json
{
  "基本参数": {
    "--config": "配置文件路径，默认: config/config.json",
    "--debug": "启用调试日志",
    "--verbose": "启用详细日志输出",
    "--log-file": "日志文件路径，默认: logs/bili_crawler.log"
  },
  "配置相关": {
    "--generate-config": "生成默认配置文件并退出"
  },
  "登录相关": {
    "--force-login": "强制重新登录",
    "--use-cookie": "使用Cookie登录"
  },
  "搜索相关": {
    "--keywords": "搜索关键词列表",
    "--limit": "每个关键词的视频数量限制，默认: 100"
  },
  "爬取相关": {
    "--download": "下载视频文件",
    "--info-only": "仅爬取视频信息，不下载视频",
    "--quality": "视频质量代码，默认: 32 (480P)"
  },
  "数据集相关": {
    "--metadata-dir": "元数据保存目录",
    "--video-dir": "视频保存目录",
    "--max-videos": "最大视频数量，默认: 1000"
  },
  "执行控制": {
    "--resume": "恢复上次爬取",
    "--max-retries": "最大重试次数，默认: 3",
    "--interval": "请求间隔时间（秒），默认: 1.0"
  },
  "视频过滤": {
    "--delete-long-videos": "删除超出指定时长的视频",
    "--list-long-videos": "列出超出指定时长的视频",
    "--max-duration": "最大允许视频时长（秒），默认: 30",
    "--dry-run": "试运行模式，不实际删除文件",
    "--generate-report": "生成删除操作报告"
  },
  "文件清理": {
    "--analyze-files": "分析视频文件和JSON文件的匹配情况",
    "--clean-orphan-videos": "清理孤立的视频文件",
    "--clean-orphan-jsons": "清理孤立的JSON文件",
    "--save-analysis-report": "保存文件分析报告到文件"
  }
}
```

### 配置文件结构

```json
{
  "login": {
    "credential_file": "config/credential.json",
    "auto_login": true,
    "login_timeout": 300
  },
  "search": {
    "default_keywords": ["测试"],
    "default_limit": 100,
    "search_type": "video",
    "order": "totalrank"
  },
  "crawler": {
    "timeout": 30,
    "max_retries": 3,
    "request_interval": 1.0,
    "user_agents": ["Mozilla/5.0..."]
  },
  "downloader": {
    "video_dir": "data/videos",
    "default_quality": 32,
    "max_concurrent": 3,
    "chunk_size": 1048576
  },
  "dataset": {
    "json_dir": "data/json",
    "index_file": "data/json/index.json",
    "update_index_on_save": true
  },
  "filter": {
    "max_duration": 30,
    "min_duration": 5,
    "quality_threshold": 0.7
  }
}
```

## 数据格式

### 命令行参数对象

```json
{
  "config": "config/config.json",
  "debug": false,
  "verbose": false,
  "log_file": "logs/bili_crawler.log",
  "generate_config": false,
  "force_login": false,
  "use_cookie": false,
  "keywords": ["关键词1", "关键词2"],
  "limit": 100,
  "download": true,
  "info_only": false,
  "quality": 32,
  "metadata_dir": "data/json",
  "video_dir": "data/videos",
  "max_videos": 1000,
  "resume": false,
  "max_retries": 3,
  "interval": 1.0,
  "delete_long_videos": false,
  "list_long_videos": false,
  "max_duration": 30,
  "dry_run": false,
  "generate_report": false,
  "analyze_files": false,
  "clean_orphan_videos": false,
  "clean_orphan_jsons": false,
  "save_analysis_report": false
}
```

### 执行结果格式

```json
{
  "status": "success",
  "start_time": "2025-01-20 10:00:00",
  "end_time": "2025-01-20 12:30:00",
  "duration": 9000,
  "statistics": {
    "total_keywords": 3,
    "total_searched": 150,
    "total_crawled": 145,
    "total_downloaded": 140,
    "total_filtered": 5,
    "success_rate": 0.967
  },
  "results": {
    "searched_videos": 150,
    "crawled_videos": 145,
    "downloaded_videos": 140,
    "filtered_videos": 5,
    "errors": 5
  },
  "errors": [
    {
      "type": "network_error",
      "message": "连接超时",
      "bvid": "BV1234567890",
      "timestamp": "2025-01-20 11:15:30"
    }
  ]
}
```

## 工作流程

### 1. 初始化阶段

```python
# 解析命令行参数
args = parse_args()

# 设置日志配置
setup_logging(args.debug, args.log_file)

# 加载配置文件
config = load_config(args.config)

# 更新配置（命令行参数优先）
update_config_from_args(config, args)
```

### 2. 登录阶段

```python
# 初始化登录管理器
login_manager = BiliLogin(config["login"])

# 执行登录
if args.force_login or not login_manager.has_valid_credential():
    credential = await login_manager.login()
else:
    credential = login_manager.load_credential()
```

### 3. 搜索阶段

```python
# 初始化搜索管理器
search_manager = BiliSearch(credential, config["search"])

# 执行搜索
all_videos = []
for keyword in args.keywords:
    videos = await search_manager.search_videos(
        keyword, 
        limit=args.limit
    )
    all_videos.extend(videos)

# 去重处理
unique_videos = search_manager.deduplicate_videos(all_videos)
```

### 4. 爬取阶段

```python
# 初始化爬虫管理器
crawler = BiliCrawler(credential, config["crawler"])

# 初始化数据集管理器
dataset_manager = DatasetManager(
    config["dataset"]["json_dir"],
    config["downloader"]["video_dir"],
    config["dataset"]
)

# 爬取视频信息
for video in unique_videos:
    try:
        video_info = await crawler.get_video_info(video["bvid"])
        dataset_manager.save_video_info(video_info)
    except Exception as e:
        logger.error(f"爬取失败: {video['bvid']}, 错误: {e}")
```

### 5. 下载阶段

```python
if args.download:
    # 初始化下载管理器
    downloader = BiliDownloader(credential, config["downloader"])
    
    # 下载视频
    for video in crawled_videos:
        try:
            await downloader.download_video(
                video["bvid"],
                quality=args.quality
            )
        except Exception as e:
            logger.error(f"下载失败: {video['bvid']}, 错误: {e}")
```

### 6. 清理阶段

```python
if args.delete_long_videos or args.list_long_videos:
    # 初始化视频过滤器
    video_filter = VideoFilter(
        config["dataset"]["json_dir"],
        config["downloader"]["video_dir"],
        config["filter"]
    )
    
    # 执行过滤
    result = video_filter.filter_by_duration(
        max_duration=args.max_duration,
        delete_files=args.delete_long_videos and not args.dry_run,
        generate_report=args.generate_report
    )

if args.analyze_files:
    # 初始化文件分析器
    file_analyzer = FileAnalyzer(
        config["dataset"]["json_dir"],
        config["downloader"]["video_dir"]
    )
    
    # 执行分析
    analysis_result = file_analyzer.analyze_files()
```

## 依赖说明

### 必需依赖

```bash
# 核心依赖
pip install bilibili-api-python>=16.0.0
pip install aiohttp>=3.8.0
pip install aiofiles>=0.8.0

# 命令行和日志
pip install argparse  # Python内置
pip install logging   # Python内置

# 数据处理
pip install json      # Python内置
pip install pathlib   # Python内置
```

### 可选依赖

```bash
# 配置文件支持
pip install pyyaml>=6.0  # YAML配置文件支持

# 进度显示
pip install rich>=12.0.0  # 美化输出

# 性能优化
pip install uvloop>=0.17.0  # Linux/macOS异步优化
```

### 系统要求

- **Python版本**: 3.8+
- **操作系统**: Windows 10+, Linux, macOS
- **内存要求**: 最少512MB，推荐2GB+
- **磁盘空间**: 根据下载视频数量而定
- **网络要求**: 稳定的互联网连接

## 常见问题

### Q1: 如何生成默认配置文件？

```bash
python main.py --generate-config
```

这将在`config/config.json`创建默认配置文件。

### Q2: 如何处理登录失败？

```bash
# 强制重新登录
python main.py --force-login

# 或删除凭证文件后重新运行
rm config/credential.json
python main.py
```

### Q3: 如何限制下载速度？

在配置文件中设置：

```json
{
  "crawler": {
    "request_interval": 2.0  // 增加请求间隔
  },
  "downloader": {
    "max_concurrent": 1      // 减少并发数
  }
}
```

### Q4: 如何恢复中断的爬取？

```bash
python main.py --resume --keywords "原关键词"
```

程序会自动跳过已爬取的视频。

### Q5: 如何处理内存不足？

```bash
# 减少并发数和批次大小
python main.py --keywords "测试" --limit 50 --max-videos 100
```

或在配置文件中调整：

```json
{
  "downloader": {
    "max_concurrent": 1,
    "chunk_size": 524288  // 减少块大小
  }
}
```

### Q6: 如何自定义日志级别？

```bash
# 调试模式（最详细）
python main.py --debug

# 详细模式
python main.py --verbose

# 指定日志文件
python main.py --log-file custom.log
```

### Q7: 如何批量处理多个关键词？

```bash
python main.py --keywords "关键词1" "关键词2" "关键词3" --limit 100
```

或创建脚本文件：

```bash
#!/bin/bash
keywords=("关键词1" "关键词2" "关键词3")
for keyword in "${keywords[@]}"; do
    python main.py --keywords "$keyword" --limit 100
done
``` 