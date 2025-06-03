#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频信息采集模块

用于采集哔哩哔哩视频的详细信息，包括基本信息、
统计数据、标签、分P信息等，并支持将数据保存为
JSON格式。

作者: Claude
日期: 2025-05-20
"""

import os
import sys
import json
import time
import random
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# 添加父目录到系统路径，以便导入bilibili_api库
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 导入bilibili_api库
from bilibili_api import video, comment, sync
from bilibili_api.utils.network import Credential


class BiliCrawler:
    """B站视频信息爬取类"""
    
    def __init__(self, credential: Credential, config: Optional[Dict[str, Any]] = None):
        """
        初始化爬虫
        
        Args:
            credential: B站API凭证
            config: 爬虫相关配置，如果不提供则使用默认配置
        """
        self.credential = credential
        self.logger = logging.getLogger("bili_crawler.crawler")
        
        # 默认配置
        self.config = {
            "include_comments": False,
            "include_danmaku": False,
            "max_comments": 100,
            "rate_limit": {
                "enable": True,
                "interval": 1.5,
                "random_offset": 0.5,
            }
        }
        
        # 更新配置
        if config and isinstance(config, dict):
            self._update_config(self.config, config)
            
    def _update_config(self, base_config, new_config):
        """递归更新配置"""
        for key, value in new_config.items():
            if key in base_config and isinstance(value, dict) and isinstance(base_config[key], dict):
                self._update_config(base_config[key], value)
            else:
                base_config[key] = value
            
    async def get_video_info(self, bvid: str) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Dict[str, Any]: 视频信息字典
        """
        if self.config["rate_limit"]["enable"]:
            # 添加随机延迟，避免请求频率过高
            interval = self.config["rate_limit"]["interval"]
            offset = self.config["rate_limit"]["random_offset"]
            delay = interval + random.uniform(-offset, offset)
            await asyncio.sleep(max(0.1, delay))
            
        self.logger.info(f"获取视频信息: {bvid}")
        
        try:
            # 创建视频对象
            v = video.Video(bvid=bvid, credential=self.credential)
            
            # 获取基本信息
            info = await v.get_info()
            
            # 获取视频详细信息
            detail = await v.get_detail()
            
            # 获取视频标签
            tags = await v.get_tags()
            
            # 获取分P信息
            pages = await v.get_pages()
            
            # 获取相关视频
            try:
                related = await v.get_related()
                if isinstance(related, list):
                    related = {"data": related}
            except Exception as e:
                self.logger.debug(f"获取相关视频失败: {e}")
                related = {"data": []}
            
            # 获取实时在线人数
            try:
                online = await v.get_online()
                if isinstance(online, (int, str)):
                    online = {"count": online}
            except Exception as e:
                self.logger.debug(f"获取在线人数失败: {e}")
                online = {"count": 0}
            
            # 获取充电用户
            try:
                chargers = await v.get_chargers()
                if isinstance(chargers, list):
                    chargers = {"list": chargers}
            except Exception as e:
                # 静默处理充电信息不可用的情况（错误码62001是正常的）
                if "62001" not in str(e):
                    self.logger.debug(f"获取充电用户失败: {e}")
                chargers = {"list": []}
            
            # 获取用户关系
            try:
                relation = await v.get_relation()
            except Exception as e:
                self.logger.debug(f"获取用户关系失败: {e}")
                relation = {}
            
            # 获取需要cid的信息
            ai_conclusion = {}
            pbp = {}
            subtitle_info = {}
            player_info = {}
            
            if pages and len(pages) > 0:
                try:
                    cid = pages[0].get("cid") if isinstance(pages[0], dict) else None
                    if cid:
                        # 获取AI总结
                        try:
                            ai_conclusion = await v.get_ai_conclusion(cid=cid)
                        except Exception as e:
                            self.logger.debug(f"获取AI总结失败: {e}")
                            ai_conclusion = {}
                        
                        # 获取高能进度条
                        try:
                            pbp = await v.get_pbp(cid=cid)
                        except Exception as e:
                            self.logger.debug(f"获取高能进度条失败: {e}")
                            pbp = {}
                        
                        # 获取字幕信息
                        try:
                            subtitle_info = await v.get_subtitle(cid)
                        except Exception as e:
                            self.logger.debug(f"获取字幕信息失败: {e}")
                            subtitle_info = {}
                        
                        # 获取播放器信息
                        try:
                            player_info = await v.get_player_info(cid)
                        except Exception as e:
                            self.logger.debug(f"获取播放器信息失败: {e}")
                            player_info = {}
                except Exception as e:
                    self.logger.debug(f"处理分P信息失败: {e}")
            
            # 组织数据 - 去除重复信息，优化结构
            result = {
                # 保持向后兼容的基本信息结构
                "basic_info": {
                    "bvid": bvid,
                    "aid": info.get("aid", 0),
                    "title": info.get("title", ""),
                    "desc": info.get("desc", ""),
                    "duration": info.get("duration", 0),  # 视频时长(秒)
                    "pubdate": info.get("pubdate", 0),  # 发布时间戳
                    "ctime": info.get("ctime", 0),  # 投稿时间戳
                    "videos": info.get("videos", 0),  # 分P数
                    "pic": info.get("pic", ""),  # 封面图片URL
                    "tname": info.get("tname", ""),  # 分区名
                    "copyright": info.get("copyright", 0),  # 版权信息
                },
                
                # UP主信息
                "owner": {
                    "mid": info.get("owner", {}).get("mid", 0),
                    "name": info.get("owner", {}).get("name", ""),
                    "face": info.get("owner", {}).get("face", ""),
                },
                
                # 统计数据
                "stat": {
                    "view": info.get("stat", {}).get("view", 0),
                    "danmaku": info.get("stat", {}).get("danmaku", 0),
                    "reply": info.get("stat", {}).get("reply", 0),
                    "favorite": info.get("stat", {}).get("favorite", 0),
                    "coin": info.get("stat", {}).get("coin", 0),
                    "share": info.get("stat", {}).get("share", 0),
                    "like": info.get("stat", {}).get("like", 0),
                },
                
                # 权限信息（从detail中提取，避免重复）
                "rights": info.get("rights", {}),
                
                # 标签信息
                "tags": [
                    {
                        "tag_id": tag.get("tag_id", 0),
                        "tag_name": tag.get("tag_name", ""),
                        "use": tag.get("count", {}).get("use", 0),
                    }
                    for tag in tags
                ],
                
                # 分P信息（只保留核心字段）
                "pages": [
                    {
                        "cid": page.get("cid"),
                        "page": page.get("page"),
                        "part": page.get("part"),
                        "duration": page.get("duration"),
                        "dimension": page.get("dimension"),
                    }
                    for page in pages
                ] if pages else [],
                
                # 扩展信息（detail中的额外字段，去除重复部分）
                "detail_extra": {
                    "tid": detail.get("View", {}).get("tid"),
                    "tid_v2": detail.get("View", {}).get("tid_v2"),
                    "tname_v2": detail.get("View", {}).get("tname_v2"),
                    "state": detail.get("View", {}).get("state"),
                    "dynamic": detail.get("View", {}).get("dynamic"),
                    "argue_info": detail.get("View", {}).get("argue_info"),
                    "teenage_mode": detail.get("View", {}).get("teenage_mode"),
                    "is_story": detail.get("View", {}).get("is_story"),
                    "enable_vt": detail.get("View", {}).get("enable_vt"),
                    "vt_display": detail.get("View", {}).get("vt_display"),
                } if detail and detail.get("View") else {},
                
                # 相关视频（限制数量）
                "related": related.get("data", [])[:10] if isinstance(related, dict) else [],
                
                # 实时数据
                "online": online,
                "chargers": chargers.get("list", [])[:20] if isinstance(chargers, dict) else [],
                "relation": relation,
                
                # AI和智能功能
                "ai_conclusion": ai_conclusion,
                "pbp": pbp,  # 高能进度条
                
                # 字幕和播放器信息
                "subtitle": subtitle_info,
                "player_info": player_info,
                
                # 元数据
                "crawl_time": int(time.time()),
            }
            
            # 获取视频评论
            if self.config["include_comments"]:
                try:
                    result["comments"] = await self._get_comments(bvid)
                except Exception as e:
                    self.logger.warning(f"获取视频评论失败: {e}")
                    result["comments"] = []
            
            # 获取视频弹幕
            if self.config["include_danmaku"]:
                try:
                    result["danmaku"] = await self._get_danmaku(v)
                except Exception as e:
                    self.logger.warning(f"获取视频弹幕失败: {e}")
                    result["danmaku"] = []
            
            self.logger.info(f"视频信息获取成功: {bvid}")
            return result
            
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {bvid}, 错误: {str(e)}")
            raise
            
    async def _get_comments(self, bvid: str, limit: int = None) -> List[Dict[str, Any]]:
        """获取视频评论"""
        if limit is None:
            limit = self.config["max_comments"]
            
        comments_list = []
        page = 1
        
        try:
            # 创建评论对象
            comments = comment.get_comments(bvid, comment.ResourceType.VIDEO)
            
            # 获取第一页评论
            comments_data = await comments.get_main(page=page)
            
            # 提取评论
            for c in comments_data.get("replies", []):
                if len(comments_list) >= limit:
                    break
                    
                comments_list.append({
                    "rpid": c.get("rpid", 0),  # 评论ID
                    "mid": c.get("member", {}).get("mid", 0),  # 用户ID
                    "uname": c.get("member", {}).get("uname", ""),  # 用户名
                    "content": c.get("content", {}).get("message", ""),  # 评论内容
                    "like": c.get("like", 0),  # 点赞数
                    "ctime": c.get("ctime", 0),  # 发布时间戳
                    "level": c.get("member", {}).get("level_info", {}).get("current_level", 0),  # 用户等级
                })
            
            return comments_list
            
        except Exception as e:
            self.logger.warning(f"获取评论失败: {str(e)}")
            return []
            
    async def _get_danmaku(self, v: video.Video) -> List[Dict[str, Any]]:
        """获取视频弹幕"""
        danmaku_list = []
        
        try:
            # 获取视频所有弹幕
            all_danmaku = await v.get_danmaku()
            
            # 提取弹幕信息
            for d in all_danmaku:
                danmaku_list.append({
                    "text": d.text,  # 弹幕内容
                    "dm_time": d.dm_time,  # 弹幕出现时间(秒)
                    "ctime": d.ctime,  # 发送时间戳
                    "weight": d.weight,  # 权重
                    "id": d.id,  # 弹幕ID
                    "idstr": d.idstr,  # 弹幕ID字符串
                    "color": d.color,  # 颜色
                    "mode": d.mode,  # 模式(滚动、顶部、底部)
                    "font_size": d.font_size,  # 字体大小
                    "pool": d.pool,  # 弹幕池
                })
            
            return danmaku_list
            
        except Exception as e:
            self.logger.warning(f"获取弹幕失败: {str(e)}")
            return []
            
    def to_json(self, data: Dict[str, Any], indent: int = 4) -> str:
        """
        将数据转换为JSON字符串
        
        Args:
            data: 要转换的数据
            indent: 缩进空格数
            
        Returns:
            str: JSON字符串
        """
        return json.dumps(data, ensure_ascii=False, indent=indent)
        
    def save_to_file(self, data: Dict[str, Any], filename: str) -> None:
        """
        保存数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.to_json(data))
                
            self.logger.info(f"数据已保存至: {filename}")
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
            raise


# 简单测试代码
if __name__ == "__main__":
    import sys
    
    async def test():
        # 禁用 API 调用的警告
        logging.getLogger("bilibili_api.utils.network").setLevel(logging.ERROR)
        
        # 设置控制台日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 从命令行获取视频BV号
        bvid = sys.argv[1] if len(sys.argv) > 1 else "BV1GJ411x7h7"  # 默认一个示例视频
        
        # 使用无登录凭证方式
        crawler = BiliCrawler(Credential())
        
        # 获取视频信息
        video_info = await crawler.get_video_info(bvid)
        
        # 打印部分信息
        print(f"视频标题: {video_info['basic_info']['title']}")
        print(f"UP主: {video_info['owner']['name']}")
        print(f"播放量: {video_info['stat']['view']}")
        print(f"弹幕数: {video_info['stat']['danmaku']}")
        print(f"点赞数: {video_info['stat']['like']}")
        print(f"标签: {', '.join([tag['tag_name'] for tag in video_info['tags']])}")
        
        # 保存到文件
        crawler.save_to_file(video_info, f"{bvid}.json")
        
    asyncio.run(test()) 