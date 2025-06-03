#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本

运行B站敏感视频爬虫项目的所有单元测试

作者: Claude
日期: 2025-05-24
"""

import os
import sys
import unittest
import argparse
from pathlib import Path

# 添加项目根目录到系统路径
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from test_config import setup_test_logging, ensure_test_dirs


def run_tests(test_names=None, verbosity=2):
    """
    运行测试用例
    
    Args:
        test_names: 要运行的测试模块名列表，默认为None表示运行所有测试
        verbosity: 测试输出的详细程度
    
    Returns:
        bool: 测试是否全部通过
    """
    logger = setup_test_logging()
    logger.info("准备运行测试用例")
    
    # 确保测试目录存在
    test_dirs = ensure_test_dirs()
    logger.info(f"测试数据目录: {test_dirs[0]}")
    
    # 构建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 当前目录
    current_dir = Path(__file__).parent
    
    if test_names:
        # 加载指定的测试模块
        for test_name in test_names:
            if not test_name.startswith("test_"):
                test_name = f"test_{test_name}"
            
            if not test_name.endswith(".py"):
                test_name = f"{test_name}.py"
            
            test_file = current_dir / test_name
            
            if test_file.exists():
                module_name = test_file.stem
                module_path = f"tests.{module_name}"
                try:
                    tests = loader.loadTestsFromName(module_path)
                    suite.addTests(tests)
                    logger.info(f"已加载测试模块: {module_path}")
                except Exception as e:
                    logger.error(f"加载测试模块 {module_path} 失败: {str(e)}")
            else:
                logger.warning(f"测试文件不存在: {test_file}")
    else:
        # 加载所有测试模块
        pattern = "test_*.py"
        tests = loader.discover(start_dir=current_dir, pattern=pattern)
        suite.addTests(tests)
        logger.info(f"已加载所有测试模块")
    
    # 运行测试
    logger.info("开始执行测试")
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    logger.info(f"测试完成: 总数={result.testsRun}, 成功={result.testsRun - len(result.failures) - len(result.errors)}, "
               f"失败={len(result.failures)}, 错误={len(result.errors)}")
    
    return len(result.failures) == 0 and len(result.errors) == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="哔哩哔哩敏感视频爬虫单元测试")
    parser.add_argument("tests", nargs="*", default=[],
                        help="要运行的测试模块名，不提供则运行所有测试")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="显示详细测试输出")
    
    args = parser.parse_args()
    verbosity = 2 if args.verbose else 1
    
    success = run_tests(args.tests, verbosity)
    
    # 设置退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 