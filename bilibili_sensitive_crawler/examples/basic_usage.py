#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哔哩哔哩敏感视频爬虫基础用法示例

本示例演示如何使用敏感视频爬虫的主要功能，包括：
1. 登录B站
2. 搜索视频
3. 下载视频
4. 管理数据集

作者: Claude
日期: 2025-05-24
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到系统路径
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 导入项目模块
from utils.login import BiliLogin
from utils.search import BiliSearch
from utils.crawler import BiliCrawler
from utils.downloader import BiliDownloader
from utils.dataset import DatasetManager
from config.settings import load_config, generate_default_config


async def example_login():
    """登录示例"""
    print("\n===== 登录示例 =====")
    
    # 加载配置或使用默认配置
    try:
        config = load_config()
    except FileNotFoundError:
        print("配置文件不存在，使用默认配置")
        config = {
            "login": {
                "use_cookie": False,
                "cookie_file": "cookies.json",
                "qrcode_in_terminal": True
            }
        }
    
    # 创建登录器
    login = BiliLogin(config)
    
    # 执行登录
    print("正在登录B站...")
    credential = await login.login()
    print(f"登录成功！用户ID: {await credential.get_uid()}")
    
    return credential


async def example_search(credential):
    """搜索示例"""
    print("\n===== 搜索示例 =====")
    
    # 加载配置或使用默认配置
    config = {
        "search": {
            "page_size": 10,
            "max_pages": 1,
            "order": "totalrank",
            "search_type": 0,
            "duration": 0,
            "tids": 0,
        }
    }
    
    # 创建搜索器
    search = BiliSearch(credential, config)
    
    # 设置过滤参数
    filter_args = {
        "min_duration": 30,    # 至少30秒
        "max_duration": 300,   # 最多5分钟
    }
    
    # 搜索视频
    print("搜索关键词: '测试视频'")
    search_results = await search.search_keyword("测试视频", **filter_args)
    
    print(f"找到 {len(search_results)} 个视频")
    
    # 显示部分搜索结果
    for i, video in enumerate(search_results[:3]):
        print(f"{i+1}. BV号：{video['bvid']}")
        print(f"   标题：{video['title']}")
        print(f"   UP主：{video['owner']['name']}")
        print(f"   时长：{video['duration']}秒")
        print(f"   播放量：{video['stat']['view']}")
        print(f"   质量评分：{video.get('quality_score', 'N/A')}%")
        print()
    
    return search_results


async def example_crawler(credential, bvid):
    """爬虫示例"""
    print("\n===== 爬虫示例 =====")
    
    # 加载配置或使用默认配置
    config = {}
    
    # 创建爬虫
    crawler = BiliCrawler(credential, config)
    
    # 获取视频信息
    print(f"获取视频信息: {bvid}")
    video_info = await crawler.get_video_info(bvid)
    
    # 显示部分信息
    print(f"视频标题: {video_info['basic_info']['title']}")
    print(f"UP主: {video_info['basic_info']['owner']['name']}")
    print(f"描述: {video_info['basic_info']['desc'][:50]}...")
    print(f"标签: {', '.join(video_info.get('tags', []))}")
    
    return video_info


async def example_downloader(credential, bvid):
    """下载器示例"""
    print("\n===== 下载器示例 =====")
    
    # 创建临时下载目录
    download_dir = Path("./demo_downloads")
    download_dir.mkdir(exist_ok=True)
    
    # 下载配置
    config = {
        "quality": 16,  # 360P，演示用
        "with_audio": True,
        "concurrent_limit": 1,
        "retry_times": 2,
        "timeout": 30,
        "chunk_size": 1024 * 1024,
    }
    
    # 创建下载器
    downloader = BiliDownloader(credential, str(download_dir), config)
    
    # 下载视频
    print(f"下载视频: {bvid}")
    try:
        video_path, size_bytes = await downloader.download_video(bvid)
        print(f"下载成功！")
        print(f"保存路径: {video_path}")
        print(f"文件大小: {size_bytes/1024/1024:.2f}MB")
    except Exception as e:
        print(f"下载失败: {str(e)}")
    
    # 获取下载统计
    stats = downloader.get_download_stats()
    print(f"下载统计: 总数={stats['total']}, 成功={stats['success']}, 失败={stats['failed']}")
    
    return download_dir


async def example_dataset(video_info, download_dir):
    """数据集管理示例"""
    print("\n===== 数据集管理示例 =====")
    
    # 创建演示数据目录
    json_dir = Path("./demo_json")
    json_dir.mkdir(exist_ok=True)
    
    # 数据集配置
    config = {
        "index_file": str(json_dir / "index.json"),
        "json_filename_format": "{bvid}.json",
        "include_comments": False,
        "include_danmaku": False,
    }
    
    # 创建数据集管理器
    dataset = DatasetManager(str(json_dir), str(download_dir), config)
    
    # 保存视频信息
    bvid = video_info["basic_info"]["bvid"]
    print(f"保存视频信息: {bvid}")
    json_path = dataset.save_video_info(video_info)
    print(f"已保存到: {json_path}")
    
    # 生成索引
    print("生成数据集索引")
    index_path = dataset.generate_index()
    print(f"索引已保存到: {index_path}")
    
    # 导出统计报告
    print("导出数据集统计报告")
    report_path = dataset.export_stats_report()
    print(f"报告已保存到: {report_path}")
    
    # 检查数据集完整性
    print("检查数据集完整性")
    integrity = dataset.check_dataset_integrity()
    print(f"总视频数: {integrity['total_videos']}")
    print(f"有JSON文件: {integrity['videos_with_json']}")
    print(f"有视频文件: {integrity['videos_with_file']}")
    
    return json_dir


async def cleanup(json_dir, download_dir):
    """清理示例创建的文件"""
    print("\n===== 清理示例文件 =====")
    
    # 确认清理
    answer = input("是否删除示例创建的文件? (y/n): ")
    if answer.lower() != 'y':
        print("保留示例文件")
        return
    
    # 删除JSON目录
    if json_dir.exists():
        import shutil
        shutil.rmtree(json_dir)
        print(f"已删除 {json_dir}")
    
    # 删除下载目录
    if download_dir.exists():
        import shutil
        shutil.rmtree(download_dir)
        print(f"已删除 {download_dir}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="哔哩哔哩敏感视频爬虫使用示例")
    parser.add_argument("--bvid", type=str, default="BV1GJ411x7h7",
                        help="要下载的视频BV号，默认是一个示例视频")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="不清理示例创建的文件")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("哔哩哔哩敏感视频爬虫使用示例")
    print("本示例将演示如何使用爬虫的主要功能")
    print("=" * 50)
    
    try:
        # 登录示例
        credential = await example_login()
        
        # 搜索示例
        search_results = await example_search(credential)
        
        # 爬虫示例
        bvid = args.bvid
        video_info = await example_crawler(credential, bvid)
        
        # 下载器示例
        download_dir = await example_downloader(credential, bvid)
        
        # 数据集管理示例
        json_dir = await example_dataset(video_info, download_dir)
        
        # 清理示例文件
        if not args.no_cleanup:
            await cleanup(json_dir, download_dir)
        
        print("\n示例运行完成！有关更多详细信息，请查阅文档。")
        
    except KeyboardInterrupt:
        print("\n示例已中断")
    except Exception as e:
        print(f"\n示例运行出错: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 