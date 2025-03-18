# Selenium到Playwright迁移方案

## 1. 项目背景

目前的项目使用Selenium完成自动化爬取小蓝本的功能，现在计划迁移到Playwright以提高效率和可靠性。

## 2. 迁移策略

采用渐进式迁移策略，先完成关键模块迁移，再逐步替换其他模块：

1. 第一阶段：基础设施层迁移
   - 浏览器初始化模块
   - 认证管理模块
   - 基础爬虫类

2. 第二阶段：业务模块迁移
   - 数据提取器迁移
   - 集团爬虫迁移
   - 公司爬虫迁移

3. 第三阶段：优化与测试
   - 利用Playwright特性优化
   - 完整流程测试
   - 性能测试与对比

## 3. 详细迁移计划

### 3.1 环境准备

```bash
# 安装Playwright
pip install playwright
# 安装Playwright浏览器
python -m playwright install
```

更新requirements.txt：
```
playwright>=1.40.0
pandas>=2.1.3
openpyxl>=3.1.2
pillow>=10.1.0
opencv-python>=4.8.1.78
numpy>=1.26.2
requests>=2.31.0
beautifulsoup4>=4.12.2
lxml>=4.9.3
tqdm>=4.66.1
python-dotenv>=1.0.0
```

### 3.2 核心模块迁移

#### 3.2.1 浏览器工具模块 (browser_utils.py)

| 状态 | ❌ 未完成 |
| --- | --- |
| 文件 | xlb/utils/browser_utils.py |
| 迁移要点 | 从Selenium的webdriver迁移到Playwright的Sync API |

计划修改：
```python
from playwright.sync_api import sync_playwright

def init_browser():
    """初始化浏览器"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=False,
        args=[
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            '--ignore-certificate-errors',
            '--disable-web-security',
            '--disable-gpu',
            '--no-sandbox',
        ]
    )
    context = browser.new_context(
        viewport=None,  # 最大化窗口
        ignore_https_errors=True,
        java_script_enabled=True,
    )
    # 设置用户代理
    context.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    })
    
    page = context.new_page()
    # 返回所有需要的对象，以便于在需要时关闭
    return {
        "playwright": playwright,
        "browser": browser, 
        "context": context,
        "page": page
    }
```

#### 3.2.2 认证管理器 (auth_manager.py)

| 状态 | ❌ 未完成 |
| --- | --- |
| 文件 | xlb/auth/auth_manager.py |
| 迁移要点 | 修改元素定位和操作方式 |

计划修改：
```python
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import json

class AuthManager:
    def __init__(self, page_context):
        self.page = page_context["page"]
        self.load_credentials()

    def load_credentials(self):
        """从配置文件加载登录凭证"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.username = config['username']
                self.password = config['password']
                self.login_url = config['login_url']
        except FileNotFoundError:
            print("请先创建配置文件 config.json")
            exit(1)

    def login(self):
        """执行登录操作"""
        try:
            # 打开登录页面
            print("正在打开登录页面...")
            self.page.goto(self.login_url)
            
            print("页面已打开，正在查找登录表单...")
            
            # 等待并找到用户名输入框
            print("找到手机号输入框，正在输入...")
            self.page.fill('input[name="phone"]', self.username)
            
            # 找到密码输入框
            print("正在输入密码...")
            self.page.fill('input[name="password"]', self.password)
            
            # 点击同意协议按钮
            print("正在点击同意协议按钮...")
            try:
                self.page.click('.checkmark')
                print("已点击同意协议按钮")
            except PlaywrightTimeoutError:
                print("找不到同意协议按钮或按钮不可点击")
                raise
            
            # 点击登录按钮
            print("正在点击登录按钮...")
            try:
                self.page.click('.login-submit')
                print("已点击登录按钮")
            except PlaywrightTimeoutError:
                print("找不到登录按钮或按钮不可点击")
                raise
            
            # 等待登录成功
            print("等待页面跳转...")
            try:
                # 等待URL改变
                self.page.wait_for_url(lambda url: self.login_url not in url, timeout=10000)
                print(f"当前URL: {self.page.url}")
                print("登录成功！")
                return True
            except PlaywrightTimeoutError:
                print("登录可能失败，请检查登录状态")
                print(f"当前URL: {self.page.url}")
                return False
            
        except PlaywrightTimeoutError:
            print("登录超时，请检查网络连接或登录信息")
            return False
        except Exception as e:
            print(f"登录过程中出现错误: {str(e)}")
            print(f"当前URL: {self.page.url}")
            return False
```

#### 3.2.3 基础爬虫类 (base_crawler.py)

| 状态 | ❌ 未完成 |
| --- | --- |
| 文件 | xlb/crawler/base_crawler.py |
| 迁移要点 | 修改基础操作方法 |

计划修改：
```python
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import time

class BaseCrawler:
    def __init__(self, page_context, output_file):
        self.page = page_context["page"]
        self.output_file = output_file

    def check_login_status(self):
        """检查登录状态"""
        if "login" in self.page.url:
            print("登录状态已失效，需要重新登录")
            return False
        return True

    def close_dialog(self):
        """关闭弹出框"""
        try:
            print("\n正在关闭弹出框...")
            # 尝试找到弹出框
            if self.page.locator(".el-dialog__wrapper").count() > 0:
                # 点击弹出框外的区域来关闭它
                self.page.mouse.click(0, 0)  # 点击页面左上角
                # 等待弹出框消失
                self.page.wait_for_selector(".el-dialog__wrapper", state="hidden", timeout=5000)
                print("弹出框已关闭")
                time.sleep(2)  # 给页面一些时间来响应
                return True
        except Exception as e:
            print(f"关闭弹出框时出错: {str(e)}")
            # 尝试使用 Escape 键关闭
            try:
                self.page.keyboard.press("Escape")
                time.sleep(2)
                print("使用 Escape 键关闭弹出框")
                return True
            except Exception as e2:
                print(f"使用 Escape 键关闭弹出框时出错: {str(e2)}")
                return False
```

### 3.3 主程序入口修改 (main.py)

| 状态 | ❌ 未完成 |
| --- | --- |
| 文件 | main.py |
| 迁移要点 | 修改浏览器初始化和关闭逻辑 |

计划修改：
```python
import argparse
import os
from xlb.auth.auth_manager import AuthManager
from xlb.utils.browser_utils import init_browser
# ... 其他导入保持不变

def main():
    """主程序入口"""
    args = parse_arguments()
    
    # ... 参数处理部分保持不变
    
    try:
        # 使用新的浏览器初始化函数
        browser_context = init_browser()
        
        # 创建认证管理器，传入新的浏览器上下文
        auth_manager = AuthManager(browser_context)
        
        # 执行登录
        print("\n开始登录...")
        if not auth_manager.login():
            print("登录失败，程序退出")
            return
        
        # ... 业务逻辑部分保持不变，只修改实例化爬虫类时传入的参数
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        # 等待用户确认后关闭浏览器
        input("\n按回车键关闭浏览器...")
        # 关闭浏览器和Playwright
        if 'browser_context' in locals():
            browser_context["browser"].close()
            browser_context["playwright"].stop()
```

### 3.4 数据提取器迁移 (data_extractor.py)

| 状态 | ❌ 未完成 |
| --- | --- |
| 文件 | xlb/crawler/data_extractor.py |
| 迁移要点 | 修改元素定位、操作和等待机制 |

### 3.5 具体爬虫类迁移

| 状态 | ❌ 未完成 |
| --- | --- |
| 文件 | xlb/crawler/group/*, xlb/crawler/company/*, xlb/crawler/companys_in_group/* |
| 迁移要点 | 修改元素定位和操作方式 |

## 4. API对照表

| Selenium API | Playwright API |
| ------------ | -------------- |
| `driver.get(url)` | `page.goto(url)` |
| `driver.find_element(By.ID, "id")` | `page.locator("#id")` |
| `driver.find_element(By.CSS_SELECTOR, "selector")` | `page.locator("selector")` |
| `element.send_keys("text")` | `page.fill("selector", "text")` |
| `element.click()` | `page.click("selector")` |
| `element.text` | `page.locator("selector").text_content()` |
| `element.get_attribute("attr")` | `page.locator("selector").get_attribute("attr")` |
| `WebDriverWait(driver, 10).until(...)` | `page.wait_for_selector("selector")` |
| `ActionChains(driver).move_to_element(element)` | `page.hover("selector")` |
| `driver.execute_script("script")` | `page.evaluate("script")` |
| `driver.switch_to.frame(frame)` | `page.frame_locator("selector").locator(...)` |
| `driver.switch_to.default_content()` | 不需要，自动处理 |

## 5. 迁移进度跟踪

| 模块 | 状态 | 负责人 | 完成日期 |
| ---- | ---- | ------ | -------- |
| browser_utils.py | ❌ 未开始 | TBD | - |
| auth_manager.py | ❌ 未开始 | TBD | - |
| base_crawler.py | ❌ 未开始 | TBD | - |
| main.py | ❌ 未开始 | TBD | - |
| data_extractor.py | ❌ 未开始 | TBD | - |
| 集团爬虫模块 | ❌ 未开始 | TBD | - |
| 公司爬虫模块 | ❌ 未开始 | TBD | - |
| 集团成员爬虫模块 | ❌ 未开始 | TBD | - |

## 6. 潜在问题与解决方案

1. **问题**: Selenium特有API无直接对应
   **解决方案**: 使用Playwright的替代功能或自定义实现

2. **问题**: 元素定位策略差异
   **解决方案**: 优化选择器，利用Playwright强大的定位机制

3. **问题**: 截图和日志记录方式差异
   **解决方案**: 开发适配Playwright的截图和日志模块

4. **问题**: 框架间调试工具差异
   **解决方案**: 利用Playwright内置的调试功能，如`playwright codegen`

## 7. Playwright优势利用

1. **自动等待**: 利用Playwright自动等待元素可交互特性减少显式等待代码
2. **网络拦截**: 使用`route`和`request`拦截功能优化请求
3. **并发执行**: 使用多上下文并发执行提高效率
4. **视觉比较**: 利用`screenshot`和比较功能增强测试
5. **移动设备模拟**: 使用`devices`模拟移动端访问

## 8. 回滚策略

1. 保留原有Selenium代码
2. 在`browser_utils.py`中提供切换机制
3. 通过环境变量控制使用哪个框架 