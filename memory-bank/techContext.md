# Bilibili-API 技术环境

## 技术栈

### 编程语言

- **Python**: 3.9+（支持 3.9、3.10、3.11、3.12、3.13）

### 核心技术

- **asyncio**: 异步IO操作
- **aiohttp/httpx/curl_cffi**: 异步HTTP请求
- **JSON**: API数据存储和交换格式
- **WebSocket**: 直播弹幕连接

### 设计方法

- 模块化架构
- 面向对象编程
- 异步编程
- 装饰器模式
- 工厂模式
- 适配器模式

## 依赖项

### 核心依赖

```
beautifulsoup4~=4.13.3  # HTML解析
colorama~=0.4.6        # 终端着色
lxml~=5.3.1            # XML处理
pyyaml~=6.0            # YAML文件处理
brotli~=1.1.0          # HTTP压缩
qrcode~=8.0            # 二维码生成
APScheduler~=3.11.0    # 任务调度
pillow~=11.1.0         # 图像处理
yarl~=1.18.3           # URL解析
pycryptodomex~=3.21.0  # 加密功能
qrcode_terminal~=0.8   # 终端二维码
PyJWT~=2.10.1          # JWT处理
```

### 可选依赖（用户自行安装）

```
aiohttp       # 异步HTTP客户端
httpx         # 现代HTTP客户端
curl_cffi     # 支持TLS指纹伪装的HTTP客户端
```

### 敏感视频爬虫项目依赖

```
bilibili-api-python    # 哔哩哔哩API库
aiohttp               # 异步HTTP客户端（推荐）
pyyaml                # YAML配置文件处理
pillow                # 图像处理
qrcode                # 二维码生成
qrcode_terminal       # 终端二维码显示
ffmpeg-python         # 音视频处理
tqdm                  # 进度条显示
colorlog              # 彩色日志
```

## 开发环境

### 推荐开发环境

- **操作系统**: 跨平台支持 (Windows, macOS, Linux)
- **Python版本**: 3.9+
- **IDE**: 支持Python的任意IDE (如VSCode, PyCharm)
- **包管理**: pip, conda 或 poetry
- **版本控制**: Git
- **测试框架**: pytest
- **CI/CD**: GitHub Actions

### 环境设置步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/Nemo2011/bilibili-api.git
   cd bilibili-api
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 安装可选HTTP客户端（至少选一个）
   ```bash
   pip install aiohttp  # 或 httpx 或 curl_cffi
   ```

4. 安装开发依赖
   ```bash
   pip install pytest black flake8  # 测试和代码格式化工具
   ```

## 文件结构组织

```
bilibili-api/
├── bilibili_api/           # 主模块
│   ├── __init__.py         # 模块初始化和公共导出
│   ├── _pyinstaller/       # PyInstaller支持
│   ├── clients/            # 客户端实现
│   ├── data/               # API数据和静态资源
│   │   ├── api/            # API接口定义（JSON格式）
│   │   └── geetest/        # 极验验证相关资源
│   ├── exceptions/         # 异常类定义
│   ├── tools/              # 工具集
│   │   ├── ivitools/       # IVI文件工具
│   │   └── parser/         # 解析器工具
│   └── utils/              # 实用工具
├── CHANGELOGS/             # 更新日志
├── design/                 # 设计资源
├── docs/                   # 文档
├── scripts/                # 辅助脚本
├── tests/                  # 测试用例
├── .editorconfig           # 编辑器配置
├── .gitignore              # Git忽略文件
├── install.py              # 安装脚本
├── LICENSE                 # 许可证
├── pyproject.toml          # 项目配置
├── README.md               # 项目说明
├── requirements.txt        # 依赖清单
└── SECURITY.md             # 安全策略
```

## 包结构和组织

### 核心包结构

- **bilibili_api**: 主包
  - **utils**: 工具和辅助函数
  - **exceptions**: 异常定义
  - **clients**: 客户端实现
  - **data**: 数据文件
  - **tools**: 工具集合

### 模块组织

模块按功能划分，每个模块对应B站的一个主要功能领域：

- **video.py**: 视频相关功能
- **live.py**: 直播相关功能
- **user.py**: 用户相关功能
- **dynamic.py**: 动态相关功能
- **audio.py**: 音频相关功能
- **article.py**: 专栏相关功能
- **search.py**: 搜索相关功能
- **message.py**: 消息相关功能
- **show.py**: 展示相关功能
- 其他功能模块...

## 技术约束

### 语言和版本约束

- 仅支持Python 3.9及以上版本
- 全面使用异步编程，同步代码需通过sync包装器调用

### API约束

- B站API可能随时变动，需保持关注和更新
- 受B站反爬虫机制限制，请求频率过高可能触发风控
- 部分功能需要登录凭证才能使用

### 安全约束

- 用户凭证敏感信息不应明文存储或传输
- 避免在公开环境中暴露登录凭证
- 遵循B站用户协议，不进行恶意操作

### 性能约束

- 异步请求应注意并发量控制，避免触发风控
- 对于需要大量请求的操作，应实现适当的延迟机制
- 处理大量数据时注意内存占用

### 兼容性约束

- 跨平台兼容：代码需兼容Windows、macOS和Linux
- 请求库兼容：需支持多种HTTP客户端库

## 构建和发布

### 构建流程

使用setuptools进行包构建：

```bash
python -m build
```

### 发布渠道

- **主版本**: PyPI (bilibili-api-python)
- **开发版本**: PyPI (bilibili-api-dev)
- **最新代码**: GitHub (dev分支)

### 版本管理

- 版本号格式: X.Y.Z
- 版本定义在 bilibili_api.BILIBILI_API_VERSION
- 通过pyproject.toml的动态版本机制管理

## 测试策略

- **单元测试**: 测试各个功能模块的独立功能
- **集成测试**: 测试模块间的交互
- **自动化测试**: 通过GitHub Actions自动运行测试
- **手动测试**: 针对需要人工干预的功能（如登录流程）

## CI/CD流程

通过GitHub Actions实现：

- **代码检查**: 运行代码格式检查和静态分析
- **自动测试**: 运行自动化测试套件
- **构建检查**: 验证构建过程
- **文档生成**: 自动更新文档

## 敏感视频爬虫项目技术细节

### 登录模块技术实现

登录模块(`bilibili_sensitive_crawler/utils/login.py`)实现了高可靠性的B站账号登录功能，主要技术特点包括：

1. **多登录方式支持**：
   - 扫码登录（QR Code）：使用`bilibili_api.login.login_with_qrcode`
   - Cookie登录：使用`bilibili_api.login.login_with_cookie`

2. **网络连接检测**：
   - TCP连接测试：使用`asyncio.open_connection`
   - HTTP连接测试：使用`aiohttp.ClientSession`
   - 多服务器检测：自动尝试多个B站服务器
   - 超时控制：自定义超时时间

3. **异步实现**：
   - 基于`asyncio`的异步编程
   - 异步超时控制：使用`asyncio.wait_for`
   - 异步重试机制：使用递增延时策略

4. **凭证管理**：
   - 安全存储：JSON格式保存凭证
   - 自动加载：启动时尝试加载已有凭证
   - 凭证验证：使用`bilibili_api.login.get_user_info`验证凭证有效性

5. **错误处理策略**：
   - 异常分类：区分网络错误、凭证错误、超时错误等
   - 自动重试：根据错误类型采用不同重试策略
   - 详细日志：记录每个步骤的执行状态和错误信息

6. **配置灵活性**：
   - YAML驱动配置：所有参数可通过配置文件调整
   - 默认值机制：提供合理默认值，确保基本功能可用
   - 运行时配置：支持强制重新登录等运行时行为控制

### 搜索模块技术实现

// ... existing code ...

## 安全与性能考虑

### 安全特性

1. **登录凭证保护**：
   - 本地加密存储登录凭证
   - 避免凭证明文传输
   - 定期验证凭证有效性

2. **网络安全**：
   - 安全的HTTPS连接
   - 合理的请求频率控制
   - 防封禁策略

3. **数据安全**：
   - 敏感数据本地存储
   - 用户信息保护

### 性能优化

1. **网络性能**：
   - 异步请求处理
   - 连接池复用
   - 超时控制和自动重试
   - 智能退避策略

2. **存储性能**：
   - 结构化数据组织
   - 增量更新机制
   - 高效索引结构

3. **计算性能**：
   - 多级缓存策略
   - 并发下载控制
   - 资源使用限制

## 测试策略

// ... existing code ... 