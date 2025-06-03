# 搜索模块文档 (search.py)

## 1. 模块简介

搜索模块提供哔哩哔哩视频搜索和筛选服务，支持关键词搜索、分页获取、结果过滤和去重处理。基于bilibili_api的search模块实现，为视频数据采集提供精准的搜索功能。

**主要用途：**
- 基于关键词搜索B站视频
- 批量获取搜索结果
- 视频质量筛选和过滤
- 搜索结果去重和排序

## 2. 功能一览

### 2.1 核心功能

#### 2.1.1 关键词搜索
- **单关键词搜索**：支持单个关键词的视频搜索
- **多关键词搜索**：支持批量关键词搜索
- **搜索类型**：支持综合搜索、用户搜索、专栏搜索等
- **排序方式**：支持按相关度、播放量、发布时间等排序

#### 2.1.2 分页处理
- **自动分页**：自动处理搜索结果分页
- **页面限制**：可配置每个关键词的最大页面数
- **结果限制**：可配置每个关键词的最大结果数
- **增量获取**：支持增量获取搜索结果

#### 2.1.3 结果过滤
- **播放量过滤**：按最小播放量过滤视频
- **时长过滤**：按视频时长范围过滤
- **发布时间过滤**：按发布时间范围过滤
- **UP主过滤**：按UP主粉丝数等条件过滤
- **质量评分**：基于多维度指标计算视频质量分

#### 2.1.4 去重处理
- **BV号去重**：基于视频BV号去除重复视频
- **标题相似度**：基于标题相似度去除近似重复视频
- **UP主去重**：限制同一UP主的视频数量
- **时间窗口去重**：在时间窗口内去除重复内容

#### 2.1.5 数据标准化
- **字段映射**：将API返回数据映射为标准格式
- **数据清洗**：清理和标准化文本数据
- **类型转换**：确保数据类型的一致性
- **缺失值处理**：处理API返回的缺失字段

### 2.2 主要类和方法

#### 2.2.1 BiliSearch类
**初始化参数：**
- `credential`: 登录凭证对象
- `config`: 配置字典，包含搜索相关配置

**主要方法：**
- `search_videos(keyword, limit=100)`: 搜索单个关键词的视频
- `batch_search(keywords, limit_per_keyword=100)`: 批量搜索多个关键词
- `search_with_filter(keyword, filters)`: 带过滤条件的搜索
- `get_search_suggestions(keyword)`: 获取搜索建议
- `_filter_videos(videos, filters)`: 过滤视频结果
- `_deduplicate_videos(videos)`: 去重处理
- `_calculate_quality_score(video)`: 计算视频质量分

#### 2.2.2 过滤器类
- `VideoFilter`: 视频过滤器基类
- `PlayCountFilter`: 播放量过滤器
- `DurationFilter`: 时长过滤器
- `DateFilter`: 日期过滤器
- `QualityFilter`: 质量过滤器

## 3. 使用示例

### 3.1 基本使用

#### 3.1.1 简单搜索
```python
import asyncio
from utils.login import BiliLogin
from utils.search import BiliSearch
from config.settings import load_config

async def main():
    # 登录
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    # 创建搜索器
    search = BiliSearch(credential, config)
    
    # 搜索视频
    videos = await search.search_videos("测试关键词", limit=50)
    
    print(f"找到 {len(videos)} 个视频")
    for video in videos[:5]:  # 显示前5个结果
        print(f"标题: {video['title']}")
        print(f"BV号: {video['bvid']}")
        print(f"播放量: {video['play']}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3.1.2 批量搜索
```python
async def batch_search_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    search = BiliSearch(credential, config)
    
    # 批量搜索多个关键词
    keywords = ["关键词1", "关键词2", "关键词3"]
    all_videos = await search.batch_search(keywords, limit_per_keyword=30)
    
    print(f"总共找到 {len(all_videos)} 个视频")
    
    # 按关键词分组统计
    keyword_stats = {}
    for video in all_videos:
        keyword = video.get('search_keyword', '未知')
        keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
    
    for keyword, count in keyword_stats.items():
        print(f"{keyword}: {count} 个视频")
```

#### 3.1.3 带过滤条件的搜索
```python
async def filtered_search_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    search = BiliSearch(credential, config)
    
    # 定义过滤条件
    filters = {
        "min_play": 10000,        # 最小播放量
        "max_duration": 300,      # 最大时长(秒)
        "min_like_ratio": 0.05,   # 最小点赞率
        "min_quality_score": 0.6  # 最小质量分
    }
    
    # 执行过滤搜索
    videos = await search.search_with_filter("测试关键词", filters)
    
    print(f"过滤后找到 {len(videos)} 个高质量视频")
    for video in videos:
        print(f"标题: {video['title']}")
        print(f"播放量: {video['play']}, 点赞率: {video.get('like_ratio', 0):.3f}")
        print(f"质量分: {video.get('quality_score', 0):.3f}")
        print("-" * 40)
```

### 3.2 高级功能

#### 3.2.1 自定义过滤器
```python
async def custom_filter_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    search = BiliSearch(credential, config)
    
    # 搜索原始结果
    videos = await search.search_videos("测试关键词", limit=100)
    
    # 自定义过滤逻辑
    def custom_filter(video):
        # 过滤条件：播放量>5万，时长<5分钟，点赞数>100
        return (video.get('play', 0) > 50000 and 
                video.get('duration', 0) < 300 and
                video.get('like', 0) > 100)
    
    # 应用自定义过滤器
    filtered_videos = [v for v in videos if custom_filter(v)]
    
    print(f"自定义过滤后: {len(filtered_videos)} 个视频")
```

#### 3.2.2 搜索建议
```python
async def search_suggestions_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    search = BiliSearch(credential, config)
    
    # 获取搜索建议
    suggestions = await search.get_search_suggestions("测试")
    
    print("搜索建议:")
    for suggestion in suggestions:
        print(f"- {suggestion}")
```

#### 3.2.3 质量评分
```python
async def quality_scoring_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    search = BiliSearch(credential, config)
    
    # 搜索视频
    videos = await search.search_videos("测试关键词", limit=20)
    
    # 计算质量分并排序
    for video in videos:
        quality_score = search._calculate_quality_score(video)
        video['quality_score'] = quality_score
    
    # 按质量分排序
    videos.sort(key=lambda x: x['quality_score'], reverse=True)
    
    print("按质量分排序的视频:")
    for i, video in enumerate(videos[:10], 1):
        print(f"{i}. {video['title']}")
        print(f"   质量分: {video['quality_score']:.3f}")
        print(f"   播放量: {video['play']}, 点赞: {video['like']}")
        print()
```

### 3.3 配置使用

#### 3.3.1 搜索配置
```python
config = {
    "search": {
        "default_order": "totalrank",        # 默认排序方式
        "max_pages_per_keyword": 10,         # 每个关键词最大页数
        "page_size": 20,                     # 每页结果数
        "request_interval": 1.0,             # 请求间隔(秒)
        "enable_deduplication": True,        # 启用去重
        "quality_threshold": 0.5,            # 质量分阈值
        "filters": {                         # 默认过滤条件
            "min_play": 1000,
            "min_duration": 10,
            "max_duration": 600
        }
    }
}

search = BiliSearch(credential, config)
```

#### 3.3.2 过滤配置
```python
# 详细过滤配置
filter_config = {
    "play_filter": {
        "min_play": 5000,                    # 最小播放量
        "max_play": 10000000                 # 最大播放量
    },
    "duration_filter": {
        "min_duration": 30,                  # 最小时长(秒)
        "max_duration": 300                  # 最大时长(秒)
    },
    "date_filter": {
        "start_date": "2023-01-01",          # 开始日期
        "end_date": "2024-12-31"             # 结束日期
    },
    "quality_filter": {
        "min_like_ratio": 0.02,              # 最小点赞率
        "min_coin_ratio": 0.01,              # 最小投币率
        "min_favorite_ratio": 0.01           # 最小收藏率
    }
}

videos = await search.search_with_filter("关键词", filter_config)
```

### 3.4 错误处理

#### 3.4.1 搜索异常处理
```python
from utils.search import BiliSearch, SearchException, RateLimitError

async def safe_search():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    search = BiliSearch(credential, config)
    
    try:
        videos = await search.search_videos("测试关键词", limit=100)
        return videos
        
    except RateLimitError as e:
        print(f"请求频率限制: {e}")
        # 等待一段时间后重试
        await asyncio.sleep(60)
        
    except SearchException as e:
        print(f"搜索错误: {e}")
        
    except Exception as e:
        print(f"未知错误: {e}")
        
    return []
```

## 4. 配置说明

### 4.1 搜索配置项

```json
{
  "search": {
    "default_order": "totalrank",           // 默认排序方式
    "search_type": "video",                 // 搜索类型
    "max_pages_per_keyword": 10,            // 每个关键词最大页数
    "page_size": 20,                        // 每页结果数
    "request_interval": 1.0,                // 请求间隔(秒)
    "max_retries": 3,                       // 最大重试次数
    "timeout": 30,                          // 请求超时(秒)
    "enable_deduplication": true,           // 启用去重
    "dedup_similarity_threshold": 0.8,      // 去重相似度阈值
    "quality_threshold": 0.5,               // 质量分阈值
    "filters": {                            // 默认过滤条件
      "min_play": 1000,                     // 最小播放量
      "min_duration": 10,                   // 最小时长(秒)
      "max_duration": 600,                  // 最大时长(秒)
      "min_like_ratio": 0.01,               // 最小点赞率
      "min_quality_score": 0.3              // 最小质量分
    }
  }
}
```

### 4.2 排序方式说明

- `totalrank`: 综合排序（默认）
- `click`: 按播放量排序
- `pubdate`: 按发布时间排序
- `dm`: 按弹幕数排序
- `stow`: 按收藏数排序
- `scores`: 按评分排序

### 4.3 搜索类型说明

- `video`: 视频搜索（默认）
- `bangumi`: 番剧搜索
- `pgc`: PGC内容搜索
- `live`: 直播搜索
- `article`: 专栏搜索
- `topic`: 话题搜索

## 5. 数据格式

### 5.1 搜索结果格式

```json
{
  "bvid": "BV1234567890",
  "aid": 123456789,
  "title": "视频标题",
  "description": "视频描述",
  "duration": 120,
  "play": 10000,
  "like": 500,
  "coin": 100,
  "favorite": 200,
  "share": 50,
  "reply": 300,
  "danmaku": 150,
  "pubdate": 1640995200,
  "owner": {
    "mid": 987654321,
    "name": "UP主昵称",
    "face": "头像URL"
  },
  "pic": "封面URL",
  "tag": "标签",
  "search_keyword": "搜索关键词",
  "quality_score": 0.75,
  "like_ratio": 0.05,
  "coin_ratio": 0.01,
  "favorite_ratio": 0.02
}
```

### 5.2 过滤器格式

```json
{
  "min_play": 1000,
  "max_play": 10000000,
  "min_duration": 30,
  "max_duration": 600,
  "min_like": 10,
  "min_like_ratio": 0.01,
  "min_coin_ratio": 0.005,
  "min_favorite_ratio": 0.01,
  "min_quality_score": 0.5,
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "exclude_keywords": ["广告", "推广"],
  "include_keywords": ["教程", "测评"]
}
```

## 6. 依赖说明

### 6.1 必需依赖
- `bilibili-api-python`: B站API库
- `asyncio`: 异步编程支持
- `json`: JSON数据处理
- `re`: 正则表达式
- `datetime`: 日期时间处理

### 6.2 可选依赖
- `jieba`: 中文分词（用于文本相似度计算）
- `difflib`: 文本相似度计算

### 6.3 安装命令
```bash
# 必需依赖
pip install bilibili-api-python

# 可选依赖
pip install jieba
```

## 7. 常见问题

### 7.1 搜索相关
- **问题**: 搜索结果为空
- **解决**: 检查关键词是否正确，调整过滤条件

### 7.2 性能相关
- **问题**: 搜索速度慢
- **解决**: 增加请求间隔，减少并发数

### 7.3 质量相关
- **问题**: 搜索结果质量低
- **解决**: 调整质量分阈值，增加过滤条件

---

**模块版本**: v1.0.0  
**最后更新**: 2025-01-20  
**维护者**: Claude 