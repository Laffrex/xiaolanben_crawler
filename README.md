# 小蓝本数据采集工具

## 项目说明
这是一个用于采集小蓝本网站数据的自动化工具，支持采集公司和集团的产品、媒体、网站、股东等相关信息。工具具有自动处理弹窗、智能重试、错误恢复和递归提取功能，提高了数据采集的效率和稳定性。

## 项目结构
```
xiaolanben/
├── auth/                   # 认证相关
│   └── auth_manager.py     # 登录认证管理
├── crawler/                # 爬虫模块
│   ├── base_crawler.py     # 基础爬虫类
│   ├── crawler_manager.py  # 爬虫管理器
│   ├── data_extractor.py   # 数据提取器
│   ├── group/              # 集团数据采集
│   │   ├── group_crawler.py       # 集团产品爬虫
│   │   └── shareholder_crawler.py # 集团股东爬虫
│   ├── company/            # 公司数据采集
│   │   └── company_crawler.py     # 公司产品爬虫
│   └── companys_in_group/  # 集团成员数据采集
│       └── group_members_crawler.py # 集团成员递归爬虫
├── utils/                  # 工具类
│   ├── browser_utils.py    # 浏览器工具
│   └── excel_manager.py    # Excel文件管理工具
├── main.py                 # 主程序入口
├── config.json             # 配置文件
└── README.md               # 项目说明文档
```

## 环境要求
- Python 3.8+
- Chrome浏览器
- ChromeDriver（与Chrome版本匹配）

## ChromeDriver配置
首次使用前，请按以下步骤配置ChromeDriver：

1. 查看Chrome版本
   - 打开Chrome浏览器
   - 点击右上角三个点
   - 点击"帮助" -> "关于Google Chrome"
   - 记下版本号（例如：115.0.5790.171）

2. 下载ChromeDriver
   - 访问：https://sites.google.com/chromium.org/driver/
   - 下载与Chrome版本匹配的chromedriver_win32.zip

3. 配置驱动
   - 解压下载的zip文件
   - 将chromedriver.exe放入项目的drivers目录下
   - 确保文件名为"chromedriver.exe"

注意：如果更新了Chrome浏览器，需要重新下载对应版本的ChromeDriver。或者使用`webdriver_manager`库自动安装与浏览器匹配的驱动。

## 依赖安装
```bash
pip install -r requirements.txt
```

## 配置文件
在运行程序前，请先配置 `config.json` 文件：
```json
{
    "username": "您的小蓝本账号",
    "password": "您的小蓝本密码",
    "login_url": "https://sou.xiaolanben.com/login"
}
```

## 命令行参数说明
程序支持以下命令行参数：

### 必需参数（二选一）
- `-g, --group`: 集团页面的URL，例如：`https://sou.xiaolanben.com/group/xxx`
- `-c, --company`: 公司页面的URL，例如：`https://sou.xiaolanben.com/company/xxx`

### 可选参数
- `-f, --filename`: 输出Excel文件名（不需要包含.xlsx扩展名）
- `--all`: 提取所有可用数据（默认选项）
- `--shareholders`: 仅提取集团股东数据
- `--products`: 仅提取产品数据（APP、Media、Website）
- `--recursive`: 递归提取集团成员的公司数据
- `--members-output`: 集团成员数据输出文件名（不需要包含.xlsx扩展名），默认与集团数据使用相同的文件

### 参数使用示例
```bash
# 提取集团所有数据
python main.py -g https://sou.xiaolanben.com/group/xxx --all

# 提取公司数据并指定输出文件名
python main.py -c https://sou.xiaolanben.com/company/xxx --all -f custom_name

# 仅提取集团股东数据
python main.py -g https://sou.xiaolanben.com/group/xxx --shareholders

# 递归提取集团成员数据并指定输出文件名
python main.py -g https://sou.xiaolanben.com/group/xxx --recursive --members-output custom_members

# 同时提取股东数据和递归提取集团成员数据
python main.py -g https://sou.xiaolanben.com/group/xxx --shareholders --recursive
```

## 主要功能

### 采集集团数据
```bash
python main.py -g https://sou.xiaolanben.com/group/xxx --all
```
这将采集集团的所有数据，包括产品信息和股东信息。

### 采集公司数据
```bash
python main.py -c https://sou.xiaolanben.com/company/xxx --all
```
这将采集公司的所有产品信息。

### 自定义输出文件
```bash
python main.py -g https://sou.xiaolanben.com/group/xxx --all -f custom_name
```
这将生成 `custom_name.xlsx` 作为输出文件。

### 选择性采集
```bash
# 仅采集股东数据
python main.py -g https://sou.xiaolanben.com/group/xxx --shareholders

# 仅采集产品数据
python main.py -g https://sou.xiaolanben.com/group/xxx --products
```

### 递归提取集团成员数据
```bash
python main.py -g https://sou.xiaolanben.com/group/xxx --recursive
```
这将遍历集团的所有成员，并对每个成员公司进行数据采集。递归提取的数据会存储在一个单独的Excel文件中：
- 如果使用默认文件名，数据会存储在`xiaolanben_group_recursive.xlsx`
- 如果使用自定义文件名（例如`custom_name.xlsx`），数据会存储在`custom_name_recursive.xlsx`
- 如果指定了`--members-output`，则使用指定的文件名

## 已实现功能
1. **认证管理**
   - 通过配置文件加载用户名和密码
   - 自动登录小蓝本网站
   - 登录状态检查和维护

2. **集团数据采集**
   - 集团产品信息采集（APP、媒体、网站）
   - 集团股东信息采集（集团成员、对外投资、投资方）
   - 数据自动分类并保存到Excel文件

3. **公司数据采集**
   - 公司产品信息采集（APP、媒体、网站）
   - 数据自动分类并保存到Excel文件

4. **递归数据采集**
   - 递归提取集团成员的公司数据
   - 支持自定义输出文件
   - 智能文件命名和处理

5. **数据提取与处理**
   - 支持多种数据类型的提取
   - 数据自动保存到Excel的不同工作表
   - 支持追加模式和合并现有数据
   - 智能处理"查看更多"弹窗
   - 自动滚动加载更多内容
   - 高效的数据去重机制

6. **资源管理**
   - 自动垃圾回收
   - 优化内存使用
   - 更高效的资源释放

7. **错误处理与重试机制**
   - 自动重试失败的操作（最多3次）
   - 异常处理和错误日志
   - 智能弹窗关闭策略（点击弹窗外部、ESC键、页面刷新）
   - 优雅的错误恢复机制

8. **Excel文件管理**
   - 集中式Excel文件管理
   - 智能表格初始化和验证
   - 文件锁定机制避免并发访问冲突

## 输出文件说明
程序会在运行目录下生成Excel文件，包含以下工作表：

### 集团数据文件
1. **APP**：包含APP名称和链接
2. **Website**：包含网站名称和链接
3. **微信公众号**：包含公众号名称和链接
4. **微信小程序**：包含小程序名称和链接
5. **其他媒体**：包含其他媒体平台名称和链接
6. **集团成员**：包含成员名称和链接
7. **对外投资**：包含被投资方名称和链接
8. **投资方**：包含投资方名称和链接

### 公司数据文件
1. **APP**：包含APP名称和链接
2. **Website**：包含网站名称和链接
3. **微信公众号**：包含公众号名称和链接
4. **微信小程序**：包含小程序名称和链接
5. **其他媒体**：包含其他媒体平台名称和链接

### 递归提取的集团成员数据文件
1. **APP**：包含成员公司APP名称和链接
2. **Website**：包含成员公司网站名称和链接
3. **微信公众号**：包含成员公司公众号名称和链接
4. **微信小程序**：包含成员公司小程序名称和链接
5. **其他媒体**：包含成员公司其他媒体平台名称和链接

## 注意事项
1. 确保运行前已正确配置账号密码
2. 每个标签页的内容会自动判断是否为空，空内容会跳过处理
3. 程序包含自动重试机制，最多重试3次
4. 数据保存时会自动处理文件已存在的情况，合并新旧数据并去重
5. 请合理使用，避免频繁请求导致账号被限制
6. 程序会自动处理"查看更多"弹窗，无需手动干预
7. 如遇到弹窗关闭失败，程序会自动尝试多种关闭方式
8. 递归提取可能耗时较长，请耐心等待
9. 使用`--recursive`参数时，数据会保存到单独的文件中

## 错误处理
1. 登录失效：程序会提示重新登录
2. 网络超时：自动重试机制
3. 内容为空：跳过处理并继续执行
4. 弹窗关闭失败：多种关闭方式尝试（点击弹窗外部、ESC键、页面刷新）
5. 数据提取失败：自动跳过并继续处理其他数据
6. 页面加载超时：自动刷新并重试
7. 内存管理：定期释放资源并执行垃圾回收

## 最近更新
1. 添加了递归提取集团成员数据功能
2. 优化了弹窗关闭机制，现在通过点击弹窗外部区域关闭
3. 改进了数据提取器，支持不同页面结构的智能适配
4. 增强了Excel文件管理，集中处理文件操作
5. 优化了资源管理，减少内存占用
6. 统一了控制台输出格式，提高可读性
7. 支持自定义递归数据输出文件名

## 维护者
[Laffrex]

## 许可证
MIT License 
