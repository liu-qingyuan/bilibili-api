# 下载模块文档 (downloader.py)

## 1. 模块简介

下载模块提供哔哩哔哩视频文件下载服务，支持多清晰度视频下载、音视频合并、断点续传和并发控制。基于bilibili_api的video模块实现，使用FFmpeg进行音视频合并处理。

**主要用途：**
- 下载B站视频文件
- 音视频流分离下载和合并
- 支持多种清晰度选择
- 提供下载进度监控和错误处理

## 2. 功能一览

### 2.1 核心功能

#### 2.1.1 视频下载
- **多清晰度支持**：360P、480P、720P、1080P等多种清晰度
- **音视频分离**：分别下载视频流和音频流
- **自动合并**：使用FFmpeg自动合并音视频文件
- **格式支持**：支持MP4、FLV等多种视频格式

#### 2.1.2 下载控制
- **并发控制**：支持多线程并发下载，可配置并发数量
- **速度限制**：支持下载速度限制
- **断点续传**：支持下载中断后的断点续传
- **重试机制**：网络异常时自动重试，支持指数退避策略

#### 2.1.3 进度监控
- **实时进度**：实时显示下载进度和速度
- **状态回调**：支持下载状态变化回调
- **统计信息**：提供详细的下载统计信息
- **日志记录**：完整的下载过程日志记录

#### 2.1.4 错误处理
- **网络异常**：处理网络连接异常和超时
- **文件异常**：处理磁盘空间不足、权限错误等
- **合并异常**：处理FFmpeg合并失败等问题
- **智能重试**：根据错误类型选择合适的重试策略

#### 2.1.5 反爬虫机制
- **User-Agent轮换**：随机轮换User-Agent避免检测
- **请求延迟**：控制请求频率避免触发限制
- **代理支持**：支持HTTP/SOCKS代理
- **Cookie管理**：自动管理和更新Cookie

### 2.2 主要类和方法

#### 2.2.1 BiliDownloader类
**初始化参数：**
- `credential`: 登录凭证对象
- `output_dir`: 视频输出目录
- `config`: 配置字典，包含下载相关配置

**主要方法：**
- `download_video(bvid, quality=None)`: 下载单个视频
- `batch_download(bvids, quality=None)`: 批量下载多个视频
- `get_video_download_url(bvid, quality)`: 获取视频下载链接
- `download_stream(url, output_path)`: 下载单个流文件
- `merge_video_audio(video_path, audio_path, output_path)`: 合并音视频
- `check_ffmpeg()`: 检查FFmpeg是否可用
- `get_download_progress(bvid)`: 获取下载进度
- `pause_download(bvid)`: 暂停下载
- `resume_download(bvid)`: 恢复下载
- `cancel_download(bvid)`: 取消下载

#### 2.2.2 异常类
- `DownloadException`: 下载异常基类
- `NetworkError`: 网络连接错误
- `FileError`: 文件操作错误
- `MergeError`: 音视频合并错误
- `QualityNotAvailableError`: 清晰度不可用错误

## 3. 使用示例

### 3.1 基本使用

#### 3.1.1 简单下载
```python
import asyncio
from utils.login import BiliLogin
from utils.downloader import BiliDownloader
from config.settings import load_config

async def main():
    # 登录
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    # 创建下载器
    downloader = BiliDownloader(credential, "downloads", config)
    
    # 下载视频
    result = await downloader.download_video("BV1234567890")
    
    if result['success']:
        print(f"下载成功: {result['output_path']}")
    else:
        print(f"下载失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3.1.2 指定清晰度下载
```python
async def quality_download_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    # 下载720P视频
    result = await downloader.download_video("BV1234567890", quality=64)
    
    print(f"下载结果: {result}")
```

#### 3.1.3 批量下载
```python
async def batch_download_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    # 批量下载视频
    bvids = ["BV1234567890", "BV0987654321", "BV1111111111"]
    results = await downloader.batch_download(bvids, quality=32)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"成功下载 {success_count}/{len(bvids)} 个视频")
    
    for result in results:
        if result['success']:
            print(f"✓ {result['bvid']}: {result['output_path']}")
        else:
            print(f"✗ {result['bvid']}: {result['error']}")
```

### 3.2 高级功能

#### 3.2.1 进度监控
```python
async def progress_monitoring_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    # 定义进度回调函数
    def progress_callback(bvid, progress_info):
        percent = progress_info.get('percent', 0)
        speed = progress_info.get('speed', 0)
        eta = progress_info.get('eta', 0)
        
        print(f"{bvid}: {percent:.1f}% - {speed:.1f}KB/s - ETA: {eta}s")
    
    # 设置进度回调
    downloader.set_progress_callback(progress_callback)
    
    # 开始下载
    result = await downloader.download_video("BV1234567890")
    print(f"下载完成: {result}")
```

#### 3.2.2 断点续传
```python
async def resume_download_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    bvid = "BV1234567890"
    
    try:
        # 开始下载
        result = await downloader.download_video(bvid)
        
    except KeyboardInterrupt:
        print("下载被中断，稍后恢复...")
        
        # 恢复下载
        result = await downloader.resume_download(bvid)
        print(f"恢复下载结果: {result}")
```

#### 3.2.3 自定义下载配置
```python
async def custom_config_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    # 自定义下载配置
    download_config = {
        "downloader": {
            "default_quality": 64,           # 默认720P
            "concurrent_limit": 2,           # 并发数限制
            "chunk_size": 1024 * 1024,       # 1MB块大小
            "max_retries": 5,                # 最大重试次数
            "retry_interval": 3,             # 重试间隔
            "speed_limit": 5 * 1024 * 1024,  # 5MB/s速度限制
            "use_external_downloader": False, # 使用外部下载器
            "ffmpeg_path": "ffmpeg"          # FFmpeg路径
        }
    }
    
    downloader = BiliDownloader(credential, "downloads", download_config)
    
    result = await downloader.download_video("BV1234567890")
    print(f"自定义配置下载结果: {result}")
```

#### 3.2.4 错误处理和重试
```python
from utils.downloader import DownloadException, NetworkError, MergeError

async def robust_download_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    async def safe_download(bvid, max_retries=3):
        for attempt in range(max_retries):
            try:
                result = await downloader.download_video(bvid)
                return result
                
            except NetworkError as e:
                print(f"网络错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except MergeError as e:
                print(f"合并错误: {e}")
                # 合并错误通常不需要重试
                break
                
            except DownloadException as e:
                print(f"下载错误: {e}")
                break
                
        return {'success': False, 'error': '重试次数已用完'}
    
    # 使用安全下载方法
    result = await safe_download("BV1234567890")
    print(f"安全下载结果: {result}")
```

### 3.3 外部工具集成

#### 3.3.1 使用aria2c下载
```python
async def aria2_download_example():
    config = {
        "downloader": {
            "use_external_downloader": True,
            "external_downloader": "aria2c",
            "aria2_options": [
                "--max-connection-per-server=16",
                "--split=16",
                "--min-split-size=1M"
            ]
        }
    }
    
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    result = await downloader.download_video("BV1234567890")
    print(f"aria2下载结果: {result}")
```

#### 3.3.2 自定义FFmpeg参数
```python
async def custom_ffmpeg_example():
    config = {
        "downloader": {
            "ffmpeg_path": "/usr/local/bin/ffmpeg",
            "ffmpeg_options": [
                "-c:v", "copy",
                "-c:a", "copy",
                "-avoid_negative_ts", "make_zero"
            ]
        }
    }
    
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    result = await downloader.download_video("BV1234567890")
    print(f"自定义FFmpeg下载结果: {result}")
```

### 3.4 下载管理

#### 3.4.1 下载队列管理
```python
async def download_queue_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    # 添加到下载队列
    bvids = ["BV1234567890", "BV0987654321", "BV1111111111"]
    
    for bvid in bvids:
        await downloader.add_to_queue(bvid, quality=32)
    
    # 开始队列下载
    results = await downloader.process_queue()
    
    print(f"队列下载完成，成功: {len([r for r in results if r['success']])}")
```

#### 3.4.2 下载状态查询
```python
async def download_status_example():
    config = load_config()
    login = BiliLogin(config)
    credential = await login.login()
    
    downloader = BiliDownloader(credential, "downloads", config)
    
    # 开始下载（异步）
    download_task = asyncio.create_task(
        downloader.download_video("BV1234567890")
    )
    
    # 监控下载状态
    while not download_task.done():
        progress = await downloader.get_download_progress("BV1234567890")
        if progress:
            print(f"下载进度: {progress['percent']:.1f}%")
        
        await asyncio.sleep(1)
    
    result = await download_task
    print(f"下载完成: {result}")
```

## 4. 配置说明

### 4.1 下载配置项

```json
{
  "downloader": {
    "default_quality": 32,                  // 默认视频质量
    "concurrent_limit": 3,                  // 并发下载数量
    "chunk_size": 1048576,                  // 下载块大小(字节)
    "max_retries": 3,                       // 最大重试次数
    "retry_interval": 2,                    // 重试间隔(秒)
    "timeout": 30,                          // 请求超时(秒)
    "speed_limit": 0,                       // 速度限制(字节/秒，0为无限制)
    "use_external_downloader": false,       // 使用外部下载器
    "external_downloader": "aria2c",        // 外部下载器名称
    "ffmpeg_path": "ffmpeg",                // FFmpeg可执行文件路径
    "ffmpeg_options": [                     // FFmpeg参数
      "-c:v", "copy",
      "-c:a", "copy"
    ],
    "aria2_options": [                      // aria2参数
      "--max-connection-per-server=16",
      "--split=16"
    ],
    "user_agents": [                        // User-Agent列表
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ],
    "enable_proxy": false,                  // 启用代理
    "proxy_url": "http://127.0.0.1:8080",  // 代理URL
    "temp_dir": "temp",                     // 临时文件目录
    "keep_temp_files": false                // 保留临时文件
  }
}
```

### 4.2 视频质量代码

| 质量代码 | 分辨率 | 描述 |
|---------|--------|------|
| 16 | 360P | 流畅 |
| 32 | 480P | 清晰 |
| 64 | 720P | 高清 |
| 74 | 720P60 | 高清60帧 |
| 80 | 1080P | 超清 |
| 112 | 1080P+ | 超清+ |
| 116 | 1080P60 | 超清60帧 |

### 4.3 外部下载器配置

#### 4.3.1 aria2c配置
```json
{
  "external_downloader": "aria2c",
  "aria2_options": [
    "--max-connection-per-server=16",
    "--split=16",
    "--min-split-size=1M",
    "--max-download-limit=5M",
    "--continue=true",
    "--auto-file-renaming=false"
  ]
}
```

#### 4.3.2 wget配置
```json
{
  "external_downloader": "wget",
  "wget_options": [
    "--continue",
    "--timeout=30",
    "--tries=3",
    "--limit-rate=5m"
  ]
}
```

## 5. 数据格式

### 5.1 下载结果格式

```json
{
  "success": true,
  "bvid": "BV1234567890",
  "title": "视频标题",
  "output_path": "downloads/BV1234567890.mp4",
  "quality": 32,
  "file_size": 52428800,
  "duration": 120,
  "download_time": 45.6,
  "average_speed": 1048576,
  "metadata": {
    "video_codec": "avc1",
    "audio_codec": "mp4a",
    "resolution": "854x480",
    "fps": 25
  }
}
```

### 5.2 错误结果格式

```json
{
  "success": false,
  "bvid": "BV1234567890",
  "error": "网络连接超时",
  "error_code": "NETWORK_TIMEOUT",
  "retry_count": 3,
  "timestamp": 1640995200
}
```

### 5.3 进度信息格式

```json
{
  "bvid": "BV1234567890",
  "status": "downloading",
  "percent": 45.6,
  "downloaded_bytes": 23068672,
  "total_bytes": 52428800,
  "speed": 1048576,
  "eta": 28,
  "current_part": "video",
  "parts_completed": 0,
  "total_parts": 2
}
```

## 6. 依赖说明

### 6.1 必需依赖
- `bilibili-api-python`: B站API库
- `aiohttp`: HTTP客户端
- `aiofiles`: 异步文件操作
- `asyncio`: 异步编程支持

### 6.2 外部工具依赖
- **FFmpeg**: 音视频合并（必需）
- **aria2c**: 外部下载器（可选）
- **wget**: 外部下载器（可选）

### 6.3 安装命令
```bash
# Python依赖
pip install bilibili-api-python aiohttp aiofiles

# FFmpeg (Windows)
# 下载并配置到系统PATH

# aria2c (可选)
# Windows: 下载aria2并配置PATH
# Linux: sudo apt-get install aria2
# macOS: brew install aria2
```

## 7. 常见问题

### 7.1 下载相关
- **问题**: 下载速度慢
- **解决**: 使用外部下载器(aria2c)，增加并发连接数

### 7.2 合并相关
- **问题**: FFmpeg合并失败
- **解决**: 检查FFmpeg安装，确保PATH配置正确

### 7.3 存储相关
- **问题**: 磁盘空间不足
- **解决**: 清理临时文件，检查可用空间

### 7.4 网络相关
- **问题**: 下载中断
- **解决**: 启用断点续传，增加重试次数

---

**模块版本**: v1.0.0  
**最后更新**: 2025-01-20  
**维护者**: Claude 