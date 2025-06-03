# 数据集管理模块文档 (dataset_manager.py)

## 1. 模块简介

数据集管理模块提供哔哩哔哩视频数据集的统一管理服务，包括数据集创建、维护、版本控制和质量保证。支持多种数据格式的导出和数据集的完整性验证。

**主要用途：**
- 统一管理视频数据集
- 数据集版本控制和备份
- 数据质量保证和验证
- 多格式数据导出

## 2. 功能一览

### 2.1 核心功能

#### 2.1.1 数据集创建
- **自动创建**：基于爬取的数据自动创建数据集
- **结构化组织**：按照标准格式组织数据集结构
- **元数据生成**：自动生成数据集元数据和描述文件
- **索引构建**：构建数据集索引以便快速查询

#### 2.1.2 数据集维护
- **增量更新**：支持数据集的增量更新和扩展
- **数据清理**：自动清理无效或重复的数据
- **质量检查**：定期检查数据集的完整性和质量
- **统计更新**：实时更新数据集统计信息

#### 2.1.3 版本控制
- **版本管理**：支持数据集的版本控制和历史记录
- **变更追踪**：追踪数据集的变更历史
- **回滚支持**：支持回滚到历史版本
- **分支管理**：支持数据集的分支和合并

#### 2.1.4 数据导出
- **多格式支持**：支持JSON、CSV、Parquet等多种格式
- **自定义导出**：支持自定义字段和过滤条件的导出
- **批量导出**：支持大规模数据的批量导出
- **压缩打包**：支持导出数据的压缩和打包

### 2.2 主要类和方法

#### 2.2.1 DatasetManager类
**初始化参数：**
- `dataset_name`: 数据集名称
- `base_dir`: 数据集基础目录
- `config`: 配置字典，包含管理相关配置

**主要方法：**
- `create_dataset(metadata)`: 创建新数据集
- `load_dataset(version=None)`: 加载数据集
- `add_data(data_list)`: 添加数据到数据集
- `update_data(bvid, new_data)`: 更新数据集中的数据
- `remove_data(bvid_list)`: 从数据集中移除数据
- `validate_dataset()`: 验证数据集完整性
- `get_statistics()`: 获取数据集统计信息
- `export_dataset(format, output_path)`: 导出数据集
- `create_version(version_name)`: 创建数据集版本
- `list_versions()`: 列出所有版本

#### 2.2.2 辅助类
- `DatasetValidator`: 数据集验证器
- `DatasetExporter`: 数据集导出器
- `VersionManager`: 版本管理器
- `StatisticsCalculator`: 统计计算器

## 3. 使用示例

### 3.1 基本使用

#### 3.1.1 创建数据集
```python
from utils.dataset_manager import DatasetManager

def create_dataset_example():
    # 创建数据集管理器
    manager = DatasetManager(
        dataset_name="bilibili_sensitive_videos",
        base_dir="datasets"
    )
    
    # 定义数据集元数据
    metadata = {
        "name": "哔哩哔哩敏感视频数据集",
        "description": "包含敏感内容的哔哩哔哩视频数据集",
        "version": "1.0.0",
        "created_by": "bilibili_crawler",
        "keywords": ["bilibili", "video", "sensitive", "content"],
        "license": "MIT",
        "data_sources": ["bilibili.com"],
        "collection_period": {
            "start": "2025-01-01",
            "end": "2025-01-20"
        }
    }
    
    # 创建数据集
    result = manager.create_dataset(metadata)
    
    if result['success']:
        print(f"数据集创建成功:")
        print(f"- 数据集ID: {result['dataset_id']}")
        print(f"- 存储路径: {result['dataset_path']}")
        print(f"- 元数据文件: {result['metadata_file']}")
    else:
        print(f"数据集创建失败: {result['error']}")

if __name__ == "__main__":
    create_dataset_example()
```

#### 3.1.2 加载和查看数据集
```python
def load_dataset_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 加载数据集
    dataset = manager.load_dataset()
    
    if dataset:
        print("数据集信息:")
        print(f"- 名称: {dataset.metadata['name']}")
        print(f"- 版本: {dataset.metadata['version']}")
        print(f"- 数据量: {len(dataset.data)} 条")
        print(f"- 创建时间: {dataset.metadata['created_at']}")
        
        # 显示前几条数据
        print("\n前5条数据:")
        for i, item in enumerate(dataset.data[:5]):
            print(f"{i+1}. {item['title']} (BV{item['bvid']})")
    else:
        print("数据集加载失败")
```

#### 3.1.3 添加数据到数据集
```python
def add_data_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 准备要添加的数据
    new_data = [
        {
            "bvid": "BV1234567890",
            "title": "示例视频标题",
            "description": "视频描述",
            "duration": 120,
            "view_count": 10000,
            "like_count": 500,
            "upload_time": "2025-01-20",
            "uploader": {
                "name": "UP主名称",
                "uid": 123456789
            },
            "tags": ["标签1", "标签2"],
            "quality_score": 0.85
        }
    ]
    
    # 添加数据
    result = manager.add_data(new_data)
    
    if result['success']:
        print(f"数据添加成功:")
        print(f"- 添加数量: {result['added_count']}")
        print(f"- 跳过重复: {result['skipped_count']}")
        print(f"- 当前总量: {result['total_count']}")
    else:
        print(f"数据添加失败: {result['error']}")
```

### 3.2 数据集维护

#### 3.2.1 数据集验证
```python
def validate_dataset_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 验证数据集
    validation_result = manager.validate_dataset()
    
    print("数据集验证结果:")
    print(f"- 总数据量: {validation_result['total_records']}")
    print(f"- 有效记录: {validation_result['valid_records']}")
    print(f"- 无效记录: {validation_result['invalid_records']}")
    print(f"- 重复记录: {validation_result['duplicate_records']}")
    print(f"- 完整性: {validation_result['integrity_score']:.2%}")
    
    # 显示发现的问题
    if validation_result['issues']:
        print("\n发现的问题:")
        for issue in validation_result['issues'][:10]:
            print(f"- {issue['type']}: {issue['description']}")
            print(f"  影响记录: {issue['affected_records']}")
```

#### 3.2.2 数据清理
```python
def clean_dataset_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 执行数据清理
    cleaning_result = manager.clean_dataset(
        remove_duplicates=True,
        remove_invalid=True,
        update_statistics=True
    )
    
    print("数据清理结果:")
    print(f"- 清理前数量: {cleaning_result['before_count']}")
    print(f"- 清理后数量: {cleaning_result['after_count']}")
    print(f"- 移除重复: {cleaning_result['removed_duplicates']}")
    print(f"- 移除无效: {cleaning_result['removed_invalid']}")
    print(f"- 数据质量提升: {cleaning_result['quality_improvement']:.2%}")
```

#### 3.2.3 更新数据集统计
```python
def update_statistics_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 更新统计信息
    stats = manager.get_statistics(refresh=True)
    
    print("数据集统计信息:")
    print(f"基本信息:")
    print(f"  - 总视频数: {stats['basic']['total_videos']}")
    print(f"  - 总时长: {stats['basic']['total_duration']} 秒")
    print(f"  - 平均时长: {stats['basic']['avg_duration']:.1f} 秒")
    print(f"  - 总播放量: {stats['basic']['total_views']}")
    
    print(f"质量分布:")
    for quality_range, count in stats['quality_distribution'].items():
        print(f"  - {quality_range}: {count} 个视频")
    
    print(f"时长分布:")
    for duration_range, count in stats['duration_distribution'].items():
        print(f"  - {duration_range}: {count} 个视频")
    
    print(f"UP主统计:")
    print(f"  - 总UP主数: {stats['uploaders']['total_count']}")
    print(f"  - 平均每人视频数: {stats['uploaders']['avg_videos_per_uploader']:.1f}")
```

### 3.3 版本控制

#### 3.3.1 创建版本
```python
def create_version_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 创建新版本
    version_result = manager.create_version(
        version_name="v1.1.0",
        description="添加了新的敏感内容检测算法",
        changes=[
            "新增100个视频样本",
            "改进了质量评分算法",
            "修复了重复数据问题"
        ]
    )
    
    if version_result['success']:
        print(f"版本创建成功:")
        print(f"- 版本号: {version_result['version']}")
        print(f"- 版本ID: {version_result['version_id']}")
        print(f"- 创建时间: {version_result['created_at']}")
        print(f"- 数据快照: {version_result['snapshot_path']}")
    else:
        print(f"版本创建失败: {version_result['error']}")
```

#### 3.3.2 版本管理
```python
def version_management_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 列出所有版本
    versions = manager.list_versions()
    
    print("数据集版本历史:")
    for version in versions:
        print(f"- {version['version']} ({version['created_at']})")
        print(f"  描述: {version['description']}")
        print(f"  数据量: {version['record_count']}")
        print(f"  大小: {version['size'] / 1024 / 1024:.1f} MB")
        print()
    
    # 切换到特定版本
    if len(versions) > 1:
        target_version = versions[-2]['version']  # 切换到倒数第二个版本
        
        switch_result = manager.switch_version(target_version)
        if switch_result['success']:
            print(f"已切换到版本 {target_version}")
        else:
            print(f"版本切换失败: {switch_result['error']}")
```

#### 3.3.3 版本比较
```python
def version_comparison_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 比较两个版本
    comparison = manager.compare_versions("v1.0.0", "v1.1.0")
    
    print("版本比较结果:")
    print(f"版本 {comparison['version_a']} vs {comparison['version_b']}")
    print(f"- 新增记录: {comparison['added_records']}")
    print(f"- 删除记录: {comparison['removed_records']}")
    print(f"- 修改记录: {comparison['modified_records']}")
    print(f"- 数据量变化: {comparison['size_change']:+.1f} MB")
    
    # 显示具体变化
    if comparison['changes']:
        print("\n具体变化:")
        for change in comparison['changes'][:10]:
            print(f"- {change['type']}: {change['description']}")
```

### 3.4 数据导出

#### 3.4.1 基本导出
```python
def basic_export_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 导出为JSON格式
    json_result = manager.export_dataset(
        format="json",
        output_path="exports/dataset.json"
    )
    
    if json_result['success']:
        print(f"JSON导出成功:")
        print(f"- 文件路径: {json_result['output_path']}")
        print(f"- 文件大小: {json_result['file_size'] / 1024 / 1024:.1f} MB")
        print(f"- 记录数量: {json_result['record_count']}")
    
    # 导出为CSV格式
    csv_result = manager.export_dataset(
        format="csv",
        output_path="exports/dataset.csv",
        fields=["bvid", "title", "duration", "view_count", "like_count"]
    )
    
    if csv_result['success']:
        print(f"CSV导出成功:")
        print(f"- 文件路径: {csv_result['output_path']}")
        print(f"- 包含字段: {len(csv_result['fields'])} 个")
```

#### 3.4.2 条件导出
```python
def conditional_export_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 定义导出条件
    export_conditions = {
        "duration": {"min": 30, "max": 300},  # 时长30-300秒
        "view_count": {"min": 1000},          # 播放量大于1000
        "quality_score": {"min": 0.7},       # 质量分大于0.7
        "upload_date": {                      # 上传时间范围
            "start": "2025-01-01",
            "end": "2025-01-20"
        }
    }
    
    # 条件导出
    result = manager.export_dataset(
        format="json",
        output_path="exports/filtered_dataset.json",
        conditions=export_conditions
    )
    
    if result['success']:
        print(f"条件导出成功:")
        print(f"- 原始数据: {result['total_records']} 条")
        print(f"- 筛选后: {result['exported_records']} 条")
        print(f"- 筛选率: {result['filter_rate']:.2%}")
        print(f"- 文件大小: {result['file_size'] / 1024 / 1024:.1f} MB")
```

#### 3.4.3 批量导出
```python
def batch_export_example():
    manager = DatasetManager("bilibili_sensitive_videos", "datasets")
    
    # 定义多种导出格式
    export_configs = [
        {
            "format": "json",
            "output_path": "exports/full_dataset.json",
            "description": "完整数据集JSON格式"
        },
        {
            "format": "csv",
            "output_path": "exports/basic_info.csv",
            "fields": ["bvid", "title", "duration", "view_count"],
            "description": "基本信息CSV格式"
        },
        {
            "format": "parquet",
            "output_path": "exports/dataset.parquet",
            "compression": "snappy",
            "description": "Parquet格式（压缩）"
        }
    ]
    
    # 批量导出
    batch_result = manager.batch_export(export_configs)
    
    print("批量导出结果:")
    for i, result in enumerate(batch_result['results']):
        config = export_configs[i]
        if result['success']:
            print(f"✓ {config['description']}")
            print(f"  文件: {result['output_path']}")
            print(f"  大小: {result['file_size'] / 1024 / 1024:.1f} MB")
        else:
            print(f"✗ {config['description']}")
            print(f"  错误: {result['error']}")
        print()
    
    print(f"成功导出: {batch_result['success_count']}/{len(export_configs)}")
```

## 4. 配置说明

### 4.1 数据集配置项

```json
{
  "dataset_manager": {
    "default_format": "json",               // 默认数据格式
    "auto_backup": true,                    // 自动备份
    "backup_interval": 86400,               // 备份间隔(秒)
    "max_backups": 10,                      // 最大备份数量
    "compression": true,                    // 启用压缩
    "compression_algorithm": "gzip",        // 压缩算法
    "validation_on_load": true,             // 加载时验证
    "auto_index": true,                     // 自动建立索引
    "index_fields": ["bvid", "title"],      // 索引字段
    "cache_statistics": true,               // 缓存统计信息
    "statistics_refresh_interval": 3600     // 统计刷新间隔(秒)
  }
}
```

### 4.2 版本控制配置

```json
{
  "version_control": {
    "enable_versioning": true,              // 启用版本控制
    "auto_version": false,                  // 自动版本控制
    "version_naming": "semantic",           // 版本命名规则
    "max_versions": 50,                     // 最大版本数量
    "snapshot_compression": true,           // 快照压缩
    "delta_storage": true,                  // 增量存储
    "metadata_versioning": true             // 元数据版本控制
  }
}
```

### 4.3 导出配置

```json
{
  "export_settings": {
    "default_format": "json",               // 默认导出格式
    "supported_formats": [                  // 支持的格式
      "json", "csv", "parquet", "xlsx"
    ],
    "max_export_size": 1073741824,          // 最大导出大小(字节)
    "chunk_size": 10000,                    // 分块大小
    "include_metadata": true,               // 包含元数据
    "compress_exports": true,               // 压缩导出文件
    "export_validation": true               // 导出验证
  }
}
```

## 5. 数据格式

### 5.1 数据集元数据格式

```json
{
  "dataset_id": "bilibili_sensitive_videos_20250120",
  "name": "哔哩哔哩敏感视频数据集",
  "description": "包含敏感内容的哔哩哔哩视频数据集",
  "version": "1.0.0",
  "created_at": "2025-01-20T14:30:22Z",
  "updated_at": "2025-01-20T14:30:22Z",
  "created_by": "bilibili_crawler",
  "license": "MIT",
  "keywords": ["bilibili", "video", "sensitive"],
  "data_sources": ["bilibili.com"],
  "collection_period": {
    "start": "2025-01-01",
    "end": "2025-01-20"
  },
  "statistics": {
    "total_records": 363,
    "total_size": 19327352832,
    "avg_duration": 145.6,
    "quality_score_avg": 0.75
  },
  "schema": {
    "version": "1.0",
    "fields": [
      {
        "name": "bvid",
        "type": "string",
        "required": true,
        "description": "视频BV号"
      }
    ]
  }
}
```

### 5.2 版本信息格式

```json
{
  "version_id": "v1.1.0_20250120_143022",
  "version": "v1.1.0",
  "created_at": "2025-01-20T14:30:22Z",
  "description": "添加了新的敏感内容检测算法",
  "changes": [
    "新增100个视频样本",
    "改进了质量评分算法",
    "修复了重复数据问题"
  ],
  "statistics": {
    "record_count": 463,
    "size": 25327352832,
    "changes_from_previous": {
      "added": 100,
      "removed": 0,
      "modified": 15
    }
  },
  "snapshot_path": "snapshots/v1.1.0_20250120_143022.gz",
  "parent_version": "v1.0.0",
  "checksum": "sha256:abc123..."
}
```

## 6. 依赖说明

### 6.1 必需依赖
- `json`: JSON数据处理
- `pathlib`: 路径操作
- `datetime`: 日期时间处理
- `hashlib`: 数据校验

### 6.2 可选依赖
- `pandas`: 数据分析和CSV导出
- `pyarrow`: Parquet格式支持
- `openpyxl`: Excel格式支持

### 6.3 安装命令
```bash
# 基础依赖（Python标准库）
# 无需额外安装

# 可选依赖
pip install pandas pyarrow openpyxl
```

## 7. 常见问题

### 7.1 数据集相关
- **问题**: 数据集加载失败
- **解决**: 检查数据集路径和权限

### 7.2 版本控制相关
- **问题**: 版本创建失败
- **解决**: 检查磁盘空间和写入权限

### 7.3 导出相关
- **问题**: 大数据集导出超时
- **解决**: 使用分块导出或增加超时时间

---

**模块版本**: v1.0.0  
**最后更新**: 2025-01-20  
**维护者**: Claude 