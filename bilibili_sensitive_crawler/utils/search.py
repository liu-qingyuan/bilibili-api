#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索模块

提供哔哩哔哩视频搜索功能，支持关键词搜索和筛选。
支持分页获取搜索结果，并提供结果过滤和排序功能。

作者: Claude
日期: 2025-05-20
"""

import os
import sys
import time
import random
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

# 添加父目录到系统路径，以便导入bilibili_api库
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 导入bilibili_api库
from bilibili_api import search, sync
from bilibili_api.utils.network import Credential


class BiliSearch:
    """B站搜索类"""
    
    def __init__(self, credential: Credential, config: Optional[Dict[str, Any]] = None):
        """
        初始化搜索器
        
        Args:
            credential: B站API凭证
            config: 搜索相关配置，如果不提供则使用默认配置
        """
        self.credential = credential
        self.logger = logging.getLogger("bili_crawler.search")
        
        # 默认配置
        self.config = {
            "page_size": 30,           # 每页结果数
            "max_pages": 50,           # 最大搜索页数
            "order": "totalrank",      # 排序方式：默认为综合排序
            "search_type": 0,          # 搜索类型：0=视频
            "duration": 0,             # 视频时长筛选：0=全部时长
            "tids": 0,                 # 分区ID：0=全部分区
            "page_interval": [1.0, 2.5], # 分页请求间隔时间范围(秒)
            "max_retries": 3,          # 单页搜索失败最大重试次数
            "min_view_count": 0,       # 最小播放量
            "min_pubdate": None,       # 最早发布日期 (YYYY-MM-DD)
            "max_pubdate": None,       # 最晚发布日期 (YYYY-MM-DD)
            "keyword_filters": [],     # 标题关键词过滤（包含这些词的视频）
            "keyword_excludes": [],    # 标题关键词排除（排除包含这些词的视频）
            "duplicate_check": True,   # 是否检查重复视频
            "quality_threshold": {     # 视频质量阈值
                "view_like_ratio": 0.05, # 点赞/播放比例最小值
                "min_views": 100,      # 最小播放量
                "min_like": 5,         # 最小点赞数
            }
        }
        
        # 更新配置
        if config and isinstance(config, dict):
            self._update_config(self.config, config.get("search", {}))
        
        # 已搜索视频集合(用于去重)
        self.searched_videos = set()
            
    def _update_config(self, base_config, new_config):
        """
        递归更新配置
        
        Args:
            base_config: 基础配置
            new_config: 新配置
        """
        for key, value in new_config.items():
            if key in base_config and isinstance(value, dict) and isinstance(base_config[key], dict):
                self._update_config(base_config[key], value)
            else:
                base_config[key] = value
            
    async def search_videos(self, keyword: str, progress_callback=None, limit: int = None) -> List[Dict[str, Any]]:
        """
        搜索视频
        
        Args:
            keyword: 搜索关键词
            progress_callback: 进度回调函数，接收参数 (current_page, total_pages, videos_found)
            limit: 视频数量限制
            
        Returns:
            List[Dict[str, Any]]: 视频信息列表，每个元素包含bvid和search_info
        """
        self.logger.info(f"开始搜索关键词: {keyword}")
        
        # 存储搜索结果
        video_ids = []
        total_count = 0
        
        # 清除已搜索集合(仅保留当前搜索会话中的去重)
        if self.config["duplicate_check"]:
            self.searched_videos.clear()
        
        # 分页搜索
        for page in range(1, self.config["max_pages"] + 1):
            # 调用进度回调
            if progress_callback:
                progress_callback(page, self.config["max_pages"], len(video_ids))
                
            # 添加随机延迟，避免请求频率过高
            interval = self.config["page_interval"]
            await asyncio.sleep(random.uniform(interval[0], interval[1]))
            
            # 尝试搜索，支持重试
            retry_count = 0
            success = False
            
            while not success and retry_count < self.config["max_retries"]:
                try:
                    # 执行搜索
                    search_result = await search.search_by_type(
                        keyword,
                        search_type=search.SearchObjectType.VIDEO,
                        page=page,
                        page_size=self.config["page_size"],
                        order_type=search.OrderVideo.TOTALRANK  # 使用综合排序
                    )
                    
                    success = True
                    
                except Exception as e:
                    retry_count += 1
                    self.logger.warning(f"搜索页面 {page} 失败 (尝试 {retry_count}/{self.config['max_retries']}): {str(e)}")
                    await asyncio.sleep(retry_count * 2)  # 指数退避
            
            if not success:
                self.logger.error(f"搜索页面 {page} 失败，达到最大重试次数，跳过此页")
                continue
                
            # 检查搜索结果
            if not search_result or "result" not in search_result:
                self.logger.warning(f"页面 {page} 未返回搜索结果")
                break
                
            # 获取结果列表
            results = search_result.get("result", [])
            
            # 调试：打印搜索结果的结构
            if results and self.logger.level <= logging.DEBUG:
                self.logger.debug(f"搜索结果示例: {results[0] if results else 'None'}")
            
            if not results:
                self.logger.info(f"页面 {page} 没有更多结果")
                break
                
            # 提取并预过滤视频ID
            page_ids = await self._filter_page_results(results, keyword)
            
            # 添加到搜索结果
            video_ids.extend(page_ids)
            
            # 更新计数
            new_count = len(page_ids)
            total_count += new_count
            self.logger.info(f"页面 {page}: 获取并过滤后得到 {new_count} 个视频，累计: {len(video_ids)}")
            
            # 检查是否达到最后一页
            if len(results) < self.config["page_size"]:
                self.logger.info("已到达最后一页，搜索完成")
                break
                
            # 检查是否达到数量限制
            if limit and len(video_ids) >= limit:
                self.logger.info(f"已达到视频数量限制: {limit}")
                video_ids = video_ids[:limit]
                break
                
        self.logger.info(f"搜索完成，共找到 {len(video_ids)} 个符合条件的视频")
        return video_ids
        
    async def _filter_page_results(self, results: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
        """
        过滤页面搜索结果
        
        Args:
            results: 搜索结果列表
            keyword: 搜索关键词
            
        Returns:
            List[Dict[str, Any]]: 过滤后的视频信息列表
        """
        filtered_ids = []
        
        for item in results:
            try:
                # 首先检查是否为视频类型
                if item.get("type") != "video":
                    self.logger.debug(f"跳过非视频类型: {item.get('type', 'unknown')}")
                    continue
                
                if "bvid" not in item:
                    self.logger.debug(f"跳过无bvid的项目: {item.get('title', 'unknown')}")
                    continue
                    
                bvid = item["bvid"]
                
                # 检查bvid是否有效
                if not bvid or not isinstance(bvid, str) or not bvid.startswith('BV'):
                    self.logger.debug(f"跳过无效的bvid: '{bvid}'")
                    continue
                
                # 检查重复
                if self.config["duplicate_check"] and bvid in self.searched_videos:
                    continue
                    
                # 添加到已搜索集合
                if self.config["duplicate_check"]:
                    self.searched_videos.add(bvid)
                
                # 基础信息过滤
                title = item.get("title", "").lower()
                view_count = item.get("play", 0)
                
                # 1. 视频播放量过滤
                if view_count < self.config["min_view_count"]:
                    continue
                    
                # 2. 标题关键词过滤
                if self.config["keyword_filters"]:
                    if not any(kw.lower() in title for kw in self.config["keyword_filters"]):
                        continue
                
                # 3. 标题排除关键词过滤
                if self.config["keyword_excludes"]:
                    if any(kw.lower() in title for kw in self.config["keyword_excludes"]):
                        continue
                
                # 4. 发布日期过滤
                pubdate = item.get("pubdate", 0)
                if pubdate:
                    pub_datetime = datetime.fromtimestamp(pubdate)
                    
                    if self.config["min_pubdate"]:
                        min_date = datetime.strptime(self.config["min_pubdate"], "%Y-%m-%d")
                        if pub_datetime < min_date:
                            continue
                            
                    if self.config["max_pubdate"]:
                        max_date = datetime.strptime(self.config["max_pubdate"], "%Y-%m-%d")
                        if pub_datetime > max_date:
                            continue
                
                # 通过过滤，添加到结果（保存完整的搜索信息）
                filtered_ids.append({
                    "bvid": bvid,
                    "search_info": {
                        "title": item.get("title", ""),
                        "author": item.get("author", ""),
                        "mid": item.get("mid", 0),
                        "typeid": item.get("typeid", ""),
                        "typename": item.get("typename", ""),
                        "play": item.get("play", 0),
                        "video_review": item.get("video_review", 0),
                        "favorites": item.get("favorites", 0),
                        "review": item.get("review", 0),
                        "like": item.get("like", 0),
                        "danmaku": item.get("danmaku", 0),
                        "duration_str": item.get("duration", ""),
                        "pubdate": item.get("pubdate", 0),
                        "senddate": item.get("senddate", 0),
                        "rank_score": item.get("rank_score", 0),
                        "tag": item.get("tag", ""),
                        "pic": item.get("pic", ""),
                        "arcurl": item.get("arcurl", ""),
                        "description": item.get("description", ""),
                    }
                })
                
            except Exception as e:
                self.logger.debug(f"过滤视频时出错: {str(e)}")
                continue
                
        return filtered_ids
        
    async def filter_videos(self, video_ids: List[str], **filter_args) -> List[Dict[str, Any]]:
        """
        根据多种条件过滤视频，并返回详细信息
        
        Args:
            video_ids: 要过滤的视频ID列表
            **filter_args: 过滤参数，可覆盖配置中的过滤条件
            
        Returns:
            List[Dict[str, Any]]: 过滤后的视频详细信息列表
        """
        from bilibili_api import video
        
        # 合并过滤参数
        filters = {
            "min_duration": filter_args.get("min_duration", 0),
            "max_duration": filter_args.get("max_duration", None),
            "min_view_count": filter_args.get("min_view_count", self.config["min_view_count"]),
            "min_like": filter_args.get("min_like", self.config["quality_threshold"]["min_like"]),
            "view_like_ratio": filter_args.get("view_like_ratio", self.config["quality_threshold"]["view_like_ratio"]),
        }
        
        filtered_videos = []
        total = len(video_ids)
        self.logger.info(f"开始详细过滤 {total} 个视频...")
        
        # 设置并发限制，避免请求过快
        semaphore = asyncio.Semaphore(3)
        
        async def process_video(bvid, index):
            """处理单个视频的协程"""
            async with semaphore:
                try:
                    # 添加随机延迟
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    # 获取视频信息
                    v = video.Video(bvid=bvid, credential=self.credential)
                    info = await v.get_info()
                    stat = await v.get_stat()
                    
                    # 获取视频信息
                    duration = info.get("duration", 0)  # 时长(秒)
                    view_count = stat.get("view", 0)    # 播放量
                    like_count = stat.get("like", 0)    # 点赞数
                    
                    # 计算质量指标
                    like_ratio = like_count / max(1, view_count)
                    
                    # 根据条件过滤
                    if filters["min_duration"] and duration < filters["min_duration"]:
                        return None
                        
                    if filters["max_duration"] and duration > filters["max_duration"]:
                        return None
                        
                    if view_count < filters["min_view_count"]:
                        return None
                        
                    if like_count < filters["min_like"]:
                        return None
                        
                    if like_ratio < filters["view_like_ratio"]:
                        return None
                    
                    # 组合视频信息
                    video_data = {
                        "bvid": bvid,
                        "title": info.get("title", ""),
                        "desc": info.get("desc", ""),
                        "duration": duration,
                        "pubdate": info.get("pubdate", 0),
                        "owner": {
                            "mid": info.get("owner", {}).get("mid", 0),
                            "name": info.get("owner", {}).get("name", ""),
                        },
                        "stat": {
                            "view": view_count,
                            "danmaku": stat.get("danmaku", 0),
                            "reply": stat.get("reply", 0),
                            "favorite": stat.get("favorite", 0),
                            "coin": stat.get("coin", 0),
                            "share": stat.get("share", 0),
                            "like": like_count,
                        },
                        "quality_score": round((like_ratio * 100), 2),  # 质量评分(百分比)
                    }
                    
                    self.logger.debug(f"[{index+1}/{total}] 视频 {bvid} 质量评分: {video_data['quality_score']}%")
                    return video_data
                    
                except Exception as e:
                    self.logger.warning(f"获取视频 {bvid} 信息时出错: {str(e)}，已跳过")
                    return None
        
        # 创建所有视频处理任务
        tasks = [process_video(bvid, i) for i, bvid in enumerate(video_ids)]
        
        # 并发执行任务
        results = await asyncio.gather(*tasks)
        
        # 过滤出有效结果并排序（按质量评分）
        filtered_videos = [v for v in results if v is not None]
        filtered_videos.sort(key=lambda x: x["quality_score"], reverse=True)
        
        self.logger.info(f"详细过滤完成，符合条件的视频: {len(filtered_videos)}/{total}")
        return filtered_videos
        
    async def search_and_filter(self, keyword: str, **filter_args) -> List[Dict[str, Any]]:
        """
        搜索并过滤视频，返回详细信息
        
        Args:
            keyword: 搜索关键词
            **filter_args: 过滤参数
            
        Returns:
            List[Dict[str, Any]]: 符合条件的视频详细信息列表
        """
        # 搜索视频
        video_ids = await self.search_videos(keyword)
        
        if not video_ids:
            self.logger.warning(f"搜索 '{keyword}' 没有找到视频")
            return []
            
        # 详细过滤视频
        filtered_videos = await self.filter_videos(video_ids, **filter_args)
        
        self.logger.info(f"搜索并过滤 '{keyword}' 完成，共找到 {len(filtered_videos)} 个符合条件的视频")
        return filtered_videos
    
    async def batch_search(self, keywords: List[str], limit: int = None, **filter_args) -> List[Dict[str, Any]]:
        """
        批量搜索多个关键词
        
        Args:
            keywords: 关键词列表
            limit: 总视频数量限制
            **filter_args: 过滤参数
            
        Returns:
            List[Dict[str, Any]]: 符合条件的视频详细信息列表
        """
        all_videos = []
        
        for keyword in keywords:
            self.logger.info(f"批量搜索: 开始处理关键词 '{keyword}'")
            
            # 搜索并过滤当前关键词
            videos = await self.search_and_filter(keyword, **filter_args)
            
            # 去除已有的重复视频
            if self.config["duplicate_check"] and all_videos:
                existing_bvids = {v["bvid"] for v in all_videos}
                videos = [v for v in videos if v["bvid"] not in existing_bvids]
            
            # 添加到结果列表
            all_videos.extend(videos)
            
            # 检查是否达到总数限制
            if limit and len(all_videos) >= limit:
                self.logger.info(f"已达到视频数量限制: {limit}")
                all_videos = all_videos[:limit]
                break
                
            self.logger.info(f"批量搜索: 完成关键词 '{keyword}'，当前共有 {len(all_videos)} 个视频")
            
        return all_videos


# 简单测试代码
if __name__ == "__main__":
    import sys
    
    async def test():
        # 禁用 API 调用的警告
        logging.getLogger("bilibili_api.utils.network").setLevel(logging.ERROR)
        
        # 设置控制台日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 从命令行获取关键词
        keyword = sys.argv[1] if len(sys.argv) > 1 else "测试"
        
        # 使用无登录凭证方式
        search_handler = BiliSearch(Credential(), {
            "search": {
                "min_view_count": 1000,
                "quality_threshold": {
                    "min_views": 1000,
                    "min_like": 10
                }
            }
        })
        
        # 搜索并过滤视频
        videos = await search_handler.search_and_filter(keyword)
        
        print(f"\n搜索关键词 '{keyword}' 的结果:")
        for i, video in enumerate(videos[:10]):  # 只显示前10个结果
            print(f"{i+1}. {video['title']} - 质量评分: {video['quality_score']}% - 播放量: {video['stat']['view']} - https://www.bilibili.com/video/{video['bvid']}")
        
        if len(videos) > 10:
            print(f"... 以及其他 {len(videos) - 10} 个结果")
            
    asyncio.run(test()) 