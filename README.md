# 小蓝本数据采集工具

## 项目说明
这是一个用于采集小蓝本网站数据的自动化工具。可以采集公司的产品、媒体、网站、股东等相关信息。

## 项目结构
```
xiaolanben/
├── auth/                   # 认证相关
│   └── auth_manager.py     # 登录认证管理
├── crawler/                # 爬虫模块
│   ├── base_crawler.py     # 基础爬虫类
│   ├── group/             # 集团数据采集
│   │   ├── group_crawler.py       # 集团产品爬虫
│   │   ├── shareholder_crawler.py # 集团股东爬虫
│   │   └── data_extractor.py     # 数据提取器
│   └── company/           # 公司数据采集（待实现）
├── main.py                # 主程序入口
└── README.md             # 项目说明文档
```

## 环境要求
- Python 3.8+
- Chrome浏览器
- ChromeDriver（与Chrome版本匹配）

## 依赖安装
```bash
pip install selenium pandas openpyxl webdriver_manager
```

## 使用方法

### 基本使用
```bash
python main.py
```
这将使用默认设置运行程序，输出文件为 `xiaolanben.xlsx`。

### 自定义输出文件
```bash
python main.py -f custom_name
```
这将生成 `custom_name.xlsx` 作为输出文件。

## 输出文件说明
程序会在运行目录下生成Excel文件，包含以下工作表：
1. APP：包含APP名称和链接
2. Media：包含媒体名称和链接
3. Website：包含网站名称和链接
4. 集团成员：包含成员名称和链接
5. 对外投资：包含被投资方名称和链接
6. 投资方：包含投资方名称和链接

## 注意事项
1. 确保运行前已登录小蓝本账号
2. 每个标签页的内容会自动判断是否为空，空内容会跳过处理
3. 程序包含自动重试机制，最多重试3次
4. 数据保存时会自动处理文件已存在的情况

## 错误处理
1. 登录失效：程序会提示重新登录
2. 网络超时：自动重试机制
3. 内容为空：跳过处理并继续执行
4. 弹窗关闭失败：多种关闭方式尝试

## 开发计划
1. 添加公司数据采集功能
2. 优化数据提取效率
3. 添加更多自定义配置选项
4. 实现并发数据采集

## 维护者
[您的名字/组织]

## 许可证
MIT License 