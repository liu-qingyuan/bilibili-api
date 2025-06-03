#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录模块

提供哔哩哔哩登录功能，支持扫码登录和Cookie登录两种方式。
基于bilibili_api的login_v2模块实现。

作者: Claude
日期: 2025-05-20
更新: 2025-01-XX (修复login_v2 API调用)
"""

import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, Any
import platform

# 添加父目录到系统路径，以便导入bilibili_api库
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 导入bilibili_api库
from bilibili_api import login_v2, sync, user
from bilibili_api.utils.network import Credential
from bilibili_api.exceptions import NetworkException, ApiException, CredentialNoSessdataException

# 导入QR码显示相关库
try:
    import qrcode
    from rich.console import Console
    HAS_QR_DEPENDENCIES = True
except ImportError:
    HAS_QR_DEPENDENCIES = False


class LoginException(Exception):
    """登录异常基类"""
    pass


class NetworkError(LoginException):
    """网络连接错误"""
    pass


class CredentialError(LoginException):
    """凭证错误"""
    pass


class LoginTimeout(LoginException):
    """登录超时错误"""
    pass


class BiliLogin:
    """B站登录类"""
    
    def __init__(self, config):
        """
        初始化登录器
        
        Args:
            config: 配置字典，包含登录相关配置
        """
        self.config = config
        self.logger = logging.getLogger("bili_crawler.login")
        self.credential = None
        
        # 登录配置
        self.login_config = self.config.get("login", {})
        
        # 默认登录配置
        self.default_login_config = {
            "use_cookie": False,                 # 是否使用已有Cookie
            "cookie_file": "config/cookies.json", # Cookie文件路径
            "credential_file": "config/credential.json", # 凭证保存路径
            "verify_timeout": 180,               # 验证超时时间(秒)
            "max_retries": 3,                    # 最大重试次数
            "retry_interval": 5,                 # 重试间隔(秒)
            "check_network": True,               # 是否检查网络连接
            "network_timeout": 10,               # 网络检查超时(秒)
            "test_servers": [                    # 测试服务器列表
                "api.bilibili.com",
                "passport.bilibili.com",
                "www.bilibili.com"
            ]
        }
        
        # 合并配置
        for key, value in self.default_login_config.items():
            if key not in self.login_config:
                self.login_config[key] = value
        
        # 确保目录存在
        Path(os.path.dirname(self.login_config["credential_file"])).mkdir(exist_ok=True)
        if self.login_config.get("cookie_file"):
            Path(os.path.dirname(self.login_config["cookie_file"])).mkdir(exist_ok=True)
    
    def _print_qr_terminal(self, data: str) -> None:
        """
        使用qrcode和rich在终端中打印二维码
        
        Args:
            data: 二维码数据（URL）
        """
        if not HAS_QR_DEPENDENCIES:
            self.logger.warning("未安装qrcode或rich库，无法在终端显示二维码")
            print(f"请使用手机扫描二维码链接: {data}")
            return
            
        try:
            qr = qrcode.QRCode(border=1)
            qr.add_data(data)
            qr.make(fit=True)
            matrix = qr.get_matrix()
            console = Console()
            for row in matrix:
                line = "".join("██" if cell else "  " for cell in row)
                console.print(line)
        except Exception as e:
            self.logger.warning(f"显示二维码失败: {str(e)}")
            print(f"请使用手机扫描二维码链接: {data}")
        
    async def login(self, force_relogin: bool = False) -> Credential:
        """
        执行登录流程
        
        Args:
            force_relogin: 是否强制重新登录，忽略已有凭证
            
        Returns:
            Credential: 登录凭证对象
            
        Raises:
            NetworkError: 网络连接错误
            CredentialError: 凭证错误
            LoginTimeout: 登录超时
            LoginException: 其他登录错误
        """
        # 检查网络连接
        if self.login_config["check_network"]:
            if not await self._check_network():
                raise NetworkError("登录前网络连接检查失败，请检查网络设置")
        
        # 如果不强制重新登录，首先尝试加载保存的凭证
        if not force_relogin:
            try:
                if await self._load_credential():
                    self.logger.info("成功加载已保存的凭证")
                    return self.credential
            except Exception as e:
                self.logger.warning(f"加载凭证时出错: {str(e)}，将尝试重新登录")
        
        # 凭证无效或不存在或强制重新登录，执行登录流程
        retry_count = 0
        last_error = None
        
        while retry_count < self.login_config["max_retries"]:
            try:
                # 确定登录方式
                if self.login_config["use_cookie"]:
                    self.logger.info(f"尝试使用Cookie登录 (尝试 {retry_count + 1}/{self.login_config['max_retries']})")
                    await self._login_with_cookie()
                else:
                    self.logger.info(f"尝试使用扫码登录 (尝试 {retry_count + 1}/{self.login_config['max_retries']})")
                    await self._login_with_qrcode()
                
                # 验证凭证是否有效
                if not await self._verify_credential():
                    raise CredentialError("登录成功但凭证验证失败")
                
                # 保存凭证
                await self._save_credential()
                
                self.logger.info("登录成功并验证通过")
                return self.credential
                
            except (NetworkException, ApiException) as e:
                self.logger.error(f"登录过程中发生网络错误: {str(e)}")
                last_error = NetworkError(f"网络连接错误: {str(e)}")
            
            except (ApiException, CredentialNoSessdataException) as e:
                self.logger.error(f"API错误: {str(e)}")
                last_error = CredentialError(f"API错误: {str(e)}")
                
            except asyncio.TimeoutError as e:
                self.logger.error(f"登录超时: {str(e)}")
                last_error = LoginTimeout(f"登录操作超时: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"登录过程中发生未知错误: {str(e)}")
                last_error = LoginException(f"未知错误: {str(e)}")
            
            retry_count += 1
            if retry_count < self.login_config["max_retries"]:
                self.logger.info(f"等待 {self.login_config['retry_interval']} 秒后重试...")
                await asyncio.sleep(self.login_config["retry_interval"])
        
        # 所有重试都失败了
        if last_error:
            raise last_error
        else:
            raise LoginException("登录失败，已达到最大重试次数")
    
    async def _check_network(self) -> bool:
        """
        检查网络连接
        
        Returns:
            bool: 网络是否可用
        """
        self.logger.debug("检查网络连接...")
        
        import aiohttp
        
        timeout = aiohttp.ClientTimeout(total=self.login_config["network_timeout"])
        
        for server in self.login_config["test_servers"]:
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"https://{server}") as response:
                        if response.status < 500:  # 任何非服务器错误都认为网络可用
                            self.logger.debug(f"网络连接正常 (测试服务器: {server})")
                            return True
            except Exception as e:
                self.logger.debug(f"测试服务器 {server} 连接失败: {str(e)}")
                continue
        
        self.logger.error("所有测试服务器连接失败，网络可能不可用")
        return False
    
    async def _login_with_qrcode(self) -> None:
        """
        使用二维码登录
        
        基于login_v2.md文档中的示例实现
        
        Raises:
            LoginTimeout: 登录超时
            LoginException: 其他登录错误
        """
        self.logger.info("正在使用二维码登录...")
        
        try:
            # 生成二维码登录实例，平台选择网页端
            qr = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
            
            # 生成二维码
            await qr.generate_qrcode()
            
            # 获取终端二维码文本并显示
            qr_terminal = qr.get_qrcode_terminal()
            if qr_terminal:
                print("\n请使用哔哩哔哩App扫描下方二维码:")
                print(qr_terminal)
                print("扫描后请在手机上确认登录\n")
            else:
                self.logger.warning("无法获取终端二维码")
                raise LoginException("无法生成二维码")
            
            self.logger.info("二维码已生成，请扫描二维码并在手机上确认登录")
            
            # 在完成扫描前轮询
            start_time = time.time()
            timeout = self.login_config["verify_timeout"]
            last_status = None
            
            while not qr.has_done():
                # 检查超时
                if time.time() - start_time > timeout:
                    raise LoginTimeout(f"二维码登录超时（{timeout}秒）")
                
                try:
                    # 检查状态
                    status = await qr.check_state()
                    
                    # 只在状态变化时输出日志，避免重复输出
                    if status != last_status:
                        last_status = status
                        self.logger.info(f"二维码状态: {status}")
                    
                except Exception as e:
                    self.logger.debug(f"检查二维码状态时出错: {str(e)}")
                
                # 轮询间隔建议 >=1s
                await asyncio.sleep(1)
            
            # 获取 Credential 类
            self.credential = qr.get_credential()
            self.logger.info("扫码登录成功")
            
        except Exception as e:
            if isinstance(e, (LoginTimeout, LoginException)):
                raise
            else:
                raise LoginException(f"二维码登录失败: {str(e)}")
    
    async def _login_with_cookie(self) -> None:
        """
        使用Cookie登录
        
        从保存的Cookie文件中加载凭证
        
        Raises:
            CredentialError: 凭证错误
            LoginException: 其他登录错误
        """
        self.logger.info("正在使用Cookie登录...")
        
        cookie_file = self.login_config["cookie_file"]
        
        if not os.path.exists(cookie_file):
            raise CredentialError(f"Cookie文件不存在: {cookie_file}")
        
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            # 从Cookie数据创建Credential对象
            if isinstance(cookie_data, dict):
                # 如果是字典格式，尝试提取必要字段
                sessdata = cookie_data.get('SESSDATA')
                bili_jct = cookie_data.get('bili_jct')
                buvid3 = cookie_data.get('buvid3')
                
                if not sessdata:
                    raise CredentialError("Cookie文件中缺少SESSDATA")
                
                self.credential = Credential(
                    sessdata=sessdata,
                    bili_jct=bili_jct,
                    buvid3=buvid3
                )
            else:
                raise CredentialError("Cookie文件格式不正确")
            
            self.logger.info("Cookie登录成功")
            
        except json.JSONDecodeError as e:
            raise CredentialError(f"Cookie文件格式错误: {str(e)}")
        except Exception as e:
            raise LoginException(f"Cookie登录失败: {str(e)}")
    
    async def _load_credential(self) -> bool:
        """
        从文件加载保存的凭证
        
        Returns:
            bool: 是否成功加载凭证
        """
        credential_file = self.login_config["credential_file"]
        
        if not os.path.exists(credential_file):
            self.logger.debug(f"凭证文件不存在: {credential_file}")
            return False
        
        try:
            with open(credential_file, 'r', encoding='utf-8') as f:
                credential_data = json.load(f)
            
            # 创建Credential对象
            self.credential = Credential(
                sessdata=credential_data.get('sessdata'),
                bili_jct=credential_data.get('bili_jct'),
                buvid3=credential_data.get('buvid3'),
                dedeuserid=credential_data.get('dedeuserid'),
                ac_time_value=credential_data.get('ac_time_value')
            )
            
            self.logger.debug("成功从文件加载凭证")
            return True
            
        except Exception as e:
            self.logger.warning(f"加载凭证文件失败: {str(e)}")
            return False
    
    async def _verify_credential(self) -> bool:
        """
        验证凭证是否有效
        
        Returns:
            bool: 凭证是否有效
        """
        if not self.credential:
            return False
        
        try:
            # 首先尝试获取用户基本信息来验证凭证
            # 使用更简单的方法验证凭证
            cookies = self.credential.get_cookies()
            
            # 检查必要的cookie是否存在
            if not cookies.get('SESSDATA'):
                self.logger.warning("凭证验证失败：缺少SESSDATA")
                return False
            
            # 尝试使用user模块验证凭证，但需要先获取uid
            try:
                # 从cookies中获取DedeUserID作为uid
                uid = cookies.get('DedeUserID')
                if not uid:
                    self.logger.warning("无法从cookies中获取用户ID")
                    # 尝试通过API获取用户信息
                    return await self._verify_credential_alternative()
                
                # 创建用户对象并验证
                u = user.User(uid=int(uid), credential=self.credential)
                info = await u.get_user_info()
                
                if info and 'mid' in info:
                    self.logger.info(f"凭证验证成功，用户: {info.get('name', 'Unknown')} (UID: {info['mid']})")
                    return True
                else:
                    self.logger.warning("凭证验证失败：无法获取用户信息")
                    return False
                    
            except Exception as e:
                self.logger.warning(f"使用User模块验证失败: {str(e)}，尝试备选验证方法")
                return await self._verify_credential_alternative()
            
        except Exception as e:
            self.logger.warning(f"凭证验证失败: {str(e)}")
            return False
    
    async def _verify_credential_alternative(self) -> bool:
        """
        备选凭证验证方法
        
        Returns:
            bool: 凭证是否有效
        """
        try:
            import aiohttp
            
            # 使用简单的API请求验证凭证
            cookies = self.credential.get_cookies()
            
            # 构建请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
            
            # 使用简单的API验证登录状态
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.bilibili.com/x/web-interface/nav',
                    cookies=cookies,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0 and data.get('data', {}).get('isLogin'):
                            user_info = data.get('data', {})
                            self.logger.info(f"凭证验证成功，用户: {user_info.get('uname', 'Unknown')} (UID: {user_info.get('mid', 'Unknown')})")
                            return True
                        else:
                            self.logger.warning("凭证验证失败：用户未登录")
                            return False
                    else:
                        self.logger.warning(f"凭证验证失败：HTTP状态码 {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.warning(f"备选凭证验证失败: {str(e)}")
            return False
    
    async def _save_credential(self) -> bool:
        """
        保存凭证到文件
        
        Returns:
            bool: 是否成功保存
        """
        if not self.credential:
            return False
        
        try:
            credential_file = self.login_config["credential_file"]
            
            # 获取凭证的cookies
            cookies = self.credential.get_cookies()
            
            # 保存凭证数据
            credential_data = {
                'sessdata': cookies.get('SESSDATA'),
                'bili_jct': cookies.get('bili_jct'),
                'buvid3': cookies.get('buvid3'),
                'dedeuserid': cookies.get('DedeUserID'),
                'ac_time_value': cookies.get('ac_time_value'),
                'saved_time': time.time()
            }
            
            with open(credential_file, 'w', encoding='utf-8') as f:
                json.dump(credential_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"凭证已保存到: {credential_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存凭证失败: {str(e)}")
            return False
    
    async def check_login_status(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查当前登录状态
        
        Returns:
            Tuple[bool, Dict]: (是否已登录, 用户信息)
        """
        if not self.credential:
            return False, {}
        
        try:
            # 使用备选验证方法，避免User模块的uid问题
            return await self._check_login_status_alternative()
                
        except Exception as e:
            self.logger.debug(f"检查登录状态失败: {str(e)}")
            return False, {}
    
    async def _check_login_status_alternative(self) -> Tuple[bool, Dict[str, Any]]:
        """
        备选登录状态检查方法
        
        Returns:
            Tuple[bool, Dict]: (是否已登录, 用户信息)
        """
        try:
            import aiohttp
            
            # 使用简单的API请求检查登录状态
            cookies = self.credential.get_cookies()
            
            # 构建请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
            
            # 使用简单的API验证登录状态
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.bilibili.com/x/web-interface/nav',
                    cookies=cookies,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0 and data.get('data', {}).get('isLogin'):
                            user_info = data.get('data', {})
                            return True, user_info
                        else:
                            return False, {}
                    else:
                        return False, {}
                        
        except Exception as e:
            self.logger.debug(f"备选登录状态检查失败: {str(e)}")
            return False, {}
    
    async def logout(self) -> bool:
        """
        登出（清除本地凭证）
        
        Returns:
            bool: 是否成功登出
        """
        try:
            # 清除内存中的凭证
            self.credential = None
            
            # 删除凭证文件
            credential_file = self.login_config["credential_file"]
            if os.path.exists(credential_file):
                os.remove(credential_file)
                self.logger.info("已删除本地凭证文件")
            
            # 删除Cookie文件（如果存在）
            cookie_file = self.login_config.get("cookie_file")
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)
                self.logger.info("已删除本地Cookie文件")
            
            self.logger.info("登出成功")
            return True
            
        except Exception as e:
            self.logger.error(f"登出失败: {str(e)}")
            return False


async def test_login():
    """测试登录功能"""
    # 测试配置
    test_config = {
        "login": {
            "use_cookie": False,
            "verify_timeout": 180,
            "max_retries": 1,
            "credential_file": "test_credential.json"
        }
    }
    
    # 创建登录器
    login_manager = BiliLogin(test_config)
    
    try:
        # 强制重新登录（忽略已有凭证）
        print("开始测试二维码登录功能...")
        credential = await login_manager.login(force_relogin=True)
        print(f"登录成功！")
        print(f"Cookies: {credential.get_cookies()}")
        
        # 检查登录状态
        is_logged_in, user_info = await login_manager.check_login_status()
        if is_logged_in:
            print(f"用户信息: {user_info.get('uname')} (UID: {user_info.get('mid')})")
        
    except Exception as e:
        print(f"登录失败: {str(e)}")

        
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
    
    # 运行测试
    asyncio.run(test_login()) 