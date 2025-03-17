# 小蓝本数据采集工具

## 项目说明
这是一个用于采集小蓝本网站数据的自动化工具。可以采集公司和集团的产品、媒体、网站、股东等相关信息。

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
│   └── company/            # 公司数据采集
│       └── company_crawler.py     # 公司产品爬虫
├── utils/                  # 工具类
│   └── browser_utils.py    # 浏览器工具
├── main.py                 # 主程序入口
├── config.json             # 配置文件
└── README.md               # 项目说明文档
```

## 环境要求
- Python 3.8+
- Chrome浏览器
- ChromeDriver（与Chrome版本匹配）

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

## 使用方法

### 采集集团数据
```bash
python main.py -g https://sou.xiaolanben.com/group/xxx --all
```

### 采集公司数据
```bash
python main.py -c https://sou.xiaolanben.com/company/xxx --all
```

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

4. **数据提取与处理**
   - 支持多种数据类型的提取
   - 数据自动保存到Excel的不同工作表
   - 支持追加模式和覆盖模式

5. **错误处理与重试机制**
   - 自动重试失败的操作（最多3次）
   - 异常处理和错误日志

## 输出文件说明
程序会在运行目录下生成Excel文件，包含以下工作表：
1. **APP**：包含APP名称和链接
2. **Media**：包含媒体名称和链接
3. **Website**：包含网站名称和链接
4. **集团成员**：包含成员名称和链接（仅集团数据）
5. **对外投资**：包含被投资方名称和链接（仅集团数据）
6. **投资方**：包含投资方名称和链接（仅集团数据）

## 开发计划
1. **公司详细数据采集**
   - 完善公司股东信息采集功能
   - 添加公司财务信息、法律信息等更详细数据的采集

2. **数据分析功能**
   - 添加基本数据分析和统计功能
   - 实现数据可视化展示

3. **性能优化**
   - 实现并发数据采集
   - 优化数据提取效率

4. **功能扩展**
   - 添加更多自定义配置选项
   - 支持多种数据导出格式（CSV、JSON等）
   - 实现定时自动执行采集任务
   - 添加代理IP支持
   - 实现验证码自动识别和处理

## 注意事项
1. 确保运行前已正确配置账号密码
2. 每个标签页的内容会自动判断是否为空，空内容会跳过处理
3. 程序包含自动重试机制，最多重试3次
4. 数据保存时会自动处理文件已存在的情况
5. 请合理使用，避免频繁请求导致账号被限制

## 错误处理
1. 登录失效：程序会提示重新登录
2. 网络超时：自动重试机制
3. 内容为空：跳过处理并继续执行
4. 弹窗关闭失败：多种关闭方式尝试

## 维护者
[您的名字/组织]

## 许可证
MIT License 