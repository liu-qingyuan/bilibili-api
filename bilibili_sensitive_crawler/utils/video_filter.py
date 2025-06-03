#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频过滤工具模块

功能：
1. 检测视频时长
2. 删除超出指定时长的视频文件
3. 删除对应的JSON元数据文件
4. 更新index.json索引文件
5. 生成删除报告

作者: Claude
日期: 2025-01-20
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import subprocess
import shutil
from datetime import datetime
import time


class VideoFilter:
    """视频过滤器类"""
    
    def __init__(self, metadata_dir: str, videos_dir: str, config: Dict = None):
        """
        初始化视频过滤器
        
        Args:
            metadata_dir: 元数据目录路径
            videos_dir: 视频文件目录路径
            config: 配置字典
        """
        self.metadata_dir = Path(metadata_dir)
        self.videos_dir = Path(videos_dir)
        self.config = config or {}
        self.logger = logging.getLogger("bili_crawler.video_filter")
        
        # 确保目录存在
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        # index.json文件路径
        self.index_file = self.metadata_dir / "index.json"
    
    def load_index(self) -> Dict:
        """加载index.json文件"""
        if not self.index_file.exists():
            self.logger.warning(f"索引文件不存在: {self.index_file}")
            return {"metadata": {}, "stats": {"total_videos": 0}, "videos": {}}
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载索引文件失败: {str(e)}")
            return {"metadata": {}, "stats": {"total_videos": 0}, "videos": {}}
    
    def save_index(self, index_data: Dict) -> bool:
        """保存index.json文件"""
        try:
            # 更新统计信息
            index_data["stats"]["total_videos"] = len(index_data.get("videos", {}))
            index_data["stats"]["last_updated"] = int(time.time())
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"索引文件已更新: {self.index_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存索引文件失败: {str(e)}")
            return False
    
    def remove_from_index(self, bvids: List[str]) -> bool:
        """从索引中删除指定的视频记录"""
        if not bvids:
            return True
        
        index_data = self.load_index()
        videos = index_data.get("videos", {})
        
        removed_count = 0
        for bvid in bvids:
            if bvid in videos:
                del videos[bvid]
                removed_count += 1
                self.logger.debug(f"从索引中删除视频记录: {bvid}")
        
        if removed_count > 0:
            index_data["videos"] = videos
            success = self.save_index(index_data)
            if success:
                self.logger.info(f"已从索引中删除 {removed_count} 个视频记录")
            return success
        else:
            self.logger.info("没有需要从索引中删除的视频记录")
            return True
    
    def get_video_duration_from_metadata(self, json_file: Path) -> Optional[int]:
        """
        从JSON元数据文件中获取视频时长
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            视频时长（秒），如果获取失败返回None
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 尝试从不同字段获取时长信息
            duration = None
            
            # 方法1: 从basic_info中获取（最常见的位置）
            if 'basic_info' in data and 'duration' in data['basic_info']:
                duration = data['basic_info']['duration']
            
            # 方法2: 从根级duration字段获取
            elif 'duration' in data:
                duration = data['duration']
            
            # 方法3: 从video_info中获取
            elif 'video_info' in data and 'duration' in data['video_info']:
                duration = data['video_info']['duration']
            
            # 方法4: 从页面信息中获取
            elif 'pages' in data and len(data['pages']) > 0:
                # 取第一个分P的时长
                duration = data['pages'][0].get('duration', None)
            
            # 方法5: 从stat信息中获取（某些情况下可能存在）
            elif 'stat' in data and 'duration' in data['stat']:
                duration = data['stat']['duration']
            
            if duration is not None:
                return int(duration)
            
            self.logger.warning(f"无法从元数据中获取视频时长: {json_file}")
            return None
            
        except Exception as e:
            self.logger.error(f"读取元数据文件失败 {json_file}: {str(e)}")
            return None
    
    def get_video_duration_from_file(self, video_file: Path) -> Optional[int]:
        """
        使用FFprobe从视频文件直接获取时长
        
        Args:
            video_file: 视频文件路径
            
        Returns:
            视频时长（秒），如果获取失败返回None
        """
        try:
            # 使用ffprobe获取视频时长
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(video_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                duration_str = probe_data.get('format', {}).get('duration')
                if duration_str:
                    return int(float(duration_str))
            
            self.logger.warning(f"FFprobe无法获取视频时长: {video_file}")
            return None
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"FFprobe超时: {video_file}")
            return None
        except Exception as e:
            self.logger.error(f"使用FFprobe获取视频时长失败 {video_file}: {str(e)}")
            return None
    
    def find_videos_by_duration(self, max_duration: int = 30) -> List[Dict]:
        """
        查找超出指定时长的视频
        
        Args:
            max_duration: 最大允许时长（秒）
            
        Returns:
            超出时长的视频信息列表
        """
        self.logger.info(f"开始查找超出 {max_duration} 秒的视频...")
        
        long_videos = []
        json_files = list(self.metadata_dir.glob("*.json"))
        
        self.logger.info(f"找到 {len(json_files)} 个元数据文件")
        
        for json_file in json_files:
            try:
                # 从文件名提取BV号
                bvid = json_file.stem
                
                # 获取视频时长
                duration = self.get_video_duration_from_metadata(json_file)
                
                if duration is None:
                    # 如果从元数据获取失败，尝试从视频文件获取
                    video_files = list(self.videos_dir.glob(f"{bvid}.*"))
                    if video_files:
                        duration = self.get_video_duration_from_file(video_files[0])
                
                if duration is not None and duration > max_duration:
                    # 查找对应的视频文件
                    video_files = list(self.videos_dir.glob(f"{bvid}.*"))
                    
                    video_info = {
                        'bvid': bvid,
                        'duration': duration,
                        'json_file': str(json_file),
                        'video_files': [str(vf) for vf in video_files],
                        'json_exists': json_file.exists(),
                        'video_exists': len(video_files) > 0
                    }
                    
                    long_videos.append(video_info)
                    self.logger.debug(f"发现超长视频: {bvid} ({duration}秒)")
                
            except Exception as e:
                self.logger.error(f"处理文件时出错 {json_file}: {str(e)}")
                continue
        
        self.logger.info(f"找到 {len(long_videos)} 个超出 {max_duration} 秒的视频")
        return long_videos
    
    def delete_long_videos(self, max_duration: int = 30, dry_run: bool = False, generate_report: bool = False) -> Dict:
        """
        删除超出指定时长的视频及其元数据
        
        Args:
            max_duration: 最大允许时长（秒）
            dry_run: 是否为试运行（不实际删除文件）
            generate_report: 是否生成删除报告
            
        Returns:
            删除操作的统计信息
        """
        self.logger.info(f"开始删除超出 {max_duration} 秒的视频...")
        if dry_run:
            self.logger.info("*** 试运行模式，不会实际删除文件 ***")
        
        # 查找超长视频
        long_videos = self.find_videos_by_duration(max_duration)
        
        if not long_videos:
            self.logger.info("没有找到需要删除的超长视频")
            return {
                'total_found': 0,
                'deleted_videos': 0,
                'deleted_json': 0,
                'failed_deletions': 0,
                'total_size_freed': 0,
                'deleted_files': [],
                'index_updated': False
            }
        
        # 统计信息
        stats = {
            'total_found': len(long_videos),
            'deleted_videos': 0,
            'deleted_json': 0,
            'failed_deletions': 0,
            'total_size_freed': 0,
            'deleted_files': [],
            'index_updated': False
        }
        
        # 收集需要从索引中删除的BV号
        deleted_bvids = []
        
        for video_info in long_videos:
            bvid = video_info['bvid']
            duration = video_info['duration']
            
            self.logger.info(f"处理超长视频: {bvid} ({duration}秒)")
            
            try:
                # 删除视频文件
                for video_file_path in video_info['video_files']:
                    video_file = Path(video_file_path)
                    if video_file.exists():
                        file_size = video_file.stat().st_size
                        
                        if not dry_run:
                            video_file.unlink()
                            self.logger.info(f"已删除视频文件: {video_file}")
                        else:
                            self.logger.info(f"[试运行] 将删除视频文件: {video_file}")
                        
                        stats['deleted_videos'] += 1
                        stats['total_size_freed'] += file_size
                        stats['deleted_files'].append({
                            'type': 'video',
                            'path': str(video_file),
                            'size': file_size,
                            'bvid': bvid,
                            'duration': duration
                        })
                
                # 删除JSON元数据文件
                json_file = Path(video_info['json_file'])
                if json_file.exists():
                    file_size = json_file.stat().st_size
                    
                    if not dry_run:
                        json_file.unlink()
                        self.logger.info(f"已删除元数据文件: {json_file}")
                    else:
                        self.logger.info(f"[试运行] 将删除元数据文件: {json_file}")
                    
                    stats['deleted_json'] += 1
                    stats['total_size_freed'] += file_size
                    stats['deleted_files'].append({
                        'type': 'json',
                        'path': str(json_file),
                        'size': file_size,
                        'bvid': bvid,
                        'duration': duration
                    })
                
                # 记录需要从索引中删除的BV号
                deleted_bvids.append(bvid)
                
            except Exception as e:
                self.logger.error(f"删除文件时出错 {bvid}: {str(e)}")
                stats['failed_deletions'] += 1
        
        # 更新索引文件
        if deleted_bvids and not dry_run:
            self.logger.info(f"正在从索引中删除 {len(deleted_bvids)} 个视频记录...")
            stats['index_updated'] = self.remove_from_index(deleted_bvids)
        elif deleted_bvids and dry_run:
            self.logger.info(f"[试运行] 将从索引中删除 {len(deleted_bvids)} 个视频记录")
            stats['index_updated'] = True  # 试运行时标记为成功
        
        # 输出统计信息
        self.logger.info("=" * 50)
        self.logger.info("删除操作统计:")
        self.logger.info(f"找到超长视频: {stats['total_found']} 个")
        self.logger.info(f"删除视频文件: {stats['deleted_videos']} 个")
        self.logger.info(f"删除元数据文件: {stats['deleted_json']} 个")
        self.logger.info(f"删除失败: {stats['failed_deletions']} 个")
        self.logger.info(f"索引文件更新: {'成功' if stats['index_updated'] else '失败'}")
        self.logger.info(f"释放空间: {stats['total_size_freed'] / 1024 / 1024:.2f} MB")
        self.logger.info("=" * 50)
        
        # 生成删除报告
        if generate_report:
            report_path = self.generate_deletion_report(stats)
            if report_path:
                self.logger.info(f"删除报告已生成: {report_path}")
        
        return stats
    
    def generate_deletion_report(self, stats: Dict, output_file: Optional[str] = None) -> str:
        """
        生成删除操作报告
        
        Args:
            stats: 删除操作统计信息
            output_file: 报告输出文件路径
            
        Returns:
            报告文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"deletion_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'delete_long_videos',
            'statistics': stats,
            'deleted_files': stats.get('deleted_files', [])
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"删除报告已保存: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"保存删除报告失败: {str(e)}")
            return ""
    
    def list_long_videos(self, max_duration: int = 30) -> None:
        """
        列出超出指定时长的视频（不删除）
        
        Args:
            max_duration: 最大允许时长（秒）
        """
        long_videos = self.find_videos_by_duration(max_duration)
        
        if not long_videos:
            self.logger.info(f"没有找到超出 {max_duration} 秒的视频")
            return
        
        self.logger.info(f"找到 {len(long_videos)} 个超出 {max_duration} 秒的视频:")
        self.logger.info("=" * 80)
        
        total_size = 0
        for i, video_info in enumerate(long_videos, 1):
            bvid = video_info['bvid']
            duration = video_info['duration']
            
            # 计算文件大小
            file_size = 0
            for video_file_path in video_info['video_files']:
                video_file = Path(video_file_path)
                if video_file.exists():
                    file_size += video_file.stat().st_size
            
            json_file = Path(video_info['json_file'])
            if json_file.exists():
                file_size += json_file.stat().st_size
            
            total_size += file_size
            
            self.logger.info(f"{i:3d}. {bvid} - {duration}秒 - {file_size/1024/1024:.2f}MB")
            
            # 显示文件状态
            status_parts = []
            if video_info['video_exists']:
                status_parts.append(f"视频文件: {len(video_info['video_files'])}个")
            if video_info['json_exists']:
                status_parts.append("元数据: 存在")
            
            if status_parts:
                self.logger.info(f"     状态: {', '.join(status_parts)}")
        
        self.logger.info("=" * 80)
        self.logger.info(f"总计: {len(long_videos)} 个视频，占用空间: {total_size/1024/1024:.2f}MB") 