#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集管理模块

用于管理哔哩哔哩视频数据集，包括数据索引、元数据管理、
增量更新和统计功能。支持数据集完整性检查和统计报告生成。

作者: Claude
日期: 2025-05-22
"""

import os
import sys
import json
import logging
import time
import asyncio
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re

# 添加父目录到系统路径，以便导入bilibili_api库
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 导入bilibili_api库
from bilibili_api import video, sync
from bilibili_api.utils.network import Credential


class DatasetManager:
    """数据集管理类"""
    
    def __init__(self, json_dir: str, video_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据集管理器
        
        Args:
            json_dir: JSON数据存储目录
            video_dir: 视频存储目录
            config: 数据集配置，如果不提供则使用默认配置
        """
        self.json_dir = json_dir
        self.video_dir = video_dir
        self.logger = logging.getLogger("bili_crawler.dataset")
        
        # 确保目录存在
        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)
        
        # 默认配置
        self.config = {
            "index_file": os.path.join(json_dir, "index.json"),
            "json_filename_format": "{bvid}.json",
            "index_fields": ["bvid", "title", "duration", "pubdate", "owner_name", "view", "like", "tags"],
            "update_index_on_save": True,
        }
        
        # 更新配置
        if config and isinstance(config, dict):
            for key, value in config.items():
                if key in self.config:
                    self.config[key] = value
    
    def save_video_info(self, video_info: Dict[str, Any]) -> str:
        """
        保存视频信息到JSON文件
        
        Args:
            video_info: 视频信息字典
            
        Returns:
            str: 保存的文件路径
        """
        # 获取视频BV号
        bvid = video_info.get("basic_info", {}).get("bvid")
        if not bvid:
            raise ValueError("视频信息缺少BV号")
        
        # 格式化文件名
        filename = self.config["json_filename_format"].format(bvid=bvid)
        file_path = os.path.join(self.json_dir, filename)
        
        try:
            # 保存JSON文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(video_info, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"视频信息已保存到: {file_path}")
            
            # 更新索引
            if self.config["update_index_on_save"]:
                self.update_index(video_info)
            
            return file_path
            
        except Exception as e:
            self.logger.error(f"保存视频信息失败: {str(e)}")
            raise
    
    def load_video_info(self, bvid: str) -> Optional[Dict[str, Any]]:
        """
        从JSON文件加载视频信息
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Optional[Dict[str, Any]]: 视频信息字典，如果文件不存在则返回None
        """
        # 格式化文件名
        filename = self.config["json_filename_format"].format(bvid=bvid)
        file_path = os.path.join(self.json_dir, filename)
        
        if not os.path.exists(file_path):
            self.logger.warning(f"视频信息文件不存在: {file_path}")
            return None
        
        try:
            # 加载JSON文件
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"加载视频信息失败: {str(e)}")
            return None
    
    def get_video_path(self, bvid: str) -> Optional[str]:
        """
        获取视频文件路径
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Optional[str]: 视频文件路径，如果文件不存在则返回None
        """
        # 获取视频信息
        video_info = self.load_video_info(bvid)
        if not video_info:
            return None
        
        # 获取视频标题
        title = video_info.get("basic_info", {}).get("title", "")
        
        # 可能的文件名格式
        possible_filenames = [
            f"{bvid}_{title}.mp4",
            f"{bvid}.mp4",
        ]
        
        # 清理文件名中的非法字符
        for i, filename in enumerate(possible_filenames):
            possible_filenames[i] = self._sanitize_filename(filename)
        
        # 查找视频文件
        for filename in possible_filenames:
            file_path = os.path.join(self.video_dir, filename)
            if os.path.exists(file_path):
                return file_path
        
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # 替换Windows文件名中的非法字符
        illegal_chars = r'[\\/*?:"<>|]'
        sanitized = re.sub(illegal_chars, "_", filename)
        
        # 限制文件名长度
        if len(sanitized) > 200:
            sanitized = sanitized[:197] + "..."
            
        return sanitized
    
    def update_index(self, video_info: Dict[str, Any]) -> None:
        """
        更新索引文件
        
        Args:
            video_info: 要添加到索引的视频信息
        """
        try:
            # 加载现有索引
            index_data = self.load_index()
            
            # 提取索引所需字段
            basic_info = video_info.get("basic_info", {})
            owner = video_info.get("owner", {})
            stat = video_info.get("stat", {})
            
            # 构建索引记录
            index_record = {
                "bvid": basic_info.get("bvid", ""),
                "title": basic_info.get("title", ""),
                "duration": basic_info.get("duration", 0),
                "pubdate": basic_info.get("pubdate", 0),
                "owner_name": owner.get("name", ""),
                "view": stat.get("view", 0),
                "like": stat.get("like", 0),
                "tags": [tag.get("tag_name", "") for tag in video_info.get("tags", [])],
                "indexed_at": int(time.time()),
            }
            
            # 更新索引
            bvid = index_record["bvid"]
            index_data["videos"][bvid] = index_record
            index_data["stats"]["total_videos"] = len(index_data["videos"])
            index_data["stats"]["last_updated"] = int(time.time())
            
            # 保存索引
            self._save_index(index_data)
            
        except Exception as e:
            self.logger.error(f"更新索引失败: {str(e)}")
    
    def load_index(self) -> Dict[str, Any]:
        """
        加载索引文件
        
        Returns:
            Dict[str, Any]: 索引数据
        """
        index_file = self.config["index_file"]
        
        # 检查索引文件是否存在
        if not os.path.exists(index_file):
            # 创建空索引
            return {
                "metadata": {
                    "dataset_name": "Bilibili Sensitive Videos Dataset",
                    "created_at": int(time.time()),
                },
                "stats": {
                    "total_videos": 0,
                    "last_updated": int(time.time()),
                },
                "videos": {},
            }
        
        try:
            # 加载索引文件
            with open(index_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"加载索引失败: {str(e)}")
            # 返回空索引
            return {
                "metadata": {
                    "dataset_name": "Bilibili Sensitive Videos Dataset",
                    "created_at": int(time.time()),
                },
                "stats": {
                    "total_videos": 0,
                    "last_updated": int(time.time()),
                },
                "videos": {},
            }
    
    def _save_index(self, index_data: Dict[str, Any]) -> None:
        """
        保存索引文件
        
        Args:
            index_data: 索引数据
        """
        index_file = self.config["index_file"]
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(index_file), exist_ok=True)
            
            # 保存索引文件
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=4)
                
            self.logger.info(f"索引已更新: {index_file}")
            
        except Exception as e:
            self.logger.error(f"保存索引失败: {str(e)}")
    
    def generate_index(self) -> Dict[str, Any]:
        """
        生成完整索引
        
        Returns:
            Dict[str, Any]: 索引数据
        """
        self.logger.info("开始生成数据集索引...")
        
        # 创建新索引
        index_data = {
            "metadata": {
                "dataset_name": "Bilibili Sensitive Videos Dataset",
                "created_at": int(time.time()),
            },
            "stats": {
                "total_videos": 0,
                "total_duration": 0,  # 总时长(秒)
                "total_view": 0,  # 总播放量
                "total_like": 0,  # 总点赞数
                "last_updated": int(time.time()),
            },
            "videos": {},
        }
        
        # 遍历JSON文件目录
        processed = 0
        
        for filename in os.listdir(self.json_dir):
            if not filename.endswith(".json") or filename == "index.json":
                continue
                
            try:
                # 加载视频信息
                filepath = os.path.join(self.json_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    video_info = json.load(f)
                
                # 提取索引所需字段
                basic_info = video_info.get("basic_info", {})
                owner = video_info.get("owner", {})
                stat = video_info.get("stat", {})
                
                bvid = basic_info.get("bvid", "")
                
                # 构建索引记录
                index_record = {
                    "bvid": bvid,
                    "title": basic_info.get("title", ""),
                    "duration": basic_info.get("duration", 0),
                    "pubdate": basic_info.get("pubdate", 0),
                    "owner_name": owner.get("name", ""),
                    "view": stat.get("view", 0),
                    "like": stat.get("like", 0),
                    "tags": [tag.get("tag_name", "") for tag in video_info.get("tags", [])],
                    "indexed_at": int(time.time()),
                }
                
                # 检查视频文件是否存在
                video_path = self.get_video_path(bvid)
                index_record["has_video"] = video_path is not None
                
                # 更新索引
                index_data["videos"][bvid] = index_record
                
                # 更新统计数据
                index_data["stats"]["total_videos"] += 1
                index_data["stats"]["total_duration"] += index_record["duration"]
                index_data["stats"]["total_view"] += index_record["view"]
                index_data["stats"]["total_like"] += index_record["like"]
                
                processed += 1
                
            except Exception as e:
                self.logger.error(f"处理文件 {filename} 时出错: {str(e)}")
        
        # 保存索引
        self._save_index(index_data)
        
        self.logger.info(f"索引生成完成，共处理 {processed} 个视频")
        return index_data
    
    def check_dataset_integrity(self) -> Dict[str, Any]:
        """
        检查数据集完整性
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        self.logger.info("开始检查数据集完整性...")
        
        # 加载索引
        index_data = self.load_index()
        
        # 统计信息
        result = {
            "total_videos": len(index_data["videos"]),
            "videos_with_json": 0,
            "videos_with_file": 0,
            "missing_json": [],
            "missing_video": [],
        }
        
        # 检查每个视频
        for bvid, info in index_data["videos"].items():
            # 检查JSON文件
            json_path = os.path.join(self.json_dir, f"{bvid}.json")
            if os.path.exists(json_path):
                result["videos_with_json"] += 1
            else:
                result["missing_json"].append(bvid)
            
            # 检查视频文件
            video_path = self.get_video_path(bvid)
            if video_path:
                result["videos_with_file"] += 1
            else:
                result["missing_video"].append(bvid)
        
        self.logger.info(f"完整性检查完成，共 {result['total_videos']} 个视频，"
                         f"{result['videos_with_json']} 个JSON文件，"
                         f"{result['videos_with_file']} 个视频文件")
        
        return result
    
    def incremental_update(self, new_videos_dir: str, force_update: bool = False) -> Dict[str, Any]:
        """
        增量更新数据集
        
        Args:
            new_videos_dir: 新视频的存储目录
            force_update: 是否强制更新已存在的视频
            
        Returns:
            Dict[str, Any]: 更新结果统计
        """
        self.logger.info(f"开始增量更新数据集，源目录: {new_videos_dir}")
        
        if not os.path.exists(new_videos_dir):
            self.logger.error(f"新视频目录不存在: {new_videos_dir}")
            return {"error": f"新视频目录不存在: {new_videos_dir}"}
        
        # 加载索引
        index_data = self.load_index()
        existing_bvids = set(index_data["videos"].keys())
        
        # 统计信息
        stats = {
            "total_processed": 0,
            "added_json": 0,
            "added_videos": 0,
            "updated_json": 0,
            "skipped": 0,
            "errors": []
        }
        
        # 处理JSON文件
        json_dir = os.path.join(new_videos_dir, "json")
        if os.path.exists(json_dir):
            for filename in os.listdir(json_dir):
                if not filename.endswith(".json"):
                    continue
                
                try:
                    # 提取BV号
                    bvid = filename.replace(".json", "")
                    stats["total_processed"] += 1
                    
                    # 检查是否已存在
                    exists = bvid in existing_bvids
                    
                    if exists and not force_update:
                        self.logger.debug(f"跳过已存在的视频信息: {bvid}")
                        stats["skipped"] += 1
                        continue
                    
                    # 拷贝JSON文件
                    src_path = os.path.join(json_dir, filename)
                    dst_path = os.path.join(self.json_dir, filename)
                    
                    with open(src_path, "r", encoding="utf-8") as src_file:
                        video_info = json.load(src_file)
                        
                    # 保存JSON并更新索引
                    self.save_video_info(video_info)
                    
                    if exists:
                        stats["updated_json"] += 1
                        self.logger.info(f"更新视频信息: {bvid}")
                    else:
                        stats["added_json"] += 1
                        existing_bvids.add(bvid)
                        self.logger.info(f"添加新视频信息: {bvid}")
                    
                except Exception as e:
                    self.logger.error(f"处理JSON文件 {filename} 时出错: {str(e)}")
                    stats["errors"].append({
                        "file": filename,
                        "error": str(e)
                    })
        
        # 处理视频文件
        videos_dir = os.path.join(new_videos_dir, "videos")
        if os.path.exists(videos_dir):
            for filename in os.listdir(videos_dir):
                if not filename.endswith((".mp4", ".flv", ".mkv")):
                    continue
                
                try:
                    # 尝试从文件名中提取BV号
                    match = re.search(r"(BV[a-zA-Z0-9]{10})", filename)
                    if not match:
                        self.logger.warning(f"无法从文件名中提取BV号: {filename}")
                        continue
                    
                    bvid = match.group(1)
                    
                    # 检查对应的JSON信息是否存在
                    json_path = os.path.join(self.json_dir, f"{bvid}.json")
                    if not os.path.exists(json_path) and not os.path.exists(os.path.join(json_dir, f"{bvid}.json")):
                        self.logger.warning(f"视频没有对应的JSON信息: {filename}")
                        continue
                    
                    # 检查是否已存在视频文件
                    existing_video_path = self.get_video_path(bvid)
                    if existing_video_path and not force_update:
                        self.logger.debug(f"跳过已存在的视频文件: {bvid}")
                        continue
                    
                    # 拷贝视频文件
                    src_path = os.path.join(videos_dir, filename)
                    dst_path = os.path.join(self.video_dir, filename)
                    
                    # 如果目标目录不同，则拷贝文件
                    if src_path != dst_path:
                        import shutil
                        shutil.copy2(src_path, dst_path)
                        self.logger.info(f"拷贝视频文件: {filename}")
                        stats["added_videos"] += 1
                    
                except Exception as e:
                    self.logger.error(f"处理视频文件 {filename} 时出错: {str(e)}")
                    stats["errors"].append({
                        "file": filename,
                        "error": str(e)
                    })
        
        # 重新生成索引
        self.generate_index()
        
        self.logger.info(f"增量更新完成，处理 {stats['total_processed']} 个文件，"
                         f"添加 {stats['added_json']} 个JSON，"
                         f"添加 {stats['added_videos']} 个视频，"
                         f"更新 {stats['updated_json']} 个JSON，"
                         f"跳过 {stats['skipped']} 个已存在文件")
        
        return stats
    
    def search_videos(self, keyword: str, search_in: List[str] = None) -> List[str]:
        """
        搜索视频
        
        Args:
            keyword: 搜索关键词
            search_in: 要搜索的字段列表，默认为["title", "tags"]
            
        Returns:
            List[str]: 匹配的视频BV号列表
        """
        if search_in is None:
            search_in = ["title", "tags"]
            
        results = []
        
        # 加载索引
        index_data = self.load_index()
        
        # 搜索每个视频
        for bvid, info in index_data["videos"].items():
            # 搜索标题
            if "title" in search_in and keyword.lower() in info.get("title", "").lower():
                results.append(bvid)
                continue
                
            # 搜索标签
            if "tags" in search_in:
                for tag in info.get("tags", []):
                    if keyword.lower() in tag.lower():
                        results.append(bvid)
                        break
        
        return results
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """
        获取数据集统计信息
        
        Returns:
            Dict[str, Any]: 数据集统计信息
        """
        self.logger.info("获取数据集统计信息...")
        
        # 加载索引
        index_data = self.load_index()
        videos = index_data["videos"]
        
        # 基本统计
        stats = {
            "total_videos": len(videos),
            "total_duration_seconds": sum(info.get("duration", 0) for info in videos.values()),
            "total_views": sum(info.get("view", 0) for info in videos.values()),
            "total_likes": sum(info.get("like", 0) for info in videos.values()),
            "video_with_files": 0,
            "videos_by_pubdate": {},
            "top_tags": {},
            "top_uploaders": {},
            "videos_by_duration": {
                "0-60s": 0,       # 1分钟以内
                "60-300s": 0,     # 1-5分钟
                "300-600s": 0,    # 5-10分钟
                "600-1800s": 0,   # 10-30分钟
                "1800+s": 0       # 30分钟以上
            },
            "quality_metrics": {
                "avg_like_view_ratio": 0,
                "high_engagement_videos": 0  # 点赞/播放比例 > 0.05的视频数
            }
        }
        
        # 高级统计
        all_tags = []
        like_view_ratios = []
        
        for bvid, info in videos.items():
            # 检查视频文件是否存在
            video_path = self.get_video_path(bvid)
            if video_path:
                stats["video_with_files"] += 1
            
            # 按发布日期统计
            pubdate = info.get("pubdate", 0)
            if pubdate > 0:
                date_str = time.strftime("%Y-%m", time.localtime(pubdate))
                stats["videos_by_pubdate"][date_str] = stats["videos_by_pubdate"].get(date_str, 0) + 1
            
            # 统计标签
            for tag in info.get("tags", []):
                all_tags.append(tag)
            
            # 按时长分类
            duration = info.get("duration", 0)
            if duration <= 60:
                stats["videos_by_duration"]["0-60s"] += 1
            elif duration <= 300:
                stats["videos_by_duration"]["60-300s"] += 1
            elif duration <= 600:
                stats["videos_by_duration"]["300-600s"] += 1
            elif duration <= 1800:
                stats["videos_by_duration"]["600-1800s"] += 1
            else:
                stats["videos_by_duration"]["1800+s"] += 1
            
            # 统计UP主
            owner_name = info.get("owner_name", "")
            if owner_name:
                stats["top_uploaders"][owner_name] = stats["top_uploaders"].get(owner_name, 0) + 1
            
            # 计算点赞/播放比例
            view = info.get("view", 0)
            like = info.get("like", 0)
            if view > 0:
                ratio = like / view
                like_view_ratios.append(ratio)
                if ratio > 0.05:  # 高互动率标准
                    stats["quality_metrics"]["high_engagement_videos"] += 1
        
        # 统计常见标签
        from collections import Counter
        tag_counter = Counter(all_tags)
        stats["top_tags"] = {tag: count for tag, count in tag_counter.most_common(20)}
        
        # 统计平均点赞/播放比例
        if like_view_ratios:
            stats["quality_metrics"]["avg_like_view_ratio"] = sum(like_view_ratios) / len(like_view_ratios)
        
        # 格式化时长为小时:分钟:秒
        total_seconds = stats["total_duration_seconds"]
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        stats["total_duration_formatted"] = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
        
        # 统计数据集总大小
        total_size = 0
        for bvid in videos.keys():
            video_path = self.get_video_path(bvid)
            if video_path and os.path.exists(video_path):
                total_size += os.path.getsize(video_path)
        
        stats["total_size_bytes"] = total_size
        stats["total_size_mb"] = total_size / (1024 * 1024)
        stats["total_size_gb"] = total_size / (1024 * 1024 * 1024)
        
        self.logger.info(f"数据集统计完成，共 {stats['total_videos']} 个视频，"
                         f"总时长 {stats['total_duration_formatted']}，"
                         f"总大小 {stats['total_size_gb']:.2f}GB")
        
        return stats
    
    def export_stats_report(self, output_file: str = None) -> str:
        """
        导出数据集统计报告
        
        Args:
            output_file: 输出文件路径，默认为数据集目录下的stats_report.md
            
        Returns:
            str: 报告文件路径
        """
        stats = self.get_dataset_stats()
        
        if output_file is None:
            output_file = os.path.join(self.json_dir, "stats_report.md")
        
        report = f"""# 哔哩哔哩敏感视频数据集统计报告

## 基本信息

- **视频总数**: {stats['total_videos']}
- **总时长**: {stats['total_duration_formatted']}
- **总播放量**: {stats['total_views']:,}
- **总点赞数**: {stats['total_likes']:,}
- **总大小**: {stats['total_size_gb']:.2f} GB

## 视频分布

### 按时长分布

| 时长范围 | 视频数量 | 百分比 |
|---------|---------|-------|
| 0-60秒 | {stats['videos_by_duration']['0-60s']} | {stats['videos_by_duration']['0-60s']/stats['total_videos']*100:.1f}% |
| 1-5分钟 | {stats['videos_by_duration']['60-300s']} | {stats['videos_by_duration']['60-300s']/stats['total_videos']*100:.1f}% |
| 5-10分钟 | {stats['videos_by_duration']['300-600s']} | {stats['videos_by_duration']['300-600s']/stats['total_videos']*100:.1f}% |
| 10-30分钟 | {stats['videos_by_duration']['600-1800s']} | {stats['videos_by_duration']['600-1800s']/stats['total_videos']*100:.1f}% |
| 30分钟以上 | {stats['videos_by_duration']['1800+s']} | {stats['videos_by_duration']['1800+s']/stats['total_videos']*100:.1f}% |

### 按发布日期分布

"""
        
        # 添加按月分布
        months = sorted(stats["videos_by_pubdate"].keys())
        for month in months:
            count = stats["videos_by_pubdate"][month]
            percent = count / stats["total_videos"] * 100
            report += f"- **{month}**: {count} ({percent:.1f}%)\n"
        
        report += f"""
## 热门标签

"""
        
        # 添加热门标签
        for tag, count in stats["top_tags"].items():
            percent = count / stats["total_videos"] * 100
            report += f"- **{tag}**: {count} ({percent:.1f}%)\n"
        
        report += f"""
## 互动指标

- **平均点赞/播放比例**: {stats['quality_metrics']['avg_like_view_ratio']:.4f}
- **高互动视频数量**: {stats['quality_metrics']['high_engagement_videos']} ({stats['quality_metrics']['high_engagement_videos']/stats['total_videos']*100:.1f}%)

## 文件信息

- **带视频文件的条目**: {stats['video_with_files']} ({stats['video_with_files']/stats['total_videos']*100:.1f}%)
- **仅元数据条目**: {stats['total_videos'] - stats['video_with_files']} ({(stats['total_videos'] - stats['video_with_files'])/stats['total_videos']*100:.1f}%)

## TOP 10 上传者

"""
        
        # 添加TOP上传者
        uploaders = sorted(stats["top_uploaders"].items(), key=lambda x: x[1], reverse=True)[:10]
        for uploader, count in uploaders:
            percent = count / stats["total_videos"] * 100
            report += f"- **{uploader}**: {count} ({percent:.1f}%)\n"
        
        # 生成时间
        report += f"\n\n*报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*"
        
        # 写入文件
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            self.logger.info(f"统计报告已生成: {output_file}")
        except Exception as e:
            self.logger.error(f"生成统计报告失败: {str(e)}")
        
        return output_file
    
    def has_video(self, bvid: str) -> bool:
        """
        检查是否已存在指定视频的元数据
        
        Args:
            bvid: 视频BV号
            
        Returns:
            bool: 如果存在元数据文件则返回True，否则返回False
        """
        filename = self.config["json_filename_format"].format(bvid=bvid)
        file_path = os.path.join(self.json_dir, filename)
        return os.path.exists(file_path)
    
    def count_videos(self) -> int:
        """
        统计数据集中的视频数量
        
        Returns:
            int: 视频数量
        """
        count = 0
        for filename in os.listdir(self.json_dir):
            if filename.endswith('.json') and filename != 'index.json':
                count += 1
        return count
    
    def save_metadata(self, video_info: Dict[str, Any]) -> str:
        """
        保存视频元数据（save_video_info的别名）
        
        Args:
            video_info: 视频信息字典
            
        Returns:
            str: 保存的文件路径
        """
        return self.save_video_info(video_info)
    
    def update_video_path(self, bvid: str, video_path: str) -> bool:
        """
        更新视频的文件路径信息
        
        Args:
            bvid: 视频BV号
            video_path: 视频文件路径
            
        Returns:
            bool: 更新成功返回True，否则返回False
        """
        try:
            # 加载现有视频信息
            video_info = self.load_video_info(bvid)
            if not video_info:
                self.logger.warning(f"视频信息不存在: {bvid}")
                return False
            
            # 更新视频路径
            video_info["video_path"] = video_path
            video_info["has_video_file"] = True
            video_info["video_file_size"] = os.path.getsize(video_path) if os.path.exists(video_path) else 0
            
            # 保存更新后的信息
            self.save_video_info(video_info)
            self.logger.info(f"已更新视频路径: {bvid} -> {video_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新视频路径失败 {bvid}: {str(e)}")
            return False
    
    def generate_stats(self) -> Dict[str, Any]:
        """
        生成数据集统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 加载索引
            index_data = self.load_index()
            videos = index_data.get("videos", {})
            
            # 基本统计
            total_videos = len(videos)
            total_duration = sum(video.get("duration", 0) for video in videos.values())
            
            # 计算总文件大小
            total_size = 0
            for bvid in videos.keys():
                video_path = self.get_video_path(bvid)
                if video_path and os.path.exists(video_path):
                    total_size += os.path.getsize(video_path)
            
            # 格式化时长
            hours = total_duration // 3600
            minutes = (total_duration % 3600) // 60
            seconds = total_duration % 60
            duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            
            # 格式化大小
            size_gb = total_size / (1024 ** 3)
            
            stats = {
                "total_videos": total_videos,
                "total_duration": total_duration,
                "total_duration_str": duration_str,
                "total_size": total_size,
                "total_size_gb": size_gb,
                "last_updated": time.time()
            }
            
            self.logger.info(f"数据集统计完成，共 {total_videos} 个视频，总时长 {duration_str}，总大小 {size_gb:.2f}GB")
            return stats
            
        except Exception as e:
            self.logger.error(f"生成统计信息失败: {str(e)}")
            return {}
    
    def get_missing_video_files(self) -> List[str]:
        """
        获取JSON记录中存在但视频文件缺失的BV号列表
        
        Returns:
            List[str]: 缺失视频文件的BV号列表
        """
        try:
            # 加载索引
            index_data = self.load_index()
            videos = index_data.get("videos", {})
            
            missing_bvids = []
            
            for bvid in videos.keys():
                # 检查视频文件是否存在
                video_path = self.get_video_path(bvid)
                if not video_path or not os.path.exists(video_path):
                    missing_bvids.append(bvid)
            
            self.logger.info(f"检查完成，发现 {len(missing_bvids)} 个缺失的视频文件")
            return missing_bvids
            
        except Exception as e:
            self.logger.error(f"检查缺失视频文件失败: {str(e)}")
            return []


# 简单测试代码
if __name__ == "__main__":
    import sys
    import argparse
    
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="哔哩哔哩视频数据集管理工具")
    parser.add_argument("--json-dir", type=str, default="data/json", help="JSON数据存储目录")
    parser.add_argument("--video-dir", type=str, default="data/videos", help="视频存储目录")
    parser.add_argument("--check", action="store_true", help="检查数据集完整性")
    parser.add_argument("--stats", action="store_true", help="生成数据集统计报告")
    parser.add_argument("--report", type=str, help="统计报告输出路径")
    parser.add_argument("--increment", type=str, help="增量更新源目录")
    parser.add_argument("--force", action="store_true", help="强制更新已存在的视频")
    parser.add_argument("--debug", action="store_true", help="显示调试日志")
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 初始化数据集管理器
    dataset = DatasetManager(args.json_dir, args.video_dir)
    
    if args.check:
        # 检查数据集完整性
        result = dataset.check_dataset_integrity()
        print(f"数据集完整性检查结果:")
        print(f"  总视频数: {result['total_videos']}")
        print(f"  有JSON文件: {result['videos_with_json']}")
        print(f"  有视频文件: {result['videos_with_file']}")
        print(f"  缺少JSON: {len(result['missing_json'])}")
        print(f"  缺少视频: {len(result['missing_video'])}")
    
    elif args.stats:
        # 生成统计报告
        output_file = args.report if args.report else None
        report_path = dataset.export_stats_report(output_file)
        print(f"统计报告已生成: {report_path}")
    
    elif args.increment:
        # 增量更新
        result = dataset.incremental_update(args.increment, args.force)
        print(f"增量更新结果:")
        print(f"  处理文件数: {result.get('total_processed', 0)}")
        print(f"  添加JSON: {result.get('added_json', 0)}")
        print(f"  添加视频: {result.get('added_videos', 0)}")
        print(f"  更新JSON: {result.get('updated_json', 0)}")
        print(f"  跳过: {result.get('skipped', 0)}")
        if result.get('errors', []):
            print(f"  错误数: {len(result['errors'])}")
    
    else:
        # 默认生成索引
        index = dataset.generate_index()
        print(f"数据集包含 {index['stats']['total_videos']} 个视频")
        if index['stats']['total_videos'] > 0:
            print(f"  总时长: {index['stats']['total_duration']} 秒")
            print(f"  总播放量: {index['stats']['total_view']}")
            print(f"  总点赞数: {index['stats']['total_like']}") 