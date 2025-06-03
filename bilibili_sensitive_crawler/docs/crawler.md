# 爬虫模块文档 (crawler.py)

## 1. 模块简介

爬虫模块提供哔哩哔哩视频详细信息采集服务，负责获取视频的完整元数据信息。基于bilibili_api的video模块实现，支持批量采集、数据结构化和异常处理。

**主要用途：**
- 采集视频详细信息和元数据
- 获取UP主信息和统计数据
- 提取视频标签和分类信息
- 构建结构化的视频数据集

## 2. 功能一览

### 2.1 核心功能

#### 2.1.1 基本信息采集
- **视频基础信息**：标题、描述、时长、发布时间、封面等
- **视频标识**：BV号、AV号、CID等唯一标识
- **分P信息**：多P视频的分集信息
- **视频状态**：发布状态、审核状态、可见性等

#### 2.1.2 统计数据采集
- **播放数据**：播放量、弹幕数、评论数
- **互动数据**：点赞数、投币数、收藏数、分享数
- **趋势数据**：历史播放趋势、增长率等
- **排行数据**：分区排行、全站排行等

#### 2.1.3 UP主信息采集
- **基本信息**：昵称、头像、个人简介
- **认证信息**：认证类型、认证描述
- **统计信息**：粉丝数、关注数、投稿数
- **等级信息**：用户等级、会员状态等

#### 2.1.4 扩展信息采集
- **标签信息**：视频标签、分类标签
- **相关视频**：推荐视频、相关视频列表
- **AI总结**：视频AI生成的总结信息
- **字幕信息**：视频字幕文件和内容

#### 2.1.5 数据处理
- **数据清洗**：清理和标准化采集的数据
- **格式转换**：统一数据格式和类型
- **缺失值处理**：处理API返回的缺失字段
- **数据验证**：验证数据的完整性和有效性

### 2.2 主要类和方法

#### 2.2.1 BiliCrawler类
**初始化参数：**
- `credential`: 登录凭证对象
- `config`: 配置字典，包含爬虫相关配置

**主要方法：**
- `get_video_info(bvid)`: 获取单个视频的完整信息
- `batch_get_video_info(bvids)`: 批量获取多个视频信息
- `get_video_basic_info(bvid)`: 获取视频基本信息
- `get_video_stat(bvid)`: 获取视频统计数据
- `get_video_tags(bvid)`: 获取视频标签信息
- `get_video_pages(bvid)`: 获取视频分P信息
- `get_owner_info(mid)`: 获取UP主详细信息
- `_process_video_data(raw_data)`: 处理原始视频数据
- `_validate_video_info(video_info)`: 验证视频信息完整性

#### 2.2.2 数据处理类
- `VideoDataProcessor`: 视频数据处理器
- `OwnerDataProcessor`: UP主数据处理器
- `TagDataProcessor`: 标签数据处理器
- `StatDataProcessor`: 统计数据处理器

## 3. 使用示例

### 3.1 基本使用

#### 3.1.1 获取单个视频信息
```python
import asyncio
from utils.login import BiliLogin
from utils.crawler import BiliCrawler
from config.settings import load_config

async def main():
    # 登录
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    # 创建爬虫
    crawler = BiliCrawler(credential, config)
    
    # 获取视频信息
    video_info = await crawler.get_video_info("BV1234567890")
    
    print(f"视频标题: {video_info['basic_info']['title']}")
    print(f"UP主: {video_info['owner']['name']}")
    print(f"播放量: {video_info['stat']['view']}")
    print(f"时长: {video_info['basic_info']['duration']} 秒")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3.1.2 批量获取视频信息
```python
async def batch_crawl_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    crawler = BiliCrawler(credential, config)
    
    # 批量获取视频信息
    bvids = ["BV1234567890", "BV0987654321", "BV1111111111"]
    video_infos = await crawler.batch_get_video_info(bvids)
    
    print(f"成功获取 {len(video_infos)} 个视频信息")
    
    for video_info in video_infos:
        if video_info:  # 检查是否获取成功
            print(f"标题: {video_info['basic_info']['title']}")
            print(f"播放量: {video_info['stat']['view']}")
            print("-" * 40)
```

#### 3.1.3 获取特定信息
```python
async def specific_info_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    crawler = BiliCrawler(credential, config)
    
    bvid = "BV1234567890"
    
    # 获取基本信息
    basic_info = await crawler.get_video_basic_info(bvid)
    print(f"标题: {basic_info['title']}")
    print(f"描述: {basic_info['desc']}")
    
    # 获取统计数据
    stat_info = await crawler.get_video_stat(bvid)
    print(f"播放量: {stat_info['view']}")
    print(f"点赞数: {stat_info['like']}")
    
    # 获取标签信息
    tags = await crawler.get_video_tags(bvid)
    print(f"标签: {[tag['tag_name'] for tag in tags]}")
    
    # 获取分P信息
    pages = await crawler.get_video_pages(bvid)
    print(f"分P数量: {len(pages)}")
```

### 3.2 高级功能

#### 3.2.1 自定义数据处理
```python
async def custom_processing_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    crawler = BiliCrawler(credential, config)
    
    # 自定义数据处理函数
    def custom_processor(video_info):
        # 添加自定义字段
        video_info['custom_score'] = (
            video_info['stat']['like'] * 0.3 +
            video_info['stat']['coin'] * 0.5 +
            video_info['stat']['favorite'] * 0.2
        )
        
        # 标准化时长格式
        duration = video_info['basic_info']['duration']
        video_info['duration_formatted'] = f"{duration // 60}:{duration % 60:02d}"
        
        return video_info
    
    # 获取并处理视频信息
    video_info = await crawler.get_video_info("BV1234567890")
    processed_info = custom_processor(video_info)
    
    print(f"自定义评分: {processed_info['custom_score']}")
    print(f"格式化时长: {processed_info['duration_formatted']}")
```

#### 3.2.2 错误处理和重试
```python
async def robust_crawling_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    crawler = BiliCrawler(credential, config)
    
    async def safe_get_video_info(bvid, max_retries=3):
        for attempt in range(max_retries):
            try:
                video_info = await crawler.get_video_info(bvid)
                return video_info
            except Exception as e:
                print(f"获取 {bvid} 失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    print(f"最终获取 {bvid} 失败")
                    return None
    
    # 使用安全的获取方法
    bvids = ["BV1234567890", "BV0987654321", "BV1111111111"]
    results = []
    
    for bvid in bvids:
        result = await safe_get_video_info(bvid)
        if result:
            results.append(result)
    
    print(f"成功获取 {len(results)} 个视频信息")
```

#### 3.2.3 数据验证和清洗
```python
async def data_validation_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    crawler = BiliCrawler(credential, config)
    
    def validate_and_clean(video_info):
        # 验证必需字段
        required_fields = ['basic_info', 'stat', 'owner']
        for field in required_fields:
            if field not in video_info:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 清洗数据
        # 确保数值字段为整数
        for stat_key in ['view', 'like', 'coin', 'favorite']:
            if stat_key in video_info['stat']:
                video_info['stat'][stat_key] = int(video_info['stat'][stat_key])
        
        # 清洗文本字段
        if 'title' in video_info['basic_info']:
            video_info['basic_info']['title'] = video_info['basic_info']['title'].strip()
        
        # 添加数据质量标记
        video_info['data_quality'] = {
            'complete': True,
            'validated': True,
            'cleaned': True
        }
        
        return video_info
    
    # 获取并验证视频信息
    video_info = await crawler.get_video_info("BV1234567890")
    validated_info = validate_and_clean(video_info)
    
    print(f"数据质量: {validated_info['data_quality']}")
```

### 3.3 配置使用

#### 3.3.1 爬虫配置
```python
config = {
    "crawler": {
        "request_interval": 1.0,             # 请求间隔(秒)
        "max_retries": 3,                    # 最大重试次数
        "timeout": 30,                       # 请求超时(秒)
        "concurrent_limit": 5,               # 并发限制
        "enable_cache": True,                # 启用缓存
        "cache_expire": 3600,                # 缓存过期时间(秒)
        "include_extended_info": True,       # 包含扩展信息
        "include_ai_summary": False,         # 包含AI总结
        "include_subtitle": False,           # 包含字幕信息
        "data_validation": True              # 启用数据验证
    }
}

crawler = BiliCrawler(credential, config)
```

#### 3.3.2 数据字段配置
```python
# 配置需要采集的数据字段
field_config = {
    "basic_fields": [
        "bvid", "aid", "title", "desc", "duration", 
        "pubdate", "pic", "ctime"
    ],
    "stat_fields": [
        "view", "danmaku", "reply", "favorite", 
        "coin", "share", "like"
    ],
    "owner_fields": [
        "mid", "name", "face", "fans", "level"
    ],
    "extended_fields": [
        "tags", "pages", "subtitle", "ai_summary"
    ]
}

# 应用配置
crawler.set_field_config(field_config)
```

### 3.4 数据保存

#### 3.4.1 保存到JSON文件
```python
import json
from pathlib import Path

async def save_to_json_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    crawler = BiliCrawler(credential, config)
    
    # 获取视频信息
    video_info = await crawler.get_video_info("BV1234567890")
    
    # 保存到JSON文件
    output_dir = Path("data/json")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"{video_info['basic_info']['bvid']}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(video_info, f, ensure_ascii=False, indent=2)
    
    print(f"视频信息已保存到: {output_file}")
```

#### 3.4.2 批量保存
```python
async def batch_save_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    crawler = BiliCrawler(credential, config)
    
    bvids = ["BV1234567890", "BV0987654321", "BV1111111111"]
    output_dir = Path("data/json")
    output_dir.mkdir(exist_ok=True)
    
    success_count = 0
    
    for bvid in bvids:
        try:
            video_info = await crawler.get_video_info(bvid)
            
            output_file = output_dir / f"{bvid}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(video_info, f, ensure_ascii=False, indent=2)
            
            success_count += 1
            print(f"已保存: {bvid}")
            
        except Exception as e:
            print(f"保存 {bvid} 失败: {e}")
    
    print(f"成功保存 {success_count}/{len(bvids)} 个视频信息")
```

## 4. 配置说明

### 4.1 爬虫配置项

```json
{
  "crawler": {
    "request_interval": 1.0,                // 请求间隔(秒)
    "max_retries": 3,                       // 最大重试次数
    "retry_interval": 2,                    // 重试间隔(秒)
    "timeout": 30,                          // 请求超时(秒)
    "concurrent_limit": 5,                  // 并发限制
    "enable_cache": true,                   // 启用缓存
    "cache_expire": 3600,                   // 缓存过期时间(秒)
    "include_extended_info": true,          // 包含扩展信息
    "include_ai_summary": false,            // 包含AI总结
    "include_subtitle": false,              // 包含字幕信息
    "include_related_videos": false,        // 包含相关视频
    "data_validation": true,                // 启用数据验证
    "auto_clean_data": true,                // 自动清洗数据
    "save_raw_data": false                  // 保存原始数据
  }
}
```

### 4.2 数据字段配置

```json
{
  "fields": {
    "basic_info": [
      "bvid", "aid", "title", "desc", "duration",
      "pubdate", "ctime", "pic", "state", "copyright"
    ],
    "stat": [
      "view", "danmaku", "reply", "favorite",
      "coin", "share", "like", "now_rank", "his_rank"
    ],
    "owner": [
      "mid", "name", "face", "fans", "friend",
      "attention", "sign", "level", "official"
    ],
    "pages": [
      "cid", "page", "part", "duration", "dimension"
    ],
    "tags": [
      "tag_id", "tag_name", "cover", "head_cover",
      "content", "short_content", "type"
    ]
  }
}
```

## 5. 数据格式

### 5.1 完整视频信息格式

```json
{
  "basic_info": {
    "bvid": "BV1234567890",
    "aid": 123456789,
    "title": "视频标题",
    "desc": "视频描述",
    "duration": 120,
    "pubdate": 1640995200,
    "ctime": 1640995200,
    "pic": "https://i0.hdslb.com/bfs/archive/example.jpg",
    "state": 0,
    "copyright": 1
  },
  "stat": {
    "view": 10000,
    "danmaku": 150,
    "reply": 300,
    "favorite": 200,
    "coin": 100,
    "share": 50,
    "like": 500,
    "now_rank": 0,
    "his_rank": 0
  },
  "owner": {
    "mid": 987654321,
    "name": "UP主昵称",
    "face": "https://i0.hdslb.com/bfs/face/example.jpg",
    "fans": 50000,
    "friend": 100,
    "attention": 200,
    "sign": "个人简介",
    "level": 5,
    "official": {
      "role": 0,
      "title": "",
      "desc": ""
    }
  },
  "pages": [
    {
      "cid": 123456789,
      "page": 1,
      "part": "P1",
      "duration": 120,
      "dimension": {
        "width": 1920,
        "height": 1080,
        "rotate": 0
      }
    }
  ],
  "tags": [
    {
      "tag_id": 123,
      "tag_name": "标签名称",
      "cover": "",
      "head_cover": "",
      "content": "标签描述",
      "short_content": "简短描述",
      "type": 0
    }
  ],
  "crawl_info": {
    "crawl_time": 1640995200,
    "data_version": "1.0",
    "source": "bilibili_api"
  }
}
```

### 5.2 错误信息格式

```json
{
  "error": {
    "code": -404,
    "message": "视频不存在",
    "bvid": "BV1234567890",
    "timestamp": 1640995200
  }
}
```

## 6. 依赖说明

### 6.1 必需依赖
- `bilibili-api-python`: B站API库
- `asyncio`: 异步编程支持
- `json`: JSON数据处理
- `datetime`: 日期时间处理
- `pathlib`: 路径操作

### 6.2 可选依赖
- `aiofiles`: 异步文件操作
- `aiohttp`: HTTP客户端（用于缓存）

### 6.3 安装命令
```bash
# 必需依赖
pip install bilibili-api-python

# 可选依赖
pip install aiofiles aiohttp
```

## 7. 常见问题

### 7.1 采集相关
- **问题**: 视频信息获取失败
- **解决**: 检查BV号是否正确，视频是否存在

### 7.2 性能相关
- **问题**: 采集速度慢
- **解决**: 调整请求间隔，启用缓存

### 7.3 数据相关
- **问题**: 数据不完整
- **解决**: 启用数据验证，检查网络连接

---

**模块版本**: v1.0.0  
**最后更新**: 2025-01-20  
**维护者**: Claude 