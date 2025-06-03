#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

用于加载和管理项目配置，支持从JSON文件加载配置，
并提供默认配置值。

作者: Claude
日期: 2025-05-23
"""

import os
import json
from pathlib import Path


# 默认配置
DEFAULT_CONFIG = {
    # 路径配置
    "paths": {
        "data_dir": "data",                   # 数据根目录
        "logs_dir": "logs",                   # 日志目录
        "metadata_dir": "data/json",          # 元数据目录
        "videos_dir": "data/videos",          # 视频文件目录
        "config_dir": "config"                # 配置文件目录
    },
    
    # 登录相关配置
    "login": {
        "use_cookie": False,                 # 是否使用已有Cookie
        "cookie_file": "config/cookies.json", # Cookie文件路径
        "qrcode_in_terminal": True,          # 是否在终端显示二维码
        "credential_file": "config/credential.json", # 凭证保存路径
        "verify_timeout": 60,                # 验证超时时间(秒)
        "max_retries": 3,                    # 最大重试次数
        "retry_interval": 5,                 # 重试间隔(秒)
        "check_network": True,               # 是否检查网络连接
        "network_timeout": 10,               # 网络检查超时(秒)
        "test_servers": [                    # 测试服务器列表
            "api.bilibili.com", 
            "passport.bilibili.com",
            "www.bilibili.com"
        ]
    },
    
    # 搜索相关配置
    "search": {
        "keywords": ["测试"],                 # 默认搜索关键词
        "limit_per_keyword": 100,            # 每个关键词的视频数量限制
        "page_size": 30,                     # 每页结果数
        "order_type": "pubdate",             # 排序方式：默认为发布日期
        "search_type": 0,                    # 搜索类型：0=视频
        "duration_type": 0,                  # 视频时长筛选：0=全部时长
        "tids": 0,                           # 分区ID：0=全部分区
        "min_duration": 30,                  # 最短视频时长(秒)
        "max_duration": 600                  # 最长视频时长(秒)
    },
    
    # 爬虫相关配置
    "crawler": {
        "max_retries": 3,                    # 最大重试次数
        "request_interval": 1.5,             # 请求间隔秒数
        "random_offset": 0.5,                # 随机偏移量(秒)
        "timeout": 30,                       # 请求超时时间(秒)
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "info_only": False,                  # 是否仅爬取信息不下载
        "include_comments": False,           # 是否包含评论数据
        "include_danmaku": False,            # 是否包含弹幕数据
    },
    
    # 下载器相关配置
    "downloader": {
        "default_quality": 32,               # 视频质量：32=480P
        "with_audio": True,                  # 是否下载音频
        "concurrent_limit": 3,               # 并发下载数量
        "retry_times": 3,                    # 下载失败重试次数
        "timeout": 60,                       # 下载超时时间(秒)
        "chunk_size": 1048576,               # 分块下载大小(字节，默认1MB)
        "filename_format": "{bvid}.mp4", # 文件命名格式
        "max_size_gb": 800,                  # 存储空间上限(GB)
        "max_filename_length": 80            # 最大文件名长度
    },
    
    # 数据集相关配置
    "dataset": {
        "index_file": "data/json/index.json", # 数据集索引文件
        "json_filename_format": "{bvid}.json", # JSON文件命名格式
        "video_filename_format": "{bvid}.mp4", # 视频文件命名格式
        "max_videos": 1000,                  # 最大视频数量
        "video_quality": "480p",             # 视频质量描述
        "creator": "Claude",                 # 数据集创建者
        "description": "哔哩哔哩敏感内容数据集", # 数据集描述
        "version": "0.1.0"                   # 数据集版本
    },
    
    # 代理设置
    "proxy": {
        "use_proxy": False,                  # 是否使用代理
        "proxy_url": ""                      # 代理URL
    }
}


def load_config(config_path: str = None):
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认配置
        
    Returns:
        dict: 配置字典
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
            # 递归更新配置
            _update_config(config, user_config)
            
        except Exception as e:
            print(f"加载配置文件失败: {e}，将使用默认配置")
    
    # 确保配置目录存在
    config_dir = Path(os.path.dirname(config_path) if config_path else "config")
    config_dir.mkdir(exist_ok=True)
    
    return config


def _update_config(base_config, new_config):
    """
    递归更新配置
    
    Args:
        base_config: 基础配置
        new_config: 新配置
    """
    if not isinstance(new_config, dict):
        return
    
    for key, value in new_config.items():
        if key in base_config:
            if isinstance(value, dict) and isinstance(base_config[key], dict):
                _update_config(base_config[key], value)
            else:
                base_config[key] = value
        else:
            base_config[key] = value


def save_config(config, config_path):
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
        
    Returns:
        bool: 是否成功保存
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False


def generate_default_config():
    """
    生成默认配置
    
    Returns:
        dict: 默认配置
    """
    return DEFAULT_CONFIG.copy() 