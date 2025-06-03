# Bilibili-API 系统架构

## 整体架构

Bilibili-API 采用模块化设计，将不同功能区分为独立的模块，便于维护和扩展。整体架构如下：

```mermaid
flowchart TD
    Client[客户端应用] --> Core[核心模块]
    Core --> Utils[工具模块]
    Core --> Exceptions[异常处理]
    Core --> Modules[功能模块]
    
    Utils --> Network[网络请求]
    Utils --> Danmaku[弹幕处理]
    Utils --> Credential[凭证管理]
    Utils --> Tools[辅助工具]
    
    Modules --> Video[视频模块]
    Modules --> Live[直播模块]
    Modules --> User[用户模块]
    Modules --> Dynamic[动态模块]
    Modules --> Audio[音频模块]
    Modules --> Article[专栏模块]
    Modules --> Search[搜索模块]
    Modules --> Message[消息模块]
    Modules --> Show[展示模块]
    Modules --> Other[其他模块]
    
    Network --> Clients[多客户端支持]
    Network --> AntiSpider[反反爬虫]
```

## 核心组件

### 1. 核心模块 (`bilibili_api/__init__.py`)

作为入口点，提供基础功能和全局设置，导出所有子模块和工具类。

### 2. 工具模块 (`bilibili_api/utils/`)

包含各种辅助功能的工具集合：

- **网络请求 (`network.py`)**：处理 HTTP 请求，支持多种请求库
- **凭证管理 (`Credential`)**：管理用户登录凭证
- **弹幕处理 (`danmaku.py`)**：处理弹幕相关功能
- **事件处理 (`AsyncEvent.py`)**：处理异步事件
- **人机验证 (`geetest.py`)**：处理极验验证码
- **AV/BV 互转 (`aid_bvid_transformer.py`)**：视频号格式转换

### 3. 异常处理 (`bilibili_api/exceptions/`)

定义各种可能出现的异常，提供统一的异常处理机制。

### 4. 功能模块 (`bilibili_api/`)

提供各种具体功能的模块，如视频、直播、用户等。

### 5. 数据模块 (`bilibili_api/data/`)

存储 API 接口和各种静态数据，使用 JSON 格式存储，便于跨语言使用。

### 6. 工具包 (`bilibili_api/tools/`)

提供额外的实用工具，如 IVI 文件管理、解析器等。

## 主要设计模式

### 1. 模块化设计

将不同功能划分为独立的模块，每个模块负责特定的功能领域，如视频、直播、用户等。

### 2. 工厂模式

通过 `select_client` 函数实现客户端工厂，根据需要选择不同的请求库实现。

```python
def select_client(client_name: str) -> None:
    """
    选择请求库

    Args:
        client_name (str): 请求库名称，支持 "aiohttp", "httpx", "curl_cffi"
    """
```

### 3. 单例模式

使用全局的 `request_settings` 对象管理请求设置，确保全局一致性。

### 4. 装饰器模式

使用装饰器实现各种功能的增强，如请求重试、异常处理等。

### 5. 策略模式

针对不同的请求库实现不同的请求策略，通过统一接口进行调用。

### 6. 观察者模式

通过 `AsyncEvent` 类实现异步事件通知机制，用于处理直播弹幕等实时数据。

### 7. 适配器模式

为不同的请求库实现适配器，提供统一的接口。

## 关键技术决策

### 1. 全异步设计

项目从 v5 版本开始全面采用异步设计，提高性能和并发能力。基于 `asyncio` 实现异步操作，所有网络请求都是异步的。

### 2. 多客户端支持

支持多种请求库 (`aiohttp`、`httpx`、`curl_cffi`)，用户可根据需要选择。按优先级自动选择可用的请求库，也可手动指定。

```python
from bilibili_api import select_client

select_client("curl_cffi")  # 选择 curl_cffi 作为请求库
```

### 3. 反反爬虫策略

实现多种反反爬虫策略，如 wbi 签名计算、buvid 刷新、bili_ticket 刷新、代理设置等。

```python
from bilibili_api import request_settings

request_settings.set_proxy("http://your-proxy.com")  # 设置代理
```

### 4. 凭证管理

通过 `Credential` 类统一管理用户凭证，支持各种验证方式。

```python
from bilibili_api import Credential

credential = Credential(sessdata="...", bili_jct="...", buvid3="...")
```

### 5. API 数据分离

将 API 接口信息存储在 JSON 文件中，与代码分离，便于维护和跨语言使用。

### 6. 同步执行支持

虽然主要使用异步，但提供 `sync` 函数将异步代码同步执行，方便不熟悉异步的用户。

```python
from bilibili_api import sync

result = sync(async_function())
```

## 数据流

### 请求流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant Module as 功能模块
    participant Network as 网络模块
    participant Server as 哔哩哔哩服务器

    Client->>Module: 调用功能模块方法
    Module->>Network: 构建请求参数
    Network->>Network: 添加认证信息
    Network->>Network: 计算wbi签名(如需)
    Network->>Network: 添加请求头
    Network->>Server: 发送HTTP请求
    Server->>Network: 返回响应数据
    Network->>Network: 检查状态码
    Network->>Network: 解析响应数据
    Network->>Module: 返回处理后的数据
    Module->>Client: 返回结果
```

### 直播弹幕流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant LiveDanmaku as 直播弹幕模块
    participant WebSocket as WebSocket客户端
    participant Server as 哔哩哔哩服务器

    Client->>LiveDanmaku: 创建弹幕实例
    LiveDanmaku->>WebSocket: 建立WebSocket连接
    WebSocket->>Server: 连接直播弹幕服务器
    WebSocket->>Server: 发送认证包
    Server->>WebSocket: 认证成功
    Server->>WebSocket: 发送弹幕数据
    WebSocket->>LiveDanmaku: 解析弹幕数据
    LiveDanmaku->>Client: 触发事件回调
```

## 扩展性设计

1. **模块化架构**：便于添加新的功能模块
2. **插件式请求库**：支持添加新的请求库适配器
3. **数据与代码分离**：API信息存储在JSON文件中，便于更新
4. **统一的异常处理**：便于添加新的异常类型
5. **事件驱动机制**：通过AsyncEvent支持事件处理

## 敏感视频爬虫项目架构

敏感视频爬虫项目是基于bilibili-api库开发的应用，用于采集和管理B站上的特定视频内容。项目采用模块化设计，各模块间通过明确的接口进行交互。

### 架构概览

```mermaid
flowchart TD
    Main[main.py] --> Config[配置模块]
    Main --> Login[登录模块]
    Main --> Search[搜索模块]
    Main --> Crawler[采集模块]
    Main --> Downloader[下载模块]
    Main --> Dataset[数据集模块]
    
    Login --> Credential[凭证管理]
    Login --> NetworkChecker[网络检测]
    Login --> RetryHandler[重试机制]
    
    Search --> Pagination[分页控制]
    Search --> Filter[结果过滤]
    Search --> QualityAssessor[质量评估]
    
    Crawler --> VideoInfo[视频信息]
    Crawler --> UserInfo[用户信息]
    
    Downloader --> VideoStream[视频流处理]
    Downloader --> AudioStream[音频流处理]
    Downloader --> Merger[音视频合并]
    
    Dataset --> MetaData[元数据管理]
    Dataset --> Storage[存储管理]
    Dataset --> Statistics[统计分析]
    
    Config --> All[所有模块]
```

### 登录模块

登录模块(`login.py`)负责处理B站账号登录、凭证管理和会话维护。该模块具有高可靠性和容错性，支持多种登录方式和自动重试机制。

#### 登录模块结构

```mermaid
classDiagram
    class BiliLogin {
        +config: dict
        +logger: Logger
        +credential: Credential
        +login_config: dict
        +login(force_relogin): Credential
        -_check_network(): bool
        -_login_with_qrcode(): void
        -_login_with_cookie(): void
        -_load_credential(): bool
        -_verify_credential(): bool
        -_save_credential(): bool
        +check_login_status(): Tuple[bool, dict]
        +logout(): bool
    }
    
    class LoginException {
        <<Exception>>
    }
    
    class NetworkError {
        <<Exception>>
    }
    
    class CredentialError {
        <<Exception>>
    }
    
    class LoginTimeout {
        <<Exception>>
    }
    
    LoginException <|-- NetworkError
    LoginException <|-- CredentialError
    LoginException <|-- LoginTimeout
```

#### 登录流程

```mermaid
sequenceDiagram
    participant Main as 主程序
    participant Login as 登录模块
    participant Network as 网络检测
    participant QRCode as 扫码登录
    participant Cookie as Cookie登录
    participant Verify as 凭证验证
    participant Storage as 凭证存储
    
    Main->>Login: 请求登录(force_relogin=False)
    
    alt 检查网络连接
        Login->>Network: 检查网络连接
        Network-->>Login: 返回连接状态
        
        alt 网络连接失败
            Login-->>Main: 抛出NetworkError
        end
    end
    
    alt 不强制重新登录
        Login->>Storage: 尝试加载已保存凭证
        alt 凭证存在且有效
            Storage-->>Login: 返回有效凭证
            Login->>Verify: 验证凭证
            Verify-->>Login: 凭证有效
            Login-->>Main: 返回凭证
        end
    end
    
    alt 登录重试循环
        loop 最大重试次数
            alt 使用Cookie登录
                Login->>Cookie: 尝试Cookie登录
                Cookie-->>Login: 返回凭证
            else 使用扫码登录
                Login->>QRCode: 获取登录二维码
                QRCode-->>Login: 显示二维码
                Login->>QRCode: 等待扫码
                QRCode-->>Login: 返回凭证
            end
            
            Login->>Verify: 验证凭证
            alt 验证成功
                Verify-->>Login: 凭证有效
                Login->>Storage: 保存凭证
                Storage-->>Login: 保存成功
                Login-->>Main: 返回凭证
            else 验证失败
                Verify-->>Login: 凭证无效
                Login->>Login: 准备重试
            end
        end
    end
    
    alt 所有重试失败
        Login-->>Main: 抛出LoginException
    end
```

#### 错误处理与重试机制

登录模块实现了全面的错误处理和自动重试机制，主要包括：

1. **异常分类**：
   - `LoginException`: 登录异常基类
   - `NetworkError`: 网络连接错误
   - `CredentialError`: 凭证错误
   - `LoginTimeout`: 登录超时错误

2. **重试策略**：
   - 最大重试次数可配置
   - 重试间隔采用指数退避策略
   - 不同类型错误采用不同处理策略

3. **网络故障检测**：
   - 登录前检查网络连接
   - 支持多服务器测试
   - TCP和HTTP双重检测
   - 自定义超时设置

#### 与其他模块交互

登录模块作为基础设施，为其他模块提供认证支持：

1. **与搜索模块交互**：提供经过认证的请求凭证，用于执行搜索操作
2. **与采集模块交互**：提供凭证以获取完整视频信息和统计数据
3. **与下载模块交互**：提供凭证以获取视频下载链接和权限

### 搜索模块

// ... existing code ... 