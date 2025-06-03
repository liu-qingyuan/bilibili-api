# 文件分析模块文档 (file_analyzer.py)

## 1. 模块简介

文件分析模块提供视频文件和JSON元数据文件的匹配分析服务，用于检测文件完整性、识别孤立文件和维护数据集的一致性。支持批量分析、文件清理、**索引文件同步**和详细报告生成。

**主要用途：**
- 分析视频文件与JSON元数据的匹配关系
- 检测和处理孤立文件
- 维护数据集文件完整性
- **同步和维护index.json索引文件**
- 生成文件分析报告

## 2. 功能一览

### 2.1 核心功能

#### 2.1.1 文件匹配分析
- **配对检测**：检测视频文件与对应JSON元数据文件的匹配关系
- **完整性验证**：验证文件对的完整性和有效性
- **批量分析**：支持大规模文件集的批量分析
- **智能匹配**：基于文件名模式的智能匹配算法

#### 2.1.2 孤立文件检测
- **孤立视频检测**：识别没有对应JSON文件的视频文件
- **孤立JSON检测**：识别没有对应视频文件的JSON文件
- **损坏文件检测**：检测损坏或无效的文件
- **重复文件检测**：识别重复或冗余的文件

#### 2.1.3 索引文件管理 ⭐ **新功能**
- **索引匹配分析**：检查index.json与实际文件的匹配情况
- **孤立记录检测**：识别索引中存在但文件不存在的记录
- **索引同步**：自动清理索引中的孤立记录
- **统计更新**：自动更新索引文件中的统计信息
- **完整性维护**：确保索引文件与实际文件保持一致

#### 2.1.4 文件清理
- **安全删除**：安全删除孤立或无效文件
- **批量清理**：批量清理多种类型的问题文件
- **索引同步清理**：清理文件时同步更新索引
- **备份机制**：删除前自动备份重要文件
- **回滚支持**：支持清理操作的撤销和回滚

#### 2.1.5 统计分析
- **文件统计**：提供详细的文件数量和大小统计
- **匹配率分析**：计算文件匹配率和完整性指标
- **索引匹配率**：计算索引文件的匹配率和一致性
- **分布分析**：分析文件大小、类型等分布情况
- **趋势分析**：跟踪文件变化趋势

### 2.2 主要类和方法

#### 2.2.1 FileAnalyzer类
**初始化参数：**
- `metadata_dir`: JSON元数据目录路径
- `videos_dir`: 视频文件目录路径

**主要方法：**
- `analyze_file_matching(check_index=True)`: 分析文件匹配关系
- `get_video_files()`: 获取所有视频文件的BV号集合
- `get_json_files()`: 获取所有JSON文件的BV号集合
- **`get_index_videos()`**: 获取索引中记录的所有视频BV号 ⭐ **新方法**
- **`load_index()`**: 加载index.json文件 ⭐ **新方法**
- **`save_index(index_data)`**: 保存index.json文件 ⭐ **新方法**
- **`sync_index_with_files(dry_run=True)`**: 同步索引文件与实际文件 ⭐ **新方法**
- `clean_orphan_files(clean_videos, clean_jsons, update_index, dry_run)`: 清理孤立文件
- `save_analysis_report(output_path)`: 保存分析报告到文件

## 3. 使用示例

### 3.1 基本使用

#### 3.1.1 基本文件分析 ⭐ **更新功能**
```python
from utils.file_analyzer import FileAnalyzer

def main():
    # 创建分析器
    analyzer = FileAnalyzer(
        metadata_dir="data/json",
        videos_dir="data/videos"
    )
    
    # 执行文件匹配分析（包含索引检查）
    analysis_result = analyzer.analyze_file_matching(check_index=True)
    
    print("文件分析结果:")
    print(f"- 视频文件总数: {analysis_result['total_videos']}")
    print(f"- JSON文件总数: {analysis_result['total_jsons']}")
    print(f"- 匹配文件对: {analysis_result['matched_pairs']}")
    print(f"- 孤立视频文件: {analysis_result['orphan_video_count']}")
    print(f"- 孤立JSON文件: {analysis_result['orphan_json_count']}")
    
    # 索引文件分析结果
    print(f"- 索引记录总数: {analysis_result['index_total']}")
    print(f"- 索引孤立记录: {analysis_result['index_orphan_count']}")
    print(f"- 缺失索引记录: {analysis_result['missing_from_index_count']}")
    print(f"- 索引匹配率: {analysis_result['index_match_rate']:.1f}%")

if __name__ == "__main__":
    main()
```

#### 3.1.2 查找孤立文件
```python
def find_orphans_example():
    analyzer = FileAnalyzer("data/json", "data/videos")
    
    # 分析文件匹配情况
    result = analyzer.analyze_file_matching(check_index=True)
    
    # 显示孤立视频文件
    if result['orphan_videos']:
        print(f"发现 {len(result['orphan_videos'])} 个孤立视频文件:")
        for bvid in result['orphan_videos'][:10]:  # 显示前10个
            print(f"- {bvid}.mp4")
    
    # 显示孤立JSON文件
    if result['orphan_jsons']:
        print(f"发现 {len(result['orphan_jsons'])} 个孤立JSON文件:")
        for bvid in result['orphan_jsons'][:10]:  # 显示前10个
            print(f"- {bvid}.json")
    
    # 显示索引孤立记录
    if result['index_orphans']:
        print(f"发现 {len(result['index_orphans'])} 个索引孤立记录:")
        for bvid in result['index_orphans'][:10]:  # 显示前10个
            print(f"- {bvid} (索引中有记录但文件不存在)")
```

### 3.2 索引文件管理 ⭐ **新功能**

#### 3.2.1 检查索引完整性
```python
def check_index_integrity():
    analyzer = FileAnalyzer("data/json", "data/videos")
    
    # 分析索引文件完整性
    result = analyzer.analyze_file_matching(check_index=True)
    
    print("索引完整性检查:")
    print(f"- 索引记录数: {result['index_total']}")
    print(f"- 实际文件数: {result['matched_pairs']}")
    print(f"- 索引匹配率: {result['index_match_rate']:.1f}%")
    
    if result['index_orphan_count'] > 0:
        print(f"⚠️  发现 {result['index_orphan_count']} 个孤立索引记录")
        print("建议运行索引同步来清理这些记录")
    
    if result['missing_from_index_count'] > 0:
        print(f"⚠️  发现 {result['missing_from_index_count']} 个文件缺失索引记录")
        print("这些文件存在但未在索引中记录")
```

#### 3.2.2 同步索引文件
```python
def sync_index_example():
    analyzer = FileAnalyzer("data/json", "data/videos")
    
    # 试运行同步操作
    sync_result = analyzer.sync_index_with_files(dry_run=True)
    
    print("索引同步预览:")
    print(f"- 原始记录数: {sync_result['kept_in_index'] + sync_result['removed_count']}")
    print(f"- 将删除记录: {sync_result['removed_count']}")
    print(f"- 将保留记录: {sync_result['kept_in_index']}")
    
    # 确认后执行实际同步
    if sync_result['removed_count'] > 0:
        confirm = input("是否执行索引同步? (y/n): ")
        if confirm.lower() == 'y':
            actual_result = analyzer.sync_index_with_files(dry_run=False)
            if actual_result['success']:
                print(f"✅ 索引同步完成，删除了 {actual_result['removed_count']} 个孤立记录")
            else:
                print("❌ 索引同步失败")
```

#### 3.2.3 手动索引操作
```python
def manual_index_operations():
    analyzer = FileAnalyzer("data/json", "data/videos")
    
    # 加载当前索引
    index_data = analyzer.load_index()
    print(f"当前索引状态:")
    print(f"- 记录数: {len(index_data.get('videos', {}))}")
    print(f"- 最后更新: {index_data.get('stats', {}).get('last_updated', 'Unknown')}")
    
    # 获取索引中的视频列表
    index_videos = analyzer.get_index_videos()
    print(f"- 索引中的视频数: {len(index_videos)}")
    
    # 检查特定视频是否在索引中
    test_bvid = "BV1234567890"
    if test_bvid in index_videos:
        print(f"✅ {test_bvid} 在索引中")
    else:
        print(f"❌ {test_bvid} 不在索引中")
```

### 3.3 文件清理

#### 3.3.1 清理孤立文件（试运行）
```python
def clean_orphans_dry_run():
    analyzer = FileAnalyzer("data/json", "data/videos")
    
    # 试运行清理孤立文件（包含索引更新）
    result = analyzer.clean_orphan_files(
        clean_videos=True,
        clean_jsons=True,
        update_index=True,
        dry_run=True
    )
    
    print("孤立文件清理预览:")
    print(f"- 将清理视频文件: {result['cleaned_video_count']} 个")
    print(f"- 将清理JSON文件: {result['cleaned_json_count']} 个")
    print(f"- 索引文件将同步: {'是' if result['index_synced'] else '否'}")
```

#### 3.3.2 实际清理操作 ⭐ **更新功能**
```python
def actual_clean_example():
    analyzer = FileAnalyzer("data/json", "data/videos")
    
    # 实际清理孤立文件并同步索引
    result = analyzer.clean_orphan_files(
        clean_videos=True,
        clean_jsons=True,
        update_index=True,
        dry_run=False
    )
    
    if result['cleaned_video_count'] > 0 or result['cleaned_json_count'] > 0:
        print(f"清理完成:")
        print(f"- 清理视频文件: {result['cleaned_video_count']} 个")
        print(f"- 清理JSON文件: {result['cleaned_json_count']} 个")
        print(f"- 索引文件同步: {'成功' if result['index_synced'] else '失败'}")
    else:
        print("没有找到需要清理的孤立文件")
```

### 3.4 命令行使用 ⭐ **新功能**

#### 3.4.1 检查索引完整性
```bash
# 检查索引文件的完整性和匹配情况
python main.py --check-index

# 输出示例：
# - 视频文件总数: 361
# - JSON文件总数: 361
# - 匹配的文件对: 361
# - 索引记录总数: 1000
# - 索引孤立记录: 639 个
# - 索引匹配率: 36.1%
```

#### 3.4.2 同步索引文件
```bash
# 试运行索引同步
python main.py --sync-index --dry-run

# 实际执行索引同步
python main.py --sync-index

# 输出示例：
# - 原始记录数: 1000 个
# - 删除孤立记录: 639 个
# - 保留有效记录: 361 个
# - 同步状态: 成功
```

#### 3.4.3 分析文件匹配情况
```bash
# 分析文件匹配情况（包含索引检查）
python main.py --analyze-files

# 清理孤立文件并同步索引
python main.py --clean-orphan-videos --clean-orphan-jsons --update-index

# 试运行清理操作
python main.py --clean-orphan-videos --clean-orphan-jsons --update-index --dry-run
```

#### 3.4.4 生成分析报告
```bash
# 生成详细的文件分析报告
python main.py --save-analysis-report

# 报告将包含：
# - 文件匹配统计
# - 索引一致性分析
# - 孤立文件列表
# - 建议的清理操作
```

## 4. 配置选项

### 4.1 基本配置
```json
{
    "file_analyzer": {
        "check_index_by_default": true,
        "auto_backup_before_clean": true,
        "generate_reports": true,
        "max_orphan_display": 10
    }
}
```

### 4.2 索引配置 ⭐ **新配置**
```json
{
    "index": {
        "auto_sync_on_clean": true,
        "backup_before_sync": true,
        "validate_on_load": true,
        "update_stats_on_save": true
    }
}
```

## 5. 数据格式

### 5.1 分析结果格式 ⭐ **更新格式**
```json
{
    "total_videos": 361,
    "total_jsons": 361,
    "matched_pairs": 361,
    "orphan_videos": [],
    "orphan_jsons": [],
    "orphan_video_count": 0,
    "orphan_json_count": 0,
    "index_total": 1000,
    "index_orphans": ["BV1234567890", "BV0987654321"],
    "index_orphan_count": 639,
    "missing_from_index": [],
    "missing_from_index_count": 0,
    "index_match_rate": 36.1,
    "analysis_time": "2025-01-20T14:30:22"
}
```

### 5.2 索引同步结果格式 ⭐ **新格式**
```json
{
    "removed_from_index": ["BV1234567890", "BV0987654321"],
    "removed_count": 639,
    "kept_in_index": 361,
    "sync_time": "2025-01-20T14:30:22",
    "dry_run": false,
    "success": true
}
```

### 5.3 清理结果格式 ⭐ **更新格式**
```json
{
    "cleaned_videos": [],
    "cleaned_jsons": [],
    "cleaned_video_count": 0,
    "cleaned_json_count": 0,
    "dry_run": false,
    "clean_time": "2025-01-20T14:30:22",
    "index_synced": true
}
```

## 6. 注意事项

### 6.1 索引文件处理 ⭐ **重要**
- **自动检查**：默认情况下会检查索引文件的一致性
- **同步建议**：发现索引孤立记录时建议及时同步
- **备份重要性**：索引同步前建议备份index.json文件
- **批量操作**：大量索引更新时建议分批处理

### 6.2 安全建议
- 重要操作前使用`--dry-run`参数预览
- 定期检查文件和索引的一致性
- 监控清理操作的结果和日志
- 在生产环境中谨慎使用批量清理功能

### 6.3 性能考虑
- 索引文件检查会增加分析时间
- 大型索引文件的同步操作可能较慢
- 建议在低峰期执行大批量同步操作
- 定期清理日志文件以节省空间

### 6.4 故障排除
- **索引匹配率低**：运行`--sync-index`同步索引文件
- **孤立记录过多**：检查是否有批量删除操作未同步索引
- **索引文件损坏**：从备份恢复或重新生成索引文件
- **同步失败**：检查文件权限和磁盘空间

---

**模块版本**: v1.0.0  
**最后更新**: 2025-01-20  
**维护者**: Claude 