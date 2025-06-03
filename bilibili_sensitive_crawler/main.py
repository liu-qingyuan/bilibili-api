#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哔哩哔哩敏感视频爬虫项目主入口

功能：
1. 登录哔哩哔哩（支持扫码登录）
2. 根据关键词搜索视频
3. 爬取视频相关信息并保存为JSON格式
4. 下载视频（480p清晰度，含音频）
5. 构建视觉大语言模型评测数据集

作者: Claude
日期: 2025-05-20
更新: 2025-05-23
"""

import os
import sys
import time
import logging
import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import platform
import shutil

# 添加父目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 添加当前目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入项目模块
from utils.login import BiliLogin
from utils.search import BiliSearch
from utils.crawler import BiliCrawler
from utils.downloader import BiliDownloader
from utils.dataset import DatasetManager
from utils.video_filter import VideoFilter
from utils.file_analyzer import FileAnalyzer
from config.settings import load_config, save_config, generate_default_config

# 设置 Windows 异步I/O策略
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 初始化日志配置
def setup_logging(debug: bool = False, log_file: str = None):
    """设置日志配置"""
    level = logging.DEBUG if debug else logging.INFO
    
    # 确保日志目录存在
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置日志处理器
    handlers = []
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # 配置根日志器
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    
    # 设置第三方库的日志级别
    for module in ['urllib3', 'asyncio', 'PIL']:
        logging.getLogger(module).setLevel(logging.WARNING)

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description="哔哩哔哩敏感内容爬虫")
    
    # 基本参数
    parser.add_argument('--config', type=str, default='config/config.json',
                        help='配置文件路径 (默认: config/config.json)')
    parser.add_argument('--debug', action='store_true',
                        help='启用调试日志')
    parser.add_argument('--verbose', action='store_true',
                        help='启用详细日志输出')
    parser.add_argument('--log-file', type=str, default='logs/bili_crawler.log',
                        help='日志文件路径 (默认: logs/bili_crawler.log)')
    
    # 配置相关
    parser.add_argument('--generate-config', action='store_true',
                        help='生成默认配置文件并退出')
    
    # 登录相关
    parser.add_argument('--force-login', action='store_true',
                        help='强制重新登录')
    parser.add_argument('--use-cookie', action='store_true',
                        help='使用Cookie登录')
    
    # 搜索相关
    parser.add_argument('--keywords', type=str, nargs='+',
                        help='搜索关键词列表')
    parser.add_argument('--limit', type=int, default=100,
                        help='每个关键词的视频数量限制 (默认: 100)')
    
    # 爬取相关
    parser.add_argument('--download', action='store_true',
                        help='下载视频文件')
    parser.add_argument('--info-only', action='store_true',
                        help='仅爬取视频信息，不下载视频')
    parser.add_argument('--quality', type=int, default=32,
                        help='视频质量 (默认: 32 [480P])')
    
    # 数据集相关
    parser.add_argument('--metadata-dir', type=str,
                        help='元数据保存目录 (默认使用配置文件设置)')
    parser.add_argument('--video-dir', type=str,
                        help='视频保存目录 (默认使用配置文件设置)')
    parser.add_argument('--max-videos', type=int, default=1000,
                        help='最大视频数量 (默认: 1000)')
    
    # 执行控制
    parser.add_argument('--resume', action='store_true',
                        help='恢复上次爬取')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='最大重试次数 (默认: 3)')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='请求间隔时间 (秒) (默认: 1.0)')
    
    # 视频过滤相关
    parser.add_argument('--delete-long-videos', action='store_true',
                        help='删除超出指定时长的视频及其元数据文件')
    parser.add_argument('--list-long-videos', action='store_true',
                        help='列出超出指定时长的视频（不删除）')
    parser.add_argument('--max-duration', type=int, default=30,
                        help='最大允许视频时长（秒）(默认: 30)')
    parser.add_argument('--dry-run', action='store_true',
                        help='试运行模式，不实际删除文件')
    parser.add_argument('--generate-report', action='store_true',
                        help='生成删除操作报告')
    
    # 文件清理相关
    parser.add_argument('--analyze-files', action='store_true',
                        help='分析视频文件和JSON文件的匹配情况')
    parser.add_argument('--clean-orphan-videos', action='store_true',
                        help='清理孤立的视频文件（有视频无JSON）')
    parser.add_argument('--clean-orphan-jsons', action='store_true',
                        help='清理孤立的JSON文件（有JSON无视频）')
    parser.add_argument('--save-analysis-report', action='store_true',
                        help='保存文件分析报告到文件')
    parser.add_argument('--sync-index', action='store_true',
                        help='同步index.json索引文件与实际文件')
    parser.add_argument('--update-index', action='store_true',
                        help='在清理文件时同时更新索引文件')
    parser.add_argument('--check-index', action='store_true',
                        help='检查索引文件的完整性和匹配情况')
    
    return parser.parse_args()

# 主函数
async def main():
    """爬虫主函数"""
    args = parse_args()
    
    # 设置日志级别 (debug优先级高于verbose)
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    logger = logging.getLogger("bili_crawler.main")
    logger.info("哔哩哔哩敏感视频爬虫启动")
    
    try:
        # 加载配置
        config = load_config()
        
        # 设置bilibili-api网络配置
        try:
            from bilibili_api import request_settings
            
            # 设置超时
            timeout = config.get("crawler", {}).get("timeout", 30)
            request_settings.set_timeout(timeout)
            
            # 设置重试次数
            max_retries = config.get("crawler", {}).get("max_retries", 3)
            request_settings.set_wbi_retry_times(max_retries)
            
            logger.info("bilibili-api全局网络设置已配置")
            
        except ImportError:
            logger.warning("无法导入bilibili_api.request_settings，跳过全局API设置")
        except Exception as e:
            logger.warning(f"设置bilibili-api全局网络配置失败: {str(e)}")
        
        # 设置日志
        setup_logging(debug=args.debug, log_file=args.log_file)
        
        # 应用程序启动信息
        logger.info("=" * 50)
        logger.info("哔哩哔哩敏感内容爬虫启动")
        logger.info(f"版本: 0.1.0")
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"平台: {platform.system()} {platform.version()}")
        logger.info("=" * 50)
        
        # 配置文件路径
        config_path = args.config
        
        # 生成默认配置并退出
        if args.generate_config:
            config_dir = os.path.dirname(config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            if os.path.exists(config_path):
                logger.warning(f"配置文件已存在: {config_path}")
                overwrite = input("是否覆盖现有配置文件? (y/n): ").lower() == 'y'
                if not overwrite:
                    logger.info("取消生成配置文件")
                    return
            
            config = generate_default_config()
            save_config(config, config_path)
            logger.info(f"已生成默认配置文件: {config_path}")
            return
        
        # 更新配置(命令行参数优先)
        update_config_from_args(config, args)
        
        # 处理视频过滤功能
        if args.delete_long_videos or args.list_long_videos:
            logger.info("=" * 50)
            logger.info("视频过滤功能")
            logger.info("=" * 50)
            
            # 创建视频过滤器
            video_filter = VideoFilter(
                config['paths']['metadata_dir'], 
                config['paths']['videos_dir'], 
                config
            )
            
            if args.list_long_videos:
                # 仅列出超长视频
                logger.info(f"列出超出 {args.max_duration} 秒的视频...")
                video_filter.list_long_videos(args.max_duration)
                return
            
            elif args.delete_long_videos:
                # 删除超长视频
                logger.info(f"删除超出 {args.max_duration} 秒的视频...")
                result = video_filter.delete_long_videos(
                    args.max_duration, 
                    dry_run=args.dry_run,
                    generate_report=args.generate_report
                )
                
                if result['deleted_count'] > 0:
                    logger.info(f"成功删除 {result['deleted_count']} 个超长视频")
                else:
                    logger.info("没有找到需要删除的超长视频")
                return
        
        # 处理文件分析和清理功能
        if args.analyze_files or args.clean_orphan_videos or args.clean_orphan_jsons or args.save_analysis_report or args.sync_index or args.check_index:
            logger.info("=" * 50)
            logger.info("文件分析和清理功能")
            logger.info("=" * 50)
            
            # 创建文件分析器
            file_analyzer = FileAnalyzer(
                config['paths']['metadata_dir'], 
                config['paths']['videos_dir']
            )
            
            if args.check_index:
                # 检查索引文件完整性
                logger.info("检查索引文件完整性和匹配情况...")
                result = file_analyzer.analyze_file_matching(check_index=True)
                return
            
            elif args.sync_index:
                # 同步索引文件
                logger.info("同步索引文件与实际文件...")
                result = file_analyzer.sync_index_with_files(dry_run=args.dry_run)
                if result['removed_count'] > 0:
                    logger.info(f"{'[试运行] ' if args.dry_run else ''}成功同步索引文件，删除 {result['removed_count']} 个孤立记录")
                else:
                    logger.info("索引文件已是最新状态，无需同步")
                return
            
            elif args.analyze_files:
                # 仅分析文件匹配情况
                logger.info("分析文件匹配情况...")
                result = file_analyzer.analyze_file_matching(check_index=True)
                return
            
            elif args.save_analysis_report:
                # 保存分析报告
                logger.info("生成文件分析报告...")
                report_path = file_analyzer.save_analysis_report()
                logger.info(f"分析报告已保存到: {report_path}")
                return
            
            elif args.clean_orphan_videos or args.clean_orphan_jsons:
                # 清理孤立文件
                logger.info("清理孤立文件...")
                result = file_analyzer.clean_orphan_files(
                    clean_videos=args.clean_orphan_videos,
                    clean_jsons=args.clean_orphan_jsons,
                    update_index=args.update_index,
                    dry_run=args.dry_run
                )
                
                total_cleaned = result['cleaned_video_count'] + result['cleaned_json_count']
                if total_cleaned > 0:
                    logger.info(f"{'[试运行] ' if args.dry_run else ''}成功清理 {total_cleaned} 个孤立文件")
                    if args.update_index:
                        logger.info(f"索引文件同步: {'成功' if result['index_synced'] else '失败'}")
                else:
                    logger.info("没有找到需要清理的孤立文件")
                return
        
        try:
            # 创建日志和数据目录
            os.makedirs(config['paths']['logs_dir'], exist_ok=True)
            os.makedirs(config['paths']['data_dir'], exist_ok=True)
            os.makedirs(config['paths']['metadata_dir'], exist_ok=True)
            os.makedirs(config['paths']['videos_dir'], exist_ok=True)
            
            # 登录
            logger.info("开始登录哔哩哔哩...")
            login_manager = BiliLogin(config)
            credential = await login_manager.login(force_relogin=args.force_login)
            logger.info("登录成功!")
            
            # 创建爬虫管理器
            search_manager = BiliSearch(credential, config)
            crawler = BiliCrawler(credential, config)
            downloader = BiliDownloader(credential, config['paths']['videos_dir'], config['downloader'])
            dataset_manager = DatasetManager(config['paths']['metadata_dir'], config['paths']['videos_dir'], config)
            
            # 获取搜索关键词
            keywords = args.keywords or config['search']['keywords']
            if not keywords:
                logger.error("未指定搜索关键词")
                return
            
            # 检查已有JSON记录中缺失的视频文件
            logger.info("检查已有记录中缺失的视频文件...")
            missing_videos = dataset_manager.get_missing_video_files()
            if missing_videos:
                logger.info(f"发现 {len(missing_videos)} 个缺失的视频文件，开始重新下载...")
                for i, bvid in enumerate(missing_videos):
                    logger.info(f"[{i+1}/{len(missing_videos)}] 重新下载缺失视频: {bvid}")
                    try:
                        save_path, file_size = await downloader.download_video(bvid)
                        logger.info(f"缺失视频下载成功: {save_path}, 大小: {file_size/1024/1024:.2f}MB")
                        # 更新元数据中的下载状态
                        dataset_manager.update_video_path(bvid, save_path)
                        await asyncio.sleep(args.interval)
                    except Exception as e:
                        logger.error(f"重新下载缺失视频失败 {bvid}: {str(e)}")
            else:
                logger.info("所有已记录的视频文件都存在")

            # 搜索视频
            max_videos_per_keyword = args.limit
            for keyword in keywords:
                logger.info(f"正在搜索关键词: {keyword}")
                video_results = await search_manager.search_videos(keyword, limit=max_videos_per_keyword)
                
                # 限制视频数量（双重保险）
                if len(video_results) > max_videos_per_keyword:
                    video_results = video_results[:max_videos_per_keyword]
                
                logger.info(f"找到 {len(video_results)} 个视频")
                
                # 爬取视频信息
                for i, video_item in enumerate(video_results):
                    bvid = video_item["bvid"]
                    search_info = video_item["search_info"]
                    
                    logger.info(f"[{i+1}/{len(video_results)}] 处理视频: {bvid}")
                    
                    try:
                        # 检查BV号是否有效
                        if not bvid or not bvid.startswith('BV') or len(bvid) != 12:
                            logger.warning(f"无效的BV号，跳过: '{bvid}'")
                            continue
                        
                        # 检查是否已经爬取过
                        if dataset_manager.has_video(bvid):
                            logger.info(f"视频已存在于数据集中: {bvid}")
                            continue
                        
                        # 爬取详细信息
                        logger.info(f"正在爬取视频信息: {bvid}")
                        video_info = await crawler.get_video_info(bvid)
                        
                        # 添加搜索信息到视频数据中
                        video_info["search_info"] = search_info
                        
                        # 检查视频时长（在下载前过滤）
                        video_duration = video_info.get('basic_info', {}).get('duration', 0)
                        
                        # 获取时长限制，如果指定了max_duration就启用过滤
                        max_duration = None
                        if hasattr(args, 'max_duration') and args.max_duration:
                            max_duration = args.max_duration
                        elif config.get('video_filter', {}).get('max_duration'):
                            max_duration = config.get('video_filter', {}).get('max_duration')
                        
                        # 如果设置了时长限制，就进行过滤
                        if max_duration and video_duration > max_duration:
                            logger.info(f"视频时长 {video_duration}秒 超过限制 {max_duration}秒，完全跳过: {bvid}")
                            # 完全跳过，不保存任何记录
                            continue
                        
                        # 保存视频元数据
                        metadata_file = dataset_manager.save_metadata(video_info)
                        logger.info(f"视频元数据已保存: {metadata_file}")
                        
                        # 下载视频
                        if args.download and not args.info_only:
                            logger.info(f"正在下载视频: {bvid} (时长: {video_duration}秒)")
                            try:
                                save_path, file_size = await downloader.download_video(bvid)
                                logger.info(f"视频下载成功: {save_path}, 大小: {file_size/1024/1024:.2f}MB")
                                # 更新元数据中的下载状态
                                dataset_manager.update_video_path(bvid, save_path)
                            except Exception as e:
                                logger.error(f"视频下载失败 {bvid}: {str(e)}")
                        
                        # 检查数据集大小限制
                        total_videos = dataset_manager.count_videos()
                        if total_videos >= args.max_videos:
                            logger.info(f"已达到最大视频数量限制: {args.max_videos}")
                            break
                        
                        # 增加延迟，避免请求过快
                        await asyncio.sleep(args.interval)
                        
                    except Exception as e:
                        logger.error(f"处理视频时出错 {bvid}: {str(e)}")
                        continue
                
                # 检查数据集大小限制
                if dataset_manager.count_videos() >= args.max_videos:
                    logger.info(f"已达到最大视频数量限制: {args.max_videos}")
                    break
            
            # 生成数据集统计信息
            logger.info("正在生成数据集统计信息...")
            stats = dataset_manager.generate_stats()
            logger.info(f"数据集统计: 共{stats['total_videos']}个视频，总大小约{stats['total_size_gb']:.2f}GB")
            
            # 完成
            logger.info("爬取任务已完成!")
            logger.info(f"元数据保存在: {config['paths']['metadata_dir']}")
            if args.download and not args.info_only:
                logger.info(f"视频文件保存在: {config['paths']['videos_dir']}")
        
        except Exception as e:
            logger.error(f"执行过程中发生错误: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())

    except Exception as e:
        logger.error(f"执行过程中发生错误: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())

# 更新配置
def update_config_from_args(config, args):
    """从命令行参数更新配置"""
    logger = logging.getLogger("bili_crawler.main")
    
    # 登录配置
    if args.use_cookie:
        config['login']['use_cookie'] = True
        logger.info("已启用Cookie登录")
    
    # 路径配置
    if args.metadata_dir:
        config['paths']['metadata_dir'] = args.metadata_dir
        logger.info(f"元数据保存目录已设置为: {args.metadata_dir}")
    
    if args.video_dir:
        config['paths']['videos_dir'] = args.video_dir
        logger.info(f"视频保存目录已设置为: {args.video_dir}")
    
    # 爬取配置
    if args.info_only:
        config['crawler']['info_only'] = True
        logger.info("仅爬取视频信息模式已启用")
    
    # 下载配置
    if args.quality:
        config['downloader']['default_quality'] = args.quality
        logger.info(f"视频质量已设置为: {args.quality}")
    
    # 搜索配置
    if args.keywords:
        config['search']['keywords'] = args.keywords
        logger.info(f"搜索关键词已设置为: {args.keywords}")
    
    if args.limit:
        config['search']['limit_per_keyword'] = args.limit
        logger.info(f"每个关键词视频数量限制已设置为: {args.limit}")
    
    # 运行配置
    if args.interval:
        config['crawler']['request_interval'] = args.interval
        logger.info(f"请求间隔已设置为: {args.interval}秒")
    
    if args.max_retries:
        config['crawler']['max_retries'] = args.max_retries
        logger.info(f"最大重试次数已设置为: {args.max_retries}")
    
    # 视频过滤配置
    if hasattr(args, 'max_duration') and args.max_duration:
        if 'video_filter' not in config:
            config['video_filter'] = {}
        config['video_filter']['max_duration'] = args.max_duration
        logger.info(f"最大视频时长已设置为: {args.max_duration}秒")
    
    return config

# 程序入口
if __name__ == "__main__":
    try:
        # 设置 Windows 异步I/O策略
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # 运行主函数
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    except Exception as e:
        print(f"程序出现未捕获的异常: {str(e)}")
        import traceback
        print(traceback.format_exc()) 