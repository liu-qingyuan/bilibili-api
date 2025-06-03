#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件匹配分析工具

功能：
1. 分析视频文件和JSON文件的匹配情况
2. 找出孤立的视频文件（有视频无JSON）
3. 找出孤立的JSON文件（有JSON无视频）
4. 同步和更新index.json索引文件
5. 生成清理建议

作者: Claude
日期: 2025-01-20
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime
import time


class FileAnalyzer:
    """文件匹配分析器"""
    
    def __init__(self, metadata_dir: str, videos_dir: str):
        """
        初始化文件分析器
        
        Args:
            metadata_dir: 元数据目录路径
            videos_dir: 视频文件目录路径
        """
        self.metadata_dir = Path(metadata_dir)
        self.videos_dir = Path(videos_dir)
        self.logger = logging.getLogger("bili_crawler.file_analyzer")
        
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
    
    def get_index_videos(self) -> Set[str]:
        """获取索引中记录的所有视频BV号"""
        index_data = self.load_index()
        videos = index_data.get("videos", {})
        return set(videos.keys())
    
    def get_video_files(self) -> Set[str]:
        """获取所有视频文件的BV号"""
        video_files = set()
        
        if not self.videos_dir.exists():
            self.logger.warning(f"视频目录不存在: {self.videos_dir}")
            return video_files
        
        for video_file in self.videos_dir.glob("*.mp4"):
            # 从文件名提取BV号 (例如: BV1234567890.mp4 -> BV1234567890)
            bv_id = video_file.stem
            video_files.add(bv_id)
        
        self.logger.info(f"找到 {len(video_files)} 个视频文件")
        return video_files
    
    def get_json_files(self) -> Set[str]:
        """获取所有JSON文件的BV号"""
        json_files = set()
        
        if not self.metadata_dir.exists():
            self.logger.warning(f"元数据目录不存在: {self.metadata_dir}")
            return json_files
        
        for json_file in self.metadata_dir.glob("*.json"):
            # 跳过index.json
            if json_file.name == "index.json":
                continue
            
            # 从文件名提取BV号 (例如: BV1234567890.json -> BV1234567890)
            bv_id = json_file.stem
            json_files.add(bv_id)
        
        self.logger.info(f"找到 {len(json_files)} 个JSON文件")
        return json_files
    
    def analyze_file_matching(self, check_index: bool = True) -> Dict:
        """
        分析文件匹配情况
        
        Args:
            check_index: 是否检查索引文件的匹配情况
        """
        self.logger.info("开始分析文件匹配情况...")
        
        video_files = self.get_video_files()
        json_files = self.get_json_files()
        
        # 计算匹配情况
        matched_files = video_files & json_files  # 交集：既有视频又有JSON
        orphan_videos = video_files - json_files  # 有视频无JSON
        orphan_jsons = json_files - video_files   # 有JSON无视频
        
        analysis_result = {
            "total_videos": len(video_files),
            "total_jsons": len(json_files),
            "matched_pairs": len(matched_files),
            "orphan_videos": list(orphan_videos),
            "orphan_jsons": list(orphan_jsons),
            "orphan_video_count": len(orphan_videos),
            "orphan_json_count": len(orphan_jsons),
            "analysis_time": datetime.now().isoformat()
        }
        
        # 检查索引文件匹配情况
        if check_index:
            index_videos = self.get_index_videos()
            
            # 索引中有记录但文件不存在的视频
            index_orphans = index_videos - matched_files
            # 有文件但索引中没有记录的视频
            missing_from_index = matched_files - index_videos
            
            analysis_result.update({
                "index_total": len(index_videos),
                "index_orphans": list(index_orphans),
                "index_orphan_count": len(index_orphans),
                "missing_from_index": list(missing_from_index),
                "missing_from_index_count": len(missing_from_index),
                "index_match_rate": len(matched_files & index_videos) / len(index_videos) * 100 if index_videos else 0
            })
        
        # 打印分析结果
        self.logger.info("=" * 60)
        self.logger.info("文件匹配分析结果")
        self.logger.info("=" * 60)
        self.logger.info(f"视频文件总数: {analysis_result['total_videos']}")
        self.logger.info(f"JSON文件总数: {analysis_result['total_jsons']}")
        self.logger.info(f"匹配的文件对: {analysis_result['matched_pairs']}")
        self.logger.info(f"孤立视频文件: {analysis_result['orphan_video_count']} 个")
        self.logger.info(f"孤立JSON文件: {analysis_result['orphan_json_count']} 个")
        
        if check_index:
            self.logger.info(f"索引记录总数: {analysis_result['index_total']}")
            self.logger.info(f"索引孤立记录: {analysis_result['index_orphan_count']} 个")
            self.logger.info(f"缺失索引记录: {analysis_result['missing_from_index_count']} 个")
            self.logger.info(f"索引匹配率: {analysis_result['index_match_rate']:.1f}%")
        
        if orphan_videos:
            self.logger.warning("孤立视频文件（有视频无JSON）:")
            for bv_id in sorted(orphan_videos)[:10]:  # 只显示前10个
                self.logger.warning(f"  - {bv_id}.mp4")
            if len(orphan_videos) > 10:
                self.logger.warning(f"  ... 还有 {len(orphan_videos) - 10} 个")
        
        if orphan_jsons:
            self.logger.warning("孤立JSON文件（有JSON无视频）:")
            for bv_id in sorted(orphan_jsons)[:10]:  # 只显示前10个
                self.logger.warning(f"  - {bv_id}.json")
            if len(orphan_jsons) > 10:
                self.logger.warning(f"  ... 还有 {len(orphan_jsons) - 10} 个")
        
        if check_index and analysis_result.get('index_orphan_count', 0) > 0:
            self.logger.warning("索引孤立记录（索引中有但文件不存在）:")
            for bv_id in sorted(analysis_result['index_orphans'])[:10]:
                self.logger.warning(f"  - {bv_id}")
            if len(analysis_result['index_orphans']) > 10:
                self.logger.warning(f"  ... 还有 {len(analysis_result['index_orphans']) - 10} 个")
        
        return analysis_result
    
    def sync_index_with_files(self, dry_run: bool = True) -> Dict:
        """
        同步索引文件与实际文件
        
        Args:
            dry_run: 是否为试运行模式
            
        Returns:
            同步结果字典
        """
        self.logger.info(f"{'[试运行] ' if dry_run else ''}开始同步索引文件...")
        
        # 分析文件匹配情况
        analysis = self.analyze_file_matching(check_index=True)
        
        # 加载当前索引
        index_data = self.load_index()
        videos = index_data.get("videos", {})
        original_count = len(videos)
        
        # 统计信息
        sync_result = {
            "removed_from_index": [],
            "removed_count": 0,
            "kept_in_index": original_count,
            "sync_time": datetime.now().isoformat(),
            "dry_run": dry_run,
            "success": False
        }
        
        # 删除索引中的孤立记录
        index_orphans = analysis.get('index_orphans', [])
        if index_orphans:
            self.logger.info(f"{'[试运行] ' if dry_run else ''}从索引中删除 {len(index_orphans)} 个孤立记录...")
            
            for bvid in index_orphans:
                if bvid in videos:
                    if not dry_run:
                        del videos[bvid]
                    sync_result["removed_from_index"].append(bvid)
                    self.logger.debug(f"{'[试运行] ' if dry_run else ''}从索引中删除: {bvid}")
            
            sync_result["removed_count"] = len(sync_result["removed_from_index"])
            # 修复计算逻辑
            if dry_run:
                sync_result["kept_in_index"] = original_count - sync_result["removed_count"]
            else:
                sync_result["kept_in_index"] = len(videos)
        
        # 保存更新后的索引
        if not dry_run and sync_result["removed_count"] > 0:
            index_data["videos"] = videos
            sync_result["success"] = self.save_index(index_data)
        else:
            sync_result["success"] = True  # 试运行或无需更新时标记为成功
        
        # 输出结果
        self.logger.info("=" * 60)
        self.logger.info(f"{'[试运行] ' if dry_run else ''}索引同步结果")
        self.logger.info("=" * 60)
        self.logger.info(f"原始记录数: {original_count} 个")
        self.logger.info(f"删除孤立记录: {sync_result['removed_count']} 个")
        self.logger.info(f"保留有效记录: {sync_result['kept_in_index']} 个")
        self.logger.info(f"同步状态: {'成功' if sync_result['success'] else '失败'}")
        
        return sync_result
    
    def clean_orphan_files(self, clean_videos: bool = False, clean_jsons: bool = False, 
                          update_index: bool = False, dry_run: bool = True) -> Dict:
        """
        清理孤立文件
        
        Args:
            clean_videos: 是否清理孤立视频文件
            clean_jsons: 是否清理孤立JSON文件
            update_index: 是否同时更新索引文件
            dry_run: 是否为试运行模式
        
        Returns:
            清理结果字典
        """
        analysis_result = self.analyze_file_matching(check_index=update_index)
        
        cleaned_videos = []
        cleaned_jsons = []
        
        if clean_videos and analysis_result['orphan_videos']:
            self.logger.info(f"{'[试运行] ' if dry_run else ''}开始清理孤立视频文件...")
            
            for bv_id in analysis_result['orphan_videos']:
                video_path = self.videos_dir / f"{bv_id}.mp4"
                if video_path.exists():
                    if not dry_run:
                        try:
                            video_path.unlink()
                            self.logger.info(f"已删除孤立视频: {video_path}")
                            cleaned_videos.append(bv_id)
                        except Exception as e:
                            self.logger.error(f"删除视频文件失败 {video_path}: {e}")
                    else:
                        self.logger.info(f"[试运行] 将删除孤立视频: {video_path}")
                        cleaned_videos.append(bv_id)
        
        if clean_jsons and analysis_result['orphan_jsons']:
            self.logger.info(f"{'[试运行] ' if dry_run else ''}开始清理孤立JSON文件...")
            
            for bv_id in analysis_result['orphan_jsons']:
                json_path = self.metadata_dir / f"{bv_id}.json"
                if json_path.exists():
                    if not dry_run:
                        try:
                            json_path.unlink()
                            self.logger.info(f"已删除孤立JSON: {json_path}")
                            cleaned_jsons.append(bv_id)
                        except Exception as e:
                            self.logger.error(f"删除JSON文件失败 {json_path}: {e}")
                    else:
                        self.logger.info(f"[试运行] 将删除孤立JSON: {json_path}")
                        cleaned_jsons.append(bv_id)
        
        clean_result = {
            "cleaned_videos": cleaned_videos,
            "cleaned_jsons": cleaned_jsons,
            "cleaned_video_count": len(cleaned_videos),
            "cleaned_json_count": len(cleaned_jsons),
            "dry_run": dry_run,
            "clean_time": datetime.now().isoformat(),
            "index_synced": False
        }
        
        # 同步索引文件
        if update_index and not dry_run:
            self.logger.info("正在同步索引文件...")
            sync_result = self.sync_index_with_files(dry_run=False)
            clean_result["index_synced"] = sync_result["success"]
        elif update_index and dry_run:
            self.logger.info("[试运行] 将同步索引文件")
            clean_result["index_synced"] = True
        
        self.logger.info("=" * 60)
        self.logger.info(f"{'[试运行] ' if dry_run else ''}清理结果")
        self.logger.info("=" * 60)
        self.logger.info(f"清理的视频文件: {clean_result['cleaned_video_count']} 个")
        self.logger.info(f"清理的JSON文件: {clean_result['cleaned_json_count']} 个")
        if update_index:
            self.logger.info(f"索引文件同步: {'成功' if clean_result['index_synced'] else '失败'}")
        
        return clean_result
    
    def save_analysis_report(self, output_path: str = None) -> str:
        """保存分析报告到文件"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"logs/file_analysis_report_{timestamp}.json"
        
        analysis_result = self.analyze_file_matching()
        
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"分析报告已保存到: {output_file}")
        return str(output_file)


def main():
    """主函数，用于测试"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    analyzer = FileAnalyzer("data/json", "data/videos")
    
    # 分析文件匹配情况
    result = analyzer.analyze_file_matching()
    
    # 保存报告
    report_path = analyzer.save_analysis_report()
    
    print(f"\n分析完成！报告已保存到: {report_path}")


if __name__ == "__main__":
    main() 