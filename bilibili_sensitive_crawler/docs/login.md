# 登录模块文档 (login.py)

## 1. 模块简介

登录模块提供哔哩哔哩网站的登录认证服务，支持扫码登录和Cookie登录两种方式。基于bilibili_api的login_v2模块实现，提供完整的登录流程管理、凭证保存和验证功能。

**主要用途：**
- B站账号登录认证
- 登录凭证管理和持久化
- 网络连接状态检测
- 登录状态验证和维护

## 2. 功能一览

### 2.1 核心功能

#### 2.1.1 扫码登录
- **二维码生成**：自动获取登录二维码
- **终端显示**：支持在终端直接显示二维码（需要qrcode和rich库）
- **状态监控**：实时监控扫码状态
- **超时处理**：支持登录超时自动重试

#### 2.1.2 Cookie登录
- **Cookie文件**：支持从文件加载已有Cookie
- **自动验证**：自动验证Cookie有效性
- **失败回退**：Cookie失效时自动回退到扫码登录

#### 2.1.3 凭证管理
- **自动保存**：登录成功后自动保存凭证到文件
- **自动加载**：启动时自动加载已保存的凭证
- **有效性验证**：定期验证凭证是否仍然有效
- **刷新机制**：支持凭证自动刷新

#### 2.1.4 网络检测
- **连接测试**：登录前检测网络连接状态
- **多服务器测试**：测试多个B站服务器的连通性
- **超时控制**：可配置的网络检测超时时间

#### 2.1.5 错误处理
- **重试机制**：登录失败时自动重试
- **指数退避**：重试间隔逐渐增加
- **异常分类**：区分网络错误、凭证错误等不同类型

### 2.2 主要类和方法

#### 2.2.1 BiliLogin类
**初始化参数：**
- `config`: 配置字典，包含登录相关配置

**主要方法：**
- `login(force_relogin=False)`: 执行登录流程
- `check_login_status()`: 检查当前登录状态
- `logout()`: 登出操作
- `_login_with_qrcode()`: 扫码登录实现
- `_login_with_cookie()`: Cookie登录实现
- `_verify_credential()`: 验证凭证有效性

#### 2.2.2 异常类
- `LoginException`: 登录异常基类
- `NetworkError`: 网络连接错误
- `CredentialError`: 凭证错误
- `LoginTimeout`: 登录超时错误

## 3. 使用示例

### 3.1 基本使用

#### 3.1.1 简单登录
```python
import asyncio
from utils.login import BiliLogin
from config.settings import load_config

async def main():
    # 加载配置
    config = load_config()
    
    # 创建登录器
    login = BiliLogin(config)
    
    # 执行登录
    credential = await login.login()
    
    print(f"登录成功，用户ID: {credential.sessdata}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3.1.2 强制重新登录
```python
async def force_login():
    config = load_config()
    login = BiliLogin(config)
    
    # 强制重新登录，忽略已保存的凭证
    credential = await login.login(force_relogin=True)
    
    return credential
```

#### 3.1.3 检查登录状态
```python
async def check_status():
    config = load_config()
    login = BiliLogin(config)
    
    # 先尝试加载已保存的凭证
    await login._load_credential()
    
    # 检查登录状态
    is_valid, user_info = await login.check_login_status()
    
    if is_valid:
        print(f"登录有效，用户: {user_info.get('uname', '未知')}")
    else:
        print("登录已失效，需要重新登录")
```

### 3.2 配置使用

#### 3.2.1 自定义登录配置
```python
config = {
    "login": {
        "use_cookie": False,                 # 是否优先使用Cookie登录
        "credential_file": "config/credential.json",  # 凭证保存路径
        "verify_timeout": 180,               # 验证超时时间(秒)
        "max_retries": 3,                    # 最大重试次数
        "check_network": True,               # 是否检查网络连接
        "test_servers": [                    # 网络测试服务器
            "api.bilibili.com",
            "passport.bilibili.com"
        ]
    }
}

login = BiliLogin(config)
```

#### 3.2.2 Cookie登录配置
```python
config = {
    "login": {
        "use_cookie": True,                  # 启用Cookie登录
        "cookie_file": "config/cookies.json"  # Cookie文件路径
    }
}

login = BiliLogin(config)
credential = await login.login()
```

### 3.3 错误处理

#### 3.3.1 异常捕获
```python
from utils.login import BiliLogin, NetworkError, CredentialError, LoginTimeout

async def safe_login():
    config = load_config()
    login = BiliLogin(config)
    
    try:
        credential = await login.login()
        return credential
        
    except NetworkError as e:
        print(f"网络错误: {e}")
        # 可以尝试使用代理或稍后重试
        
    except CredentialError as e:
        print(f"凭证错误: {e}")
        # 需要重新获取凭证
        
    except LoginTimeout as e:
        print(f"登录超时: {e}")
        # 可以增加超时时间或重试
        
    except Exception as e:
        print(f"未知错误: {e}")
        
    return None
```

### 3.4 高级用法

#### 3.4.1 自定义网络检测
```python
async def custom_network_check():
    config = load_config()
    login = BiliLogin(config)
    
    # 自定义测试服务器
    login.login_config["test_servers"] = [
        "api.bilibili.com",
        "www.bilibili.com",
        "space.bilibili.com"
    ]
    
    # 执行网络检测
    is_connected = await login._check_network()
    
    if is_connected:
        print("网络连接正常")
    else:
        print("网络连接异常")
```

#### 3.4.2 凭证验证
```python
async def verify_saved_credential():
    config = load_config()
    login = BiliLogin(config)
    
    # 加载已保存的凭证
    if await login._load_credential():
        # 验证凭证是否仍然有效
        is_valid = await login._verify_credential()
        
        if is_valid:
            print("凭证有效")
            return login.credential
        else:
            print("凭证已失效")
            return None
    else:
        print("没有找到已保存的凭证")
        return None
```

## 4. 配置说明

### 4.1 登录配置项

```json
{
  "login": {
    "use_cookie": false,                    // 是否优先使用Cookie登录
    "cookie_file": "config/cookies.json",  // Cookie文件路径
    "credential_file": "config/credential.json",  // 凭证保存路径
    "verify_timeout": 180,                  // 验证超时时间(秒)
    "max_retries": 3,                       // 最大重试次数
    "retry_interval": 5,                    // 重试间隔(秒)
    "check_network": true,                  // 是否检查网络连接
    "network_timeout": 10,                  // 网络检查超时(秒)
    "test_servers": [                       // 测试服务器列表
      "api.bilibili.com",
      "passport.bilibili.com",
      "www.bilibili.com"
    ]
  }
}
```

### 4.2 凭证文件格式

```json
{
  "sessdata": "your_sessdata_here",
  "bili_jct": "your_bili_jct_here",
  "buvid3": "your_buvid3_here",
  "dedeuserid": "your_dedeuserid_here",
  "ac_time_value": "your_ac_time_value_here"
}
```

## 5. 依赖说明

### 5.1 必需依赖
- `bilibili-api-python`: B站API库
- `asyncio`: 异步编程支持
- `json`: JSON数据处理
- `pathlib`: 路径操作

### 5.2 可选依赖
- `qrcode`: 二维码生成（用于终端显示二维码）
- `rich`: 终端美化（用于二维码显示）

### 5.3 安装命令
```bash
# 必需依赖
pip install bilibili-api-python

# 可选依赖（用于终端二维码显示）
pip install qrcode rich
```

## 6. 常见问题

### 6.1 登录相关
- **问题**: 扫码登录超时
- **解决**: 增加`verify_timeout`配置值，或检查网络连接

### 6.2 凭证相关
- **问题**: 凭证验证失败
- **解决**: 删除旧凭证文件，重新登录

### 6.3 网络相关
- **问题**: 网络检测失败
- **解决**: 检查网络连接，或禁用网络检测(`check_network: false`)

---

**模块版本**: v1.0.0  
**最后更新**: 2025-01-20  
**维护者**: Claude 