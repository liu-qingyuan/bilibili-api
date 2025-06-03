# 视频过滤模块文档 (video_filter.py)

## 1. 模块简介

视频过滤模块提供视频内容过滤和清理服务，支持基于时长、质量等条件的视频筛选和批量删除功能。主要用于数据集清理和质量控制，确保数据集中的视频符合特定要求。

**主要用途：**
- 基于时长过滤视频文件
- **下载时智能过滤**：在下载前根据时长过滤视频 ⭐ **新功能**
- 批量删除不符合条件的视频
- 数据集质量控制和清理
- **同步和更新index.json索引文件**
- 生成过滤操作报告

## 2. 功能一览

### 2.1 核心功能

#### 2.1.1 时长过滤
- **时长检测**：从JSON元数据或视频文件直接获取时长信息
- **阈值过滤**：支持最大时长、最小时长等多种阈值设置
- **批量处理**：支持批量检测和过滤大量视频文件
- **智能检测**：优先从元数据获取时长，失败时回退到文件检测
- **下载前过滤**：在下载前检查时长，避免下载不需要的视频 ⭐ **新功能**

#### 2.1.2 文件管理
- **安全删除**：删除视频文件及其对应的JSON元数据文件
- **试运行模式**：预览删除操作而不实际执行
- **备份机制**：可选的文件备份功能
- **回滚支持**：支持删除操作的回滚

#### 2.1.3 索引文件管理 ⭐ **新功能**
- **索引同步**：自动从index.json中删除已删除视频的记录
- **统计更新**：自动更新索引文件中的统计信息
- **完整性维护**：确保索引文件与实际文件保持一致
- **批量更新**：支持批量更新索引记录

#### 2.1.4 质量控制
- **多维度过滤**：支持时长、文件大小、分辨率等多种过滤条件
- **质量评分**：基于多个指标计算视频质量分
- **异常检测**：检测损坏或异常的视频文件
- **重复检测**：检测和处理重复视频

#### 2.1.5 报告生成
- **详细报告**：生成包含过滤统计和文件列表的详细报告
- **操作日志**：记录所有过滤和删除操作
- **统计信息**：提供过滤前后的数据集统计对比
- **可视化输出**：支持表格和图表形式的报告输出

### 2.2 主要类和方法

#### 2.2.1 VideoFilter类
**初始化参数：**
- `metadata_dir`: JSON元数据目录路径
- `videos_dir`: 视频文件目录路径
- `config`: 配置字典，包含过滤相关配置

**主要方法：**
- `find_videos_by_duration(max_duration)`: 查找超出指定时长的视频
- `list_long_videos(max_duration)`: 列出超过指定时长的视频
- `delete_long_videos(max_duration, dry_run=False, generate_report=False)`: 删除超长视频
- `get_video_duration_from_metadata(json_file)`: 从JSON获取视频时长
- `get_video_duration_from_file(video_file)`: 从视频文件获取时长
- **`load_index()`**: 加载index.json文件 ⭐ **新方法**
- **`save_index(index_data)`**: 保存index.json文件 ⭐ **新方法**
- **`remove_from_index(bvids)`**: 从索引中删除指定视频记录 ⭐ **新方法**
- `generate_deletion_report(stats, output_file)`: 生成删除操作报告

## 3. 使用示例

### 3.1 基本使用

#### 3.1.1 下载时时长过滤 ⭐ **新功能**
```python
# 在main.py中使用命令行参数

# 启用下载时时长过滤，限制30秒
# python main.py --keywords "测试" --download --max-duration 30

# 自定义时长限制为60秒
# python main.py --keywords "测试" --download --max-duration 60

# 这将会：
# 1. 搜索关键词相关视频
# 2. 爬取视频信息
# 3. 检查视频时长
# 4. 如果超过时长限制，跳过下载但保存元数据
# 5. 如果在时长限制内，正常下载视频

# 功能说明：
# - 只要指定了 --max-duration 参数，就会自动启用下载时过滤
# - 如果不指定 --max-duration，则不进行时长过滤
# - 时长限制优先级：命令行参数 > 配置文件
```

#### 3.1.2 简单时长过滤
```python
from utils.video_filter import VideoFilter

def main():
    # 创建过滤器
    video_filter = VideoFilter(
        metadata_dir="data/json",
        videos_dir="data/videos"
    )
    
    # 列出超过30秒的视频
    long_videos = video_filter.list_long_videos(max_duration=30)
    
    print(f"找到 {len(long_videos)} 个超过30秒的视频:")
    for video in long_videos[:10]:  # 显示前10个
        print(f"- {video['bvid']}: {video['duration']}秒")

if __name__ == "__main__":
    main()
```

#### 3.1.3 删除超长视频（试运行）
```python
def dry_run_example():
    video_filter = VideoFilter("data/json", "data/videos")
    
    # 试运行删除操作
    result = video_filter.delete_long_videos(
        max_duration=30,
        dry_run=True,
        generate_report=True
    )
    
    print(f"试运行结果:")
    print(f"- 找到超长视频: {result['total_found']} 个")
    print(f"- 将删除视频文件: {result['deleted_videos']} 个")
    print(f"- 将删除JSON文件: {result['deleted_json']} 个")
    print(f"- 将释放空间: {result['total_size_freed'] / 1024 / 1024:.1f} MB")
    print(f"- 索引文件将更新: {'是' if result['index_updated'] else '否'}")
```

#### 3.1.4 实际删除操作 ⭐ **更新功能**
```python
def actual_delete_example():
    video_filter = VideoFilter("data/json", "data/videos")
    
    # 实际删除超过60秒的视频（包含索引更新）
    result = video_filter.delete_long_videos(
        max_duration=60,
        dry_run=False,
        generate_report=True
    )
    
    if result['index_updated']:
        print(f"删除完成:")
        print(f"- 删除视频文件: {result['deleted_videos']} 个")
        print(f"- 删除JSON文件: {result['deleted_json']} 个")
        print(f"- 释放空间: {result['total_size_freed'] / 1024 / 1024:.1f} MB")
        print(f"- 索引文件已同步更新")
        
        if result.get('report_path'):
            print(f"- 报告已保存到: {result['report_path']}")
    else:
        print(f"删除失败或索引更新失败")
        print(f"失败的删除操作: {result['failed_deletions']} 个")
```

### 3.2 索引文件管理 ⭐ **新功能**

#### 3.2.1 手动索引操作
```python
def manual_index_operations():
    video_filter = VideoFilter("data/json", "data/videos")
    
    # 加载当前索引
    index_data = video_filter.load_index()
    print(f"当前索引记录数: {len(index_data.get('videos', {}))}")
    
    # 手动删除特定视频的索引记录
    bvids_to_remove = ["BV1234567890", "BV0987654321"]
    success = video_filter.remove_from_index(bvids_to_remove)
    
    if success:
        print(f"成功从索引中删除 {len(bvids_to_remove)} 个记录")
    else:
        print("索引更新失败")
```

#### 3.2.2 检查索引一致性
```python
def check_index_consistency():
    video_filter = VideoFilter("data/json", "data/videos")
    
    # 获取索引中的所有视频
    index_data = video_filter.load_index()
    index_videos = set(index_data.get('videos', {}).keys())
    
    # 获取实际存在的视频文件
    actual_videos = set()
    for video_file in Path("data/videos").glob("*.mp4"):
        actual_videos.add(video_file.stem)
    
    # 找出不一致的记录
    orphan_in_index = index_videos - actual_videos
    missing_in_index = actual_videos - index_videos
    
    print(f"索引一致性检查:")
    print(f"- 索引记录数: {len(index_videos)}")
    print(f"- 实际视频数: {len(actual_videos)}")
    print(f"- 索引孤立记录: {len(orphan_in_index)}")
    print(f"- 缺失索引记录: {len(missing_in_index)}")
    
    # 清理索引中的孤立记录
    if orphan_in_index:
        success = video_filter.remove_from_index(list(orphan_in_index))
        if success:
            print(f"已清理 {len(orphan_in_index)} 个孤立索引记录")
```

### 3.3 命令行使用 ⭐ **新功能**

#### 3.3.1 下载时时长过滤 ⭐ **新功能**
```bash
# 启用下载时时长过滤，限制30秒
python main.py --keywords "测试关键词" --download --max-duration 30

# 自定义时长限制为60秒
python main.py --keywords "测试关键词" --download --max-duration 60

# 设置其他时长限制，比如120秒
python main.py --keywords "测试关键词" --download --max-duration 120

# 结合其他参数使用
python main.py --keywords "关键词1" "关键词2" --download --max-duration 45 --quality 64 --limit 100

# 仅爬取信息，不下载，但仍然过滤
python main.py --keywords "测试" --info-only --max-duration 30
```

**重要说明：**
- 只要指定了 `--max-duration` 参数，就会自动启用下载时过滤
- 超过时长限制的视频会跳过下载但仍保存元数据文件
- 如果不指定 `--max-duration`，则不进行时长过滤，下载所有视频

#### 3.3.2 删除超长视频并更新索引
```bash
# 删除超过30秒的视频，同时更新索引文件
python main.py --delete-long-videos --max-duration 30 --generate-report

# 试运行模式查看将要删除的视频
python main.py --delete-long-videos --max-duration 30 --dry-run

# 仅列出超长视频，不删除
python main.py --list-long-videos --max-duration 30
```

#### 3.3.3 生成删除报告
```bash
# 删除超长视频并生成详细报告
python main.py --delete-long-videos --max-duration 60 --generate-report

# 报告将包含以下信息：
# - 删除的文件列表
# - 释放的存储空间
# - 索引更新状态
# - 操作时间戳
```

## 4. 配置选项

### 4.1 基本配置
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

**配置说明：**
- `max_duration`: 默认时长限制（秒），当命令行未指定时使用
- `backup_before_delete`: 删除前是否备份文件
- `generate_reports`: 是否自动生成操作报告
- `update_index`: 是否自动更新索引文件

**时长限制优先级：**
1. **命令行参数** `--max-duration`（最高优先级）
2. **配置文件** `video_filter.max_duration`
3. **不过滤**（如果前两者都未设置，则不进行时长过滤）

### 4.2 索引配置 ⭐ **新配置**
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

## 5. 注意事项

### 5.1 下载时过滤 ⭐ **重要**
- **智能过滤**：在下载前检查视频时长，避免浪费带宽和时间
- **简单易用**：只需指定 `--max-duration` 参数即可启用过滤
- **灵活配置**：支持命令行参数和配置文件两种方式设置时长限制
- **元数据保留**：即使跳过下载，仍会保存视频的JSON元数据
- **日志记录**：会在日志中记录跳过的视频及其时长

### 5.2 索引文件处理 ⭐ **重要**
- **自动同步**：删除视频时会自动从index.json中删除对应记录
- **统计更新**：索引文件中的统计信息会自动更新
- **备份建议**：建议在大批量操作前备份index.json文件
- **一致性检查**：定期检查索引文件与实际文件的一致性

### 5.3 安全建议
- 重要操作前使用`--dry-run`参数预览
- 定期备份index.json和重要视频文件
- 监控删除操作的报告和日志
- 在生产环境中谨慎使用批量删除功能

### 5.4 性能考虑
- 下载时过滤可以显著节省带宽和存储空间
- 大量文件操作时建议分批处理
- 索引文件更新会有轻微性能开销
- 使用SSD存储可提高文件操作速度
- 定期清理日志文件以节省空间

## 6. 依赖说明

### 6.1 必需依赖
- `pathlib`: 路径操作
- `json`: JSON数据处理
- `datetime`: 日期时间处理
- `logging`: 日志记录

### 6.2 可选依赖
- `ffprobe`: 视频信息检测（FFmpeg套件）
- `matplotlib`: 统计图表生成
- `pandas`: 数据分析和处理

### 6.3 安装命令
```bash
# 基础依赖（Python标准库）
# 无需额外安装

# 可选依赖
pip install matplotlib pandas

# FFmpeg (包含ffprobe)
# Windows: 下载并配置到系统PATH
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
```

## 7. 常见问题

### 7.1 下载时过滤相关 ⭐ **新问题**
- **问题**: 启用过滤后没有下载任何视频
- **解决**: 检查max-duration设置是否过小，或搜索结果中的视频是否都超过时长限制

### 7.2 时长检测相关
- **问题**: 无法获取视频时长
- **解决**: 确保FFprobe已安装，或检查JSON元数据是否完整

### 7.3 删除操作相关
- **问题**: 删除操作失败
- **解决**: 检查文件权限，确保有写入权限

### 7.4 性能相关
- **问题**: 处理大量文件时速度慢
- **解决**: 启用并发处理，增加工作线程数

### 7.5 备份相关
- **问题**: 备份空间不足
- **解决**: 清理旧备份，或禁用备份功能

---

**模块版本**: v1.1.0  
**最后更新**: 2025-01-20  
**维护者**: Claude