#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哔哩哔哩视频下载模块

提供视频下载功能，支持480p清晰度视频（含音频）的下载、
断点续传、并发控制、智能重试和错误恢复等功能。

作者: Claude
日期: 2025-05-20
更新: 2025-05-24
"""

import os
import sys
import re
import time
import asyncio
import logging
import aiohttp
import aiofiles
import subprocess
import random
import socket
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Set
import traceback

# 添加父目录到系统路径，以便导入bilibili_api库
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from bilibili_api import video, sync
from bilibili_api.utils.network import Credential


class DownloadException(Exception):
    """下载异常基类"""
    def __init__(self, message: str, bvid: Optional[str] = None):
        self.message = message
        self.bvid = bvid
        super().__init__(message)
    
    def __str__(self):
        if self.bvid:
            return f"[{self.bvid}] {self.message}"
        return self.message


class NetworkError(DownloadException):
    """网络连接错误"""
    def __init__(self, message: str, bvid: Optional[str] = None, host: Optional[str] = None):
        self.host = host
        super().__init__(message, bvid)
    
    def __str__(self):
        if self.host:
            return f"[{self.bvid if self.bvid else '未知'}] 网络错误 ({self.host}): {self.message}"
        return super().__str__()


class VideoStreamError(DownloadException):
    """视频流错误"""
    def __init__(self, message: str, bvid: Optional[str] = None, quality: Optional[int] = None):
        self.quality = quality
        super().__init__(message, bvid)
    
    def __str__(self):
        if self.quality:
            return f"[{self.bvid if self.bvid else '未知'}] 视频流错误 (清晰度:{self.quality}): {self.message}"
        return super().__str__()


class AudioStreamError(DownloadException):
    """音频流错误"""
    pass


class MergeError(DownloadException):
    """合并错误"""
    def __init__(self, message: str, bvid: Optional[str] = None, error_code: Optional[int] = None):
        self.error_code = error_code
        super().__init__(message, bvid)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.bvid if self.bvid else '未知'}] 合并错误 (代码:{self.error_code}): {self.message}"
        return super().__str__()


class RetryExceededError(DownloadException):
    """超过最大重试次数"""
    def __init__(self, message: str, bvid: Optional[str] = None, retry_count: int = 0):
        self.retry_count = retry_count
        super().__init__(message, bvid)
    
    def __str__(self):
        return f"[{self.bvid if self.bvid else '未知'}] 超过最大重试次数({self.retry_count}): {self.message}"


class InfoFetchError(DownloadException):
    """获取视频信息失败"""
    pass


class DiskSpaceError(DownloadException):
    """磁盘空间不足"""
    def __init__(self, message: str, bvid: Optional[str] = None, required: int = 0, available: int = 0):
        self.required = required
        self.available = available
        super().__init__(message, bvid)
    
    def __str__(self):
        if self.required and self.available:
            return f"[{self.bvid if self.bvid else '未知'}] 磁盘空间不足: 需要 {self.required/1024/1024:.2f}MB, 可用 {self.available/1024/1024:.2f}MB"
        return super().__str__()


class ExternalToolError(DownloadException):
    """外部工具错误"""
    def __init__(self, message: str, bvid: Optional[str] = None, tool: str = "", cmd: str = ""):
        self.tool = tool
        self.cmd = cmd
        super().__init__(message, bvid)
    
    def __str__(self):
        if self.tool:
            return f"[{self.bvid if self.bvid else '未知'}] 外部工具({self.tool})错误: {self.message}"
        return super().__str__()


class BiliDownloader:
    """B站视频下载类"""
    
    def __init__(self, credential: Credential, save_dir: str = "videos", config: Optional[Dict[str, Any]] = None):
        """
        初始化下载器
        
        Args:
            credential: B站API凭证
            save_dir: 视频保存目录
            config: 下载相关配置，如果不提供则使用默认配置
        """
        self.credential = credential
        self.save_dir = save_dir
        self.logger = logging.getLogger("bili_crawler.downloader")
        
        # 确保下载目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 默认配置
        self.config = {
            "quality": 32,  # 视频质量：32=480P
            "with_audio": True,  # 是否下载音频
            "concurrent_limit": 3,  # 并发下载数量
            "retry_times": 5,  # 下载失败重试次数
            "timeout": 60,  # 下载超时时间(秒)
            "chunk_size": 1024 * 1024,  # 分块下载大小(字节)
            "filename_format": "{bvid}.mp4",  # 文件命名格式
            "aria2c_args": [
                "--max-concurrent-downloads=3",
                "--split=10",
                "--min-split-size=10M",
                "--max-connection-per-server=10",
                "--max-tries=3",
                "--retry-wait=3",
                "--timeout=30",
            ],
            "use_external_downloader": False,  # 是否使用外部下载器
            "external_downloader": "aria2c",  # 外部下载器命令
            "check_network_before_download": True,  # 下载前检查网络连接
            "network_test_timeout": 10,  # 网络检测超时时间(秒)
            "test_servers": [  # 网络测试服务器
                "api.bilibili.com",
                "upos-sz-mirrorhw.bilivideo.com",
                "cn-hbxy-cm-01-15.bilivideo.com"
            ],
            "retry_strategy": {
                "base_delay": 2,  # 基础延迟(秒)
                "max_delay": 60,  # 最大延迟(秒)
                "factor": 2,  # 延迟增长因子
                "jitter": 0.1  # 随机抖动系数
            },
            "error_tracking": {
                "track_failed_hosts": True,  # 记录失败的主机
                "host_recovery_time": 300,  # 主机恢复时间(秒)
                "failed_hosts": {}  # 记录失败的主机及失败时间
            },
            "download_stats": {
                "enable": True,  # 启用下载统计
                "stats": {}  # 统计数据
            },
            "anti_spider": {
                "enable": True,
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ],
                "rotate_interval": 300,
                "request_delay": [2.0, 5.0]
            }
        }
        
        # 更新配置
        if config and isinstance(config, dict):
            self._update_config(self.config, config)
        
        # 并发锁
        self.semaphore = asyncio.Semaphore(self.config["concurrent_limit"])
        
        # 失败主机集合
        self.failed_hosts = self.config["error_tracking"]["failed_hosts"]
        
        # 下载统计
        self.download_stats = self.config["download_stats"]["stats"]
        
        # 反爬虫相关
        self.current_user_agent_index = 0
        self.last_user_agent_rotation = time.time()
        self.last_request_time = 0
            
    def _update_config(self, base_config, new_config):
        """递归更新配置"""
        for key, value in new_config.items():
            if key in base_config and isinstance(value, dict) and isinstance(base_config[key], dict):
                self._update_config(base_config[key], value)
            else:
                base_config[key] = value
                
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，去除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 处理后的文件名
        """
        # 替换Windows文件名中的非法字符
        illegal_chars = r'[\\/*?:"<>|]'
        sanitized = re.sub(illegal_chars, "_", filename)
        
        # 限制文件名长度（Windows路径限制）
        if len(sanitized) > 100:
            # 保留BV号和扩展名，截断标题
            parts = sanitized.split('_', 1)
            if len(parts) == 2:
                bvid = parts[0]
                title_and_ext = parts[1]
                # 分离扩展名
                if '.' in title_and_ext:
                    title, ext = title_and_ext.rsplit('.', 1)
                    # 截断标题，保留BV号和扩展名
                    max_title_len = 100 - len(bvid) - len(ext) - 5  # 5个字符用于分隔符和省略号
                    if len(title) > max_title_len:
                        title = title[:max_title_len] + "..."
                    sanitized = f"{bvid}_{title}.{ext}"
                else:
                    # 没有扩展名的情况
                    max_title_len = 100 - len(bvid) - 4  # 4个字符用于分隔符和省略号
                    if len(title_and_ext) > max_title_len:
                        title_and_ext = title_and_ext[:max_title_len] + "..."
                    sanitized = f"{bvid}_{title_and_ext}"
            else:
                # 如果没有下划线分隔，直接截断
                sanitized = sanitized[:97] + "..."
            
        return sanitized
    
    def _format_filename(self, info: Dict[str, Any]) -> str:
        """
        格式化文件名
        
        Args:
            info: 视频信息字典
            
        Returns:
            str: 格式化后的文件名
        """
        filename = self.config["filename_format"].format(
            bvid=info.get("bvid", ""),
            aid=info.get("aid", ""),
            title=info.get("title", ""),
            upload_time=time.strftime(
                "%Y%m%d", 
                time.localtime(info.get("pubdate", 0) or time.time())
            )
        )
        
        return self._sanitize_filename(filename)
            
    async def download_video(self, bvid: str) -> Tuple[str, int]:
        """
        下载视频
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Tuple[str, int]: (保存路径, 文件大小(字节))
            
        Raises:
            NetworkError: 网络连接错误
            VideoStreamError: 视频流错误
            AudioStreamError: 音频流错误
            MergeError: 合并错误
            RetryExceededError: 超过最大重试次数
            InfoFetchError: 获取视频信息失败
            DiskSpaceError: 磁盘空间不足
            ExternalToolError: 外部工具错误
        """
        # 初始化统计
        if self.config["download_stats"]["enable"]:
            self.download_stats[bvid] = {
                "start_time": time.time(),
                "status": "pending",
                "retries": 0,
                "size": 0,
                "error": None
            }
            
        async with self.semaphore:
            # 检查网络状态
            if self.config["check_network_before_download"]:
                if not await self._check_network():
                    error_msg = "下载前网络连接检查失败，请检查网络设置"
                    if self.config["download_stats"]["enable"]:
                        self.download_stats[bvid]["status"] = "failed"
                        self.download_stats[bvid]["error"] = error_msg
                    raise NetworkError(error_msg, bvid)
                    
            return await self._download_video(bvid)
            
    async def _check_network(self) -> bool:
        """
        检查网络连接
        
        Returns:
            bool: 网络是否连接正常
        """
        self.logger.info("检查网络连接...")
        timeout = self.config["network_test_timeout"]
        
        # 简化的网络检查：只测试TCP连接
        for server in self.config["test_servers"]:
            try:
                self.logger.debug(f"测试连接到 {server}...")
                
                # 使用asyncio创建TCP连接
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(server, 443),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                
                self.logger.info(f"网络连接正常，可以访问: {server}")
                return True
                
            except (asyncio.TimeoutError, socket.error) as e:
                self.logger.warning(f"连接服务器 {server} 失败: {str(e)}")
                continue
        
        # 如果所有服务器都连接失败，尝试连接通用的DNS服务器
        try:
            self.logger.debug("尝试连接到公共DNS服务器...")
            _, writer = await asyncio.wait_for(
                asyncio.open_connection("8.8.8.8", 53),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            
            self.logger.info("网络连接正常（通过DNS服务器验证）")
            return True
            
        except Exception as e:
            self.logger.error(f"网络连接检查失败: {str(e)}")
            return False

    async def _download_video(self, bvid: str) -> Tuple[str, int]:
        """
        内部下载视频实现
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Tuple[str, int]: (保存路径, 文件大小(字节))
        """
        self.logger.info(f"开始下载视频: {bvid}")
        
        # 设置bilibili-api网络配置
        self._setup_bilibili_api_settings()
        
        # 应用反爬虫延迟
        await self._apply_request_delay()
        
        try:
            # 创建视频对象
            v = video.Video(bvid=bvid, credential=self.credential)
            
            # 获取视频信息
            info = await v.get_info()
            
            # 格式化文件名
            filename = self._format_filename(info)
            save_path = os.path.join(self.save_dir, filename)
            
            # 检查文件是否已存在
            if os.path.exists(save_path):
                size = os.path.getsize(save_path)
                self.logger.info(f"视频已存在: {save_path}, 大小: {size/1024/1024:.2f}MB，跳过下载")
                if self.config["download_stats"]["enable"]:
                    self.download_stats[bvid]["status"] = "exists"
                    self.download_stats[bvid]["size"] = size
                return save_path, size
            
            # 获取视频下载流（默认第一个分P）
            download_url_data = await v.get_download_url(page_index=0)
            
            # 检查视频是否可以下载
            if not download_url_data:
                error_msg = f"无法获取视频下载链接: {bvid}"
                self.logger.error(error_msg)
                if self.config["download_stats"]["enable"]:
                    self.download_stats[bvid]["status"] = "failed"
                    self.download_stats[bvid]["error"] = error_msg
                raise VideoStreamError(error_msg, bvid)
            
            # 解析视频下载信息
            detecter = video.VideoDownloadURLDataDetecter(data=download_url_data)
            
            # 根据配置的质量选择流
            quality_map = {
                16: video.VideoQuality._360P,
                32: video.VideoQuality._480P,
                64: video.VideoQuality._720P,
                80: video.VideoQuality._1080P,
                112: video.VideoQuality._1080P_PLUS,
                116: video.VideoQuality._1080P_60,
                120: video.VideoQuality._4K,
            }
            
            max_quality = quality_map.get(self.config["quality"], video.VideoQuality._480P)
            
            # 检测最佳流
            streams = detecter.detect_best_streams(
                video_max_quality=max_quality,
                audio_max_quality=video.AudioQuality._192K,
                no_dolby_audio=True,
                no_dolby_video=True,
                no_hdr=True,
                no_hires=True
            )
            
            if not streams:
                error_msg = f"没有可用的视频流: {bvid}"
                self.logger.error(error_msg)
                if self.config["download_stats"]["enable"]:
                    self.download_stats[bvid]["status"] = "failed"
                    self.download_stats[bvid]["error"] = error_msg
                raise VideoStreamError(error_msg, bvid)
            
            # 检查流类型：FLV/MP4流 vs DASH流
            if detecter.check_flv_mp4_stream():
                # FLV流或MP4流：音视频合并
                if streams[0] is None:
                    error_msg = f"视频流不可用: {bvid}"
                    self.logger.error(error_msg)
                    raise VideoStreamError(error_msg, bvid)
                
                video_url = streams[0].url
                audio_url = None  # FLV/MP4流已包含音频
                
                self.logger.info(f"检测到FLV/MP4流 - 质量: {getattr(streams[0], 'video_quality', '未知')}")
            else:
                # DASH流：音视频分离
                if len(streams) < 2 or streams[0] is None:
                    error_msg = f"视频流不可用: {bvid}"
                    self.logger.error(error_msg)
                    raise VideoStreamError(error_msg, bvid)
                
                video_url = streams[0].url
                audio_url = streams[1].url if self.config["with_audio"] and len(streams) > 1 and streams[1] else None
                
                self.logger.info(f"检测到DASH流 - 视频: {getattr(streams[0], 'video_quality', '未知')}, 音频: {getattr(streams[1], 'audio_quality', '未知') if audio_url else '无'}")
            
            # 临时文件路径
            temp_video = f"{save_path}.video.temp"
            temp_audio = f"{save_path}.audio.temp" if audio_url else None
            
            try:
                # 使用外部下载器或内置下载器
                if self.config["use_external_downloader"]:
                    if await self._download_with_external(video_url, temp_video, audio_url, temp_audio, save_path, bvid=bvid):
                        size = os.path.getsize(save_path)
                        self.logger.info(f"外部下载完成: {save_path}, 大小: {size/1024/1024:.2f}MB")
                        if self.config["download_stats"]["enable"]:
                            self.download_stats[bvid]["status"] = "success"
                            self.download_stats[bvid]["size"] = size
                            self.download_stats[bvid]["end_time"] = time.time()
                        return save_path, size
                else:
                    # 下载视频流
                    try:
                        await self._download_stream(video_url, temp_video, bvid=bvid)
                    except Exception as e:
                        self.logger.error(f"下载视频流失败 ({bvid}): {str(e)}")
                        if self.config["download_stats"]["enable"]:
                            self.download_stats[bvid]["error"] = f"视频流下载失败: {str(e)}"
                        raise VideoStreamError(f"视频流下载失败: {str(e)}", bvid) from e
                    
                    # 下载音频流
                    if audio_url:
                        try:
                            await self._download_stream(audio_url, temp_audio, bvid=bvid)
                        except Exception as e:
                            self.logger.error(f"下载音频流失败 ({bvid}): {str(e)}")
                            if self.config["download_stats"]["enable"]:
                                self.download_stats[bvid]["error"] = f"音频流下载失败: {str(e)}"
                            raise AudioStreamError(f"音频流下载失败: {str(e)}", bvid) from e
                    
                    # 处理不同类型的流
                    if not detecter.check_flv_mp4_stream() and audio_url:
                        # DASH流：需要合并视频和音频
                        try:
                            await self._merge_video_audio(temp_video, temp_audio, save_path, bvid=bvid)
                        except MergeError as me: # 捕获特定的 MergeError
                            self.logger.error(f"合并视频和音频失败 ({bvid}): {str(me)}")
                            if self.config["download_stats"]["enable"]:
                                self.download_stats[bvid]["error"] = f"合并失败: {str(me)}"
                            raise # 直接重新抛出原始的 MergeError
                        except ExternalToolError as ete: # 捕获特定的 ExternalToolError
                            self.logger.error(f"合并时外部工具错误 ({bvid}): {str(ete)}")
                            if self.config["download_stats"]["enable"]:
                                self.download_stats[bvid]["error"] = f"合并时外部工具错误: {str(ete)}"
                            raise # 直接重新抛出原始的 ExternalToolError
                        except Exception as e: # 其他意外错误
                            self.logger.error(f"合并视频和音频时发生未知错误 ({bvid}): {str(e)}")
                            self.logger.debug(traceback.format_exc())
                            if self.config["download_stats"]["enable"]:
                                self.download_stats[bvid]["error"] = f"合并时未知错误: {str(e)}"
                            raise MergeError(f"合并视频和音频时发生未知错误: {str(e)}", bvid=bvid) from e
                    else:
                        # FLV/MP4流或无音频：直接重命名视频文件
                        os.rename(temp_video, save_path)
                
                # 删除临时文件
                self._clean_temp_files(temp_video, temp_audio)
                
                # 获取文件大小
                size = os.path.getsize(save_path)
                self.logger.info(f"下载完成: {save_path}, 大小: {size/1024/1024:.2f}MB")
                
                if self.config["download_stats"]["enable"]:
                    self.download_stats[bvid]["status"] = "success"
                    self.download_stats[bvid]["size"] = size
                    self.download_stats[bvid]["end_time"] = time.time()
                    
                return save_path, size
                
            except Exception as e:
                self.logger.error(f"下载过程中出错: {str(e)}")
                # 清理临时文件
                self._clean_temp_files(temp_video, temp_audio)
                if self.config["download_stats"]["enable"]:
                    self.download_stats[bvid]["error"] = str(e)
                raise
            
        except Exception as e:
            self.logger.error(f"下载视频失败: {bvid}, 错误: {str(e)}")
            if self.config["download_stats"]["enable"]:
                self.download_stats[bvid]["status"] = "failed"
                self.download_stats[bvid]["error"] = str(e)
                self.download_stats[bvid]["end_time"] = time.time()
            raise
    
    async def _download_stream(self, url: str, filepath: str, bvid: Optional[str] = None) -> None:
        """
        下载流到文件
        
        Args:
            url: 下载URL
            filepath: 保存路径
            
        Raises:
            NetworkError: 网络连接错误
            RetryExceededError: 超过最大重试次数
        """
        # 从URL提取主机名
        host = self._extract_host_from_url(url)
        
        # 应用反爬虫延迟
        await self._apply_request_delay()
        
        # 检查主机是否在失败列表中
        if self.config["error_tracking"]["track_failed_hosts"] and host in self.failed_hosts:
            failure_time = self.failed_hosts[host]
            recovery_time = self.config["error_tracking"]["host_recovery_time"]
            elapsed = time.time() - failure_time
            
            if elapsed < recovery_time:
                wait_time = recovery_time - elapsed
                self.logger.warning(f"主机 {host} 最近下载失败，等待 {wait_time:.0f} 秒后重试")
                await asyncio.sleep(min(wait_time, 10))  # 最多等待10秒
        
        headers = {
            "User-Agent": self._get_current_user_agent(),
            "Referer": "https://www.bilibili.com",
        }
        
        # 创建临时文件的目录
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 获取文件大小信息
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=headers) as response:
                    total_size = int(response.headers.get("content-length", 0))
        except Exception as e:
            raise NetworkError(f"无法获取文件大小信息: {str(e)}", bvid=bvid, host=host)
                
        # 检查是否支持断点续传
        resume_size = 0
        if os.path.exists(filepath):
            resume_size = os.path.getsize(filepath)
            if resume_size >= total_size:
                self.logger.info(f"文件已完整下载: {filepath}")
                return
        
        # 设置断点续传的头部
        if resume_size > 0:
            headers["Range"] = f"bytes={resume_size}-"
            self.logger.info(f"断点续传: {filepath}, 已下载: {resume_size/1024/1024:.2f}MB, 总大小: {total_size/1024/1024:.2f}MB")
        
        # 下载文件
        retry_count = 0
        last_error = None
        
        while retry_count < self.config["retry_times"]:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=self.config["timeout"]) as response:
                        if response.status != 200 and response.status != 206:
                            self.logger.warning(f"下载失败，状态码: {response.status}，尝试重试...")
                            retry_count += 1
                            await self._wait_before_retry(retry_count)
                            continue
                        
                        # 打开文件进行写入
                        async with aiofiles.open(filepath, "ab" if resume_size > 0 else "wb") as f:
                            # 计算进度
                            downloaded = resume_size
                            chunk_size = self.config["chunk_size"]
                            
                            # 分块下载
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 打印进度
                                if total_size > 0:
                                    progress = downloaded / total_size * 100
                                    self.logger.debug(f"下载进度: {progress:.2f}%, {downloaded/1024/1024:.2f}MB/{total_size/1024/1024:.2f}MB")
                        
                        # 下载完成
                        if host in self.failed_hosts:
                            del self.failed_hosts[host]  # 移除失败记录
                        return
                        
            except asyncio.TimeoutError as e:
                self.logger.warning(f"下载超时，尝试重试...")
                last_error = e
                retry_count += 1
                # 记录失败的主机
                if self.config["error_tracking"]["track_failed_hosts"] and host:
                    self.failed_hosts[host] = time.time()
                
                # 如果是ContentLengthError，增加额外延迟
                if "ContentLengthError" in str(e) or "Not enough data" in str(e):
                    extra_delay = random.uniform(5.0, 15.0)
                    self.logger.warning(f"检测到ContentLengthError，增加额外延迟: {extra_delay:.2f}秒")
                    await asyncio.sleep(extra_delay)
                
                await self._wait_before_retry(retry_count)
                continue
                
            except Exception as e:
                self.logger.error(f"下载出错: {str(e)}，尝试重试...")
                last_error = e
                retry_count += 1
                # 记录失败的主机
                if self.config["error_tracking"]["track_failed_hosts"] and host:
                    self.failed_hosts[host] = time.time()
                
                # 如果是ContentLengthError，增加额外延迟
                if "ContentLengthError" in str(e) or "Not enough data" in str(e):
                    extra_delay = random.uniform(5.0, 15.0)
                    self.logger.warning(f"检测到ContentLengthError，增加额外延迟: {extra_delay:.2f}秒")
                    await asyncio.sleep(extra_delay)
                
                await self._wait_before_retry(retry_count)
                continue
        
        # 检查是否下载成功
        if retry_count >= self.config["retry_times"]:
            error_msg = f"下载失败，已达到最大重试次数: {self.config['retry_times']}"
            if last_error:
                error_msg += f", 最后错误: {str(last_error)}"
            raise RetryExceededError(error_msg, bvid=bvid, retry_count=self.config["retry_times"])
    
    async def _wait_before_retry(self, retry_count: int) -> None:
        """
        使用指数退避算法计算重试等待时间
        
        Args:
            retry_count: 当前重试次数
        """
        strategy = self.config["retry_strategy"]
        base_delay = strategy["base_delay"]
        max_delay = strategy["max_delay"]
        factor = strategy["factor"]
        jitter = strategy["jitter"]
        
        # 计算基础等待时间
        delay = min(base_delay * (factor ** (retry_count - 1)), max_delay)
        
        # 添加随机抖动
        if jitter > 0:
            delay = delay * (1 + random.uniform(-jitter, jitter))
            
        self.logger.info(f"将在 {delay:.2f} 秒后进行第 {retry_count + 1} 次重试...")
        await asyncio.sleep(delay)
    
    def _extract_host_from_url(self, url: str) -> Optional[str]:
        """
        从URL中提取主机名
        
        Args:
            url: URL字符串
            
        Returns:
            str: 主机名
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None
    
    async def _download_with_external(self, video_url: str, temp_video: str, audio_url: Optional[str], temp_audio: Optional[str], save_path: str, bvid: Optional[str] = None) -> bool:
        """
        使用外部下载器下载
        
        Args:
            video_url: 视频URL
            temp_video: 视频临时文件路径
            audio_url: 音频URL
            temp_audio: 音频临时文件路径
            save_path: 最终保存路径
            
        Returns:
            bool: 是否下载成功
            
        Raises:
            ExternalToolError: 外部工具错误
            MergeError: 合并错误
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            if self.config["external_downloader"] == "aria2c":
                # 使用aria2c下载器
                
                # 下载视频
                cmd = [
                    "aria2c",
                    *self.config["aria2c_args"],
                    "-o", os.path.basename(temp_video),
                    "-d", os.path.dirname(temp_video),
                    "--header=Referer: https://www.bilibili.com",
                    "--header=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    video_url
                ]
                
                self.logger.info(f"使用aria2c下载视频流: {' '.join(cmd)}")
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode()
                    self.logger.error(f"aria2c下载视频失败: {error_msg}")
                    raise ExternalToolError(f"下载视频失败: {error_msg}", bvid=bvid, tool="aria2c", cmd=" ".join(cmd))
                
                # 下载音频
                if audio_url:
                    cmd = [
                        "aria2c",
                        *self.config["aria2c_args"],
                        "-o", os.path.basename(temp_audio),
                        "-d", os.path.dirname(temp_audio),
                        "--header=Referer: https://www.bilibili.com",
                        "--header=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        audio_url
                    ]
                    
                    self.logger.info(f"使用aria2c下载音频流: {' '.join(cmd)}")
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        error_msg = stderr.decode()
                        self.logger.error(f"aria2c下载音频失败: {error_msg}")
                        raise ExternalToolError(f"下载音频失败: {error_msg}", bvid=bvid, tool="aria2c", cmd=" ".join(cmd))
                    
                    # 合并视频和音频
                    await self._merge_video_audio(temp_video, temp_audio, save_path, bvid=bvid)
                else:
                    # 如果没有音频，直接重命名视频文件
                    os.rename(temp_video, save_path)
                
                return True
                
            else:
                error_msg = f"不支持的外部下载器: {self.config['external_downloader']}"
                self.logger.error(error_msg)
                raise ExternalToolError(error_msg, bvid=bvid, tool=self.config['external_downloader'])
                
        except (MergeError, ExternalToolError):
            raise
        except Exception as e:
            self.logger.error(f"外部下载器出错 ({bvid}): {str(e)}")
            raise ExternalToolError(f"外部下载器出错: {str(e)}", bvid=bvid, tool=self.config['external_downloader'])
    
    async def _merge_video_audio(self, video_path: str, audio_path: str, output_path: str, bvid: Optional[str] = None) -> None:
        """
        合并视频和音频
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 输出文件路径
            bvid: BV号，用于日志和异常记录
            
        Raises:
            MergeError: 合并错误
            ExternalToolError: 外部工具错误
        """
        cmd_to_log_str = "ffmpeg merge command" # 用于记录实际执行的命令的字符串形式
        ffmpeg_executable = r"D:\Program\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe" # FFmpeg 可执行文件完整路径
        try:
            # 检查输入文件是否存在
            if not os.path.exists(video_path):
                raise MergeError(f"视频文件不存在: {video_path}", bvid=bvid)
            if not os.path.exists(audio_path):
                raise MergeError(f"音频文件不存在: {audio_path}", bvid=bvid)

            video_size = os.path.getsize(video_path)
            audio_size = os.path.getsize(audio_path)
            # self.logger.info(f"输入文件大小 ({bvid}) - 视频: {video_size/1024/1024:.2f}MB, 音频: {audio_size/1024/1024:.2f}MB")

            if video_size == 0:
                raise MergeError(f"视频文件为空: {video_path}", bvid=bvid)
            if audio_size == 0:
                raise MergeError(f"音频文件为空: {audio_path}", bvid=bvid)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            ffmpeg_version_info = "(version not checked)"
            version_check_failed = False
            try:
                # 使用同步subprocess避免Windows上的NotImplementedError
                import subprocess
                proc_version = subprocess.run(
                    [ffmpeg_executable, "-version"],
                    capture_output=True, text=True, timeout=10
                )
                if proc_version.returncode == 0:
                    ffmpeg_version_info = proc_version.stdout.split('\n')[0].strip()
                else:
                    ffmpeg_version_info = f"(failed to get version: exit code {proc_version.returncode}, stderr: {proc_version.stderr.strip()})"
                    self.logger.warning(f"FFmpeg version check failed for BVID {bvid}: {ffmpeg_version_info}")
                    version_check_failed = True
            except FileNotFoundError:
                self.logger.error(f"FFmpeg command '{ffmpeg_executable}' not found during version check for BVID {bvid}. Ensure FFmpeg is installed and '{ffmpeg_executable}' is in your system PATH.")
                raise ExternalToolError(f"FFmpeg command '{ffmpeg_executable}' not found. Please ensure FFmpeg is installed and in your system PATH.", bvid=bvid, tool=ffmpeg_executable, cmd=f"{ffmpeg_executable} -version")
            except Exception as ve:
                self.logger.warning(f"FFmpeg version check encountered an error for BVID {bvid}: {str(ve)} (type: {type(ve).__name__})")
                self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                ffmpeg_version_info = f"(error checking version: {str(ve)})"
                version_check_failed = True

            # self.logger.info(f"Using FFmpeg {ffmpeg_version_info} for merging ({bvid})")
            # 如果版本检查失败，记录警告但继续尝试合并
            if version_check_failed:
                self.logger.warning(f"FFmpeg version check failed, but will attempt merge operation for BVID {bvid}")

            # self.logger.info(f"FFmpeg input files ({bvid}): Video='{video_path}', Audio='{audio_path}'")
            # self.logger.info(f"FFmpeg output target ({bvid}): '{output_path}'")

            import tempfile
            from pathlib import Path # 确保 Path 被导入
            with tempfile.TemporaryDirectory(prefix=f"bili_merge_{bvid}_") as temp_dir:
                temp_output_filename = f"merged_{Path(output_path).name}"
                temp_output = os.path.join(temp_dir, temp_output_filename)
                # self.logger.info(f"FFmpeg temporary output ({bvid}): '{temp_output}'")

                # 构建FFmpeg命令
                cmd = [
                    ffmpeg_executable,  # 使用完整路径
                    "-i", video_path,
                    "-i", audio_path,
                    "-c", "copy",
                    "-y",  # 覆盖输出文件
                    "-loglevel", "error",  # 只显示错误信息
                    temp_output
                ]
                cmd_to_log_str = " ".join(cmd)  # 更新为实际命令

                # self.logger.info(f"合并命令 ({bvid}): {cmd_to_log_str}")

                # 使用同步subprocess避免Windows上的NotImplementedError
                try:
                    process = subprocess.run(
                        cmd,
                        capture_output=True, text=True, timeout=300  # 5分钟超时
                    )
                    stdout_text = process.stdout.strip() if process.stdout else "(stdout was None)"
                    stderr_text = process.stderr.strip() if process.stderr else "(stderr was None)"
                except subprocess.TimeoutExpired:
                    raise MergeError(f"FFmpeg合并超时 (超过300秒)", bvid=bvid)
                except Exception as e:
                    raise ExternalToolError(f"执行FFmpeg命令时出错: {str(e)}", bvid=bvid, tool="ffmpeg", cmd=cmd_to_log_str) from e

                if not os.path.exists(temp_output):
                    raise MergeError(f"FFmpeg执行成功但未生成输出文件: {temp_output}", bvid=bvid)

                output_size = os.path.getsize(temp_output)
                if output_size == 0:
                    raise MergeError(f"FFmpeg生成的输出文件为空: {temp_output}", bvid=bvid)

                # self.logger.info(f"合并成功 ({bvid})，临时输出文件大小: {output_size/1024/1024:.2f}MB")

                shutil.move(temp_output, output_path)
                # self.logger.info(f"视频合并完成 ({bvid}): {output_path}")

        except MergeError:
            raise
        except ExternalToolError:
            raise
        except Exception as e:
            self.logger.error(f"合并视频和音频时发生意外错误 ({bvid}): {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise ExternalToolError(f"合并视频和音频时发生意外错误 ({bvid}): {str(e)}", bvid=bvid, tool="ffmpeg", cmd=cmd_to_log_str) from e
    
    def _clean_temp_files(self, *filepaths: str) -> None:
        """
        清理临时文件
        
        Args:
            *filepaths: 文件路径列表
        """
        for filepath in filepaths:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    self.logger.debug(f"已删除临时文件: {filepath}")
                except Exception as e:
                    self.logger.warning(f"删除临时文件失败: {filepath}, 错误: {str(e)}")
        
        # 额外清理：查找并删除可能遗留的.temp文件
        try:
            for filename in os.listdir(self.save_dir):
                if filename.endswith('.temp'):
                    temp_file_path = os.path.join(self.save_dir, filename)
                    try:
                        # 检查文件是否超过1小时未修改（避免删除正在使用的临时文件）
                        if os.path.exists(temp_file_path):
                            file_mtime = os.path.getmtime(temp_file_path)
                            current_time = time.time()
                            if current_time - file_mtime > 3600:  # 1小时
                                os.remove(temp_file_path)
                                self.logger.info(f"清理遗留的临时文件: {temp_file_path}")
                    except Exception as e:
                        self.logger.warning(f"清理遗留临时文件失败: {temp_file_path}, 错误: {str(e)}")
        except Exception as e:
            self.logger.debug(f"扫描临时文件时出错: {str(e)}")
    
    def get_download_stats(self) -> Dict[str, Any]:
        """
        获取下载统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.config["download_stats"]["enable"]:
            return {}
            
        stats = {
            "total": len(self.download_stats),
            "success": 0,
            "failed": 0,
            "pending": 0,
            "exists": 0,
            "total_size_mb": 0,
            "avg_time_success": 0,
            "details": self.download_stats
        }
        
        success_time = 0
        success_count = 0
        
        for bvid, info in self.download_stats.items():
            status = info.get("status", "pending")
            
            if status == "success":
                stats["success"] += 1
                stats["total_size_mb"] += info.get("size", 0) / 1024 / 1024
                
                if "start_time" in info and "end_time" in info:
                    time_taken = info["end_time"] - info["start_time"]
                    success_time += time_taken
                    success_count += 1
                    
            elif status == "failed":
                stats["failed"] += 1
            elif status == "pending":
                stats["pending"] += 1
            elif status == "exists":
                stats["exists"] += 1
                stats["total_size_mb"] += info.get("size", 0) / 1024 / 1024
        
        if success_count > 0:
            stats["avg_time_success"] = success_time / success_count
            
        return stats
        
    async def batch_download(self, bvids: List[str]) -> Dict[str, Any]:
        """
        批量下载多个视频
        
        Args:
            bvids: 视频BV号列表
            
        Returns:
            Dict[str, Any]: 下载结果统计
        """
        self.logger.info(f"开始批量下载 {len(bvids)} 个视频")
        
        tasks = []
        for bvid in bvids:
            task = asyncio.create_task(self._safe_download(bvid))
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
        
        # 统计结果
        stats = {
            "total": len(bvids),
            "success": 0,
            "failed": 0,
            "exists": 0,
            "total_size_mb": 0,
            "failed_bvids": []
        }
        
        for result in results:
            if result["status"] == "success":
                stats["success"] += 1
                stats["total_size_mb"] += result["size"] / 1024 / 1024
            elif result["status"] == "exists":
                stats["exists"] += 1
                stats["total_size_mb"] += result["size"] / 1024 / 1024
            elif result["status"] == "failed":
                stats["failed"] += 1
                stats["failed_bvids"].append({
                    "bvid": result["bvid"],
                    "error": result["error"]
                })
                
        self.logger.info(f"批量下载完成，成功: {stats['success']}，已存在: {stats['exists']}，失败: {stats['failed']}")
        return stats
        
    async def _safe_download(self, bvid: str) -> Dict[str, Any]:
        """
        安全下载单个视频，不抛出异常
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Dict[str, Any]: 下载结果
        """
        result = {
            "bvid": bvid,
            "status": "failed",
            "size": 0,
            "path": "",
            "error": ""
        }
        
        try:
            path, size = await self.download_video(bvid)
            result["status"] = "success"
            result["size"] = size
            result["path"] = path
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"下载视频 {bvid} 时出错: {str(e)}")
        
        return result

    def _get_current_user_agent(self) -> str:
        """
        获取当前User-Agent，支持轮换
        
        Returns:
            str: User-Agent字符串
        """
        anti_spider_config = self.config.get("anti_spider", {})
        if not anti_spider_config.get("enable", False):
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        user_agents = anti_spider_config.get("user_agents", [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ])
        
        # 检查是否需要轮换User-Agent
        rotate_interval = anti_spider_config.get("rotate_interval", 300)
        current_time = time.time()
        
        if current_time - self.last_user_agent_rotation > rotate_interval:
            self.current_user_agent_index = (self.current_user_agent_index + 1) % len(user_agents)
            self.last_user_agent_rotation = current_time
            self.logger.debug(f"轮换User-Agent到索引: {self.current_user_agent_index}")
        
        return user_agents[self.current_user_agent_index]
    
    async def _apply_request_delay(self) -> None:
        """
        应用请求间延迟，避免请求过于频繁
        """
        anti_spider_config = self.config.get("anti_spider", {})
        if not anti_spider_config.get("enable", False):
            return
        
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        delay_range = anti_spider_config.get("request_delay", [2.0, 5.0])
        min_delay, max_delay = delay_range
        required_delay = random.uniform(min_delay, max_delay)
        
        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            self.logger.debug(f"应用反爬虫延迟: {wait_time:.2f}秒")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _setup_bilibili_api_settings(self) -> None:
        """
        设置bilibili-api库的网络配置
        """
        try:
            from bilibili_api import request_settings
            
            # 设置超时
            timeout = self.config.get("timeout", 60)
            request_settings.set_timeout(timeout)
            
            # 设置重试次数
            retry_times = self.config.get("retry_times", 3)
            request_settings.set_wbi_retry_times(retry_times)
            
            self.logger.debug("bilibili-api网络设置已配置")
            
        except ImportError:
            self.logger.warning("无法导入bilibili_api.request_settings，跳过API设置")
        except Exception as e:
            self.logger.warning(f"设置bilibili-api网络配置失败: {str(e)}")


# 简单测试代码
if __name__ == "__main__":
    import sys
    import argparse
    
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="哔哩哔哩视频下载器")
    parser.add_argument("bvids", nargs="*", help="要下载的视频BV号，可指定多个")
    parser.add_argument("--quality", type=int, default=32, help="视频质量：32=480P，64=720P")
    parser.add_argument("--out", type=str, default="output", help="保存目录")
    parser.add_argument("--no-audio", action="store_true", help="不下载音频")
    parser.add_argument("--retry", type=int, default=5, help="重试次数")
    parser.add_argument("--concurrent", type=int, default=3, help="并发下载数量")
    parser.add_argument("--debug", action="store_true", help="显示调试日志")
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    async def test():
        # 从命令行获取视频BV号列表
        bvids = args.bvids if args.bvids else ["BV1GJ411x7h7"]  # 默认一个示例视频
        
        # 初始化下载器配置
        config = {
            "quality": args.quality,
            "with_audio": not args.no_audio,
            "concurrent_limit": args.concurrent,
            "retry_times": args.retry
        }
        
        # 使用无登录凭证方式
        downloader = BiliDownloader(Credential(), save_dir=args.out, config=config)
        
        if len(bvids) == 1:
            # 下载单个视频
            save_path, size = await downloader.download_video(bvids[0])
            print(f"视频已下载到: {save_path}")
            print(f"文件大小: {size/1024/1024:.2f}MB")
        else:
            # 批量下载
            results = await downloader.batch_download(bvids)
            print(f"批量下载结果:")
            print(f"  总数: {results['total']}")
            print(f"  成功: {results['success']}")
            print(f"  已存在: {results['exists']}")
            print(f"  失败: {results['failed']}")
            print(f"  总大小: {results['total_size_mb']:.2f}MB")
            
            if results['failed'] > 0:
                print("失败的视频:")
                for failed in results['failed_bvids']:
                    print(f"  {failed['bvid']}: {failed['error']}")
        
        # 显示下载统计
        if downloader.config["download_stats"]["enable"]:
            stats = downloader.get_download_stats()
            print("\n下载统计:")
            print(f"  总视频数: {stats['total']}")
            print(f"  成功下载: {stats['success']}")
            print(f"  下载失败: {stats['failed']}")
            print(f"  已存在跳过: {stats['exists']}")
            print(f"  总下载大小: {stats['total_size_mb']:.2f}MB")
            if stats['success'] > 0:
                print(f"  平均下载时间: {stats['avg_time_success']:.2f}秒")
    
    asyncio.run(test()) 