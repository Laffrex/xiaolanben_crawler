import os
import sys
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service

def get_driver_path():
    """获取ChromeDriver路径"""
    # 获取项目根目录路径
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    driver_path = os.path.join(current_dir, 'drivers', 'chromedriver.exe')
    
    if not os.path.exists(driver_path):
        raise FileNotFoundError(
            "\n未找到ChromeDriver！\n"
            "请按以下步骤操作：\n"
            "1. 确认Chrome浏览器版本（chrome://version）\n"
            "2. 下载对应版本的ChromeDriver\n"
            "3. 将chromedriver.exe放入drivers目录\n"
            "4. 重新运行程序\n\n"
            "详细说明请查看 drivers/README.txt"
        )
    
    return driver_path

def init_driver():
    """初始化浏览器驱动"""
    # 重定向标准错误流到null设备来隐藏错误消息
    import os
    import io
    import sys
    
    # 保存原始stderr
    original_stderr = sys.stderr
    
    # 创建一个空的输出流来捕获错误消息
    null_output = io.StringIO()
    sys.stderr = null_output
    
    options = webdriver.ChromeOptions()
    # 添加一些常用选项
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # SSL 相关配置
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--ignore-urlfetcher-cert-requests')
    
    # 禁用 WebRTC 以避免 STUN 服务器错误
    options.add_argument('--disable-webrtc')
    
    # 其他优化选项
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 禁用图像相关警告
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--force-color-profile=srgb')
    
    # 完全禁用WebGL
    options.add_argument('--disable-webgl')
    options.add_argument('--disable-3d-apis')
    
    # 设置日志级别
    options.add_argument('--log-level=3')  # 只显示 FATAL 级别的日志
    
    # 禁用所有日志输出
    options.add_argument('--silent')
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 添加一个自定义用户代理以避免一些检测
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    
    # 关闭扩展以减少日志
    options.add_argument('--disable-extensions')
    
    # 禁用开发者工具
    options.add_argument('--disable-dev-tools')
    
    # 设置浏览器首选项以禁用图片错误
    prefs = {
        'profile.default_content_setting_values.notifications': 2,
        'profile.managed_default_content_settings.images': 1,
        'browser.enable_spellchecking': 0,
        'browser.enable_autospell': 0,
        'browser.helperApps.alwaysAsk.force': 0,
        'browser.download.manager.showWhenStarting': 0,
        'browser.download.manager.focusWhenStarting': 0,
        'browser.download.manager.alertOnEXEOpen': 0,
        'browser.download.manager.closeWhenDone': 1
    }
    options.add_experimental_option('prefs', prefs)
    
    try:
        driver_path = get_driver_path()

        # 根据Python版本使用不同的初始化方式
        if sys.version_info >= (3, 9):
            # Python 3.9+ 使用 Service 类
            from selenium.webdriver.chrome.service import Service
            service = Service(driver_path)
            # 设置Service不显示任何输出
            service.creationflags = 0x08000000  # CREATE_NO_WINDOW
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Python 3.8 及以下版本使用 executable_path
            driver = webdriver.Chrome(executable_path=driver_path, options=options)
            
        # 恢复原始stderr
        sys.stderr = original_stderr
        
        return driver

    except WebDriverException as e:
        # 恢复原始stderr以显示错误消息
        sys.stderr = original_stderr
        
        if "version" in str(e).lower():
            raise WebDriverException(
                "\nChrome浏览器与ChromeDriver版本不匹配！\n"
                "请按以下步骤操作：\n"
                "1. 检查Chrome浏览器版本（chrome://version）\n"
                "2. 下载完全匹配的ChromeDriver版本\n"
                "3. 替换drivers目录中的chromedriver.exe\n"
                "4. 重新运行程序\n\n"
                "详细说明请查看 drivers/README.txt"
            )
        raise
    except Exception as e:
        # 恢复原始stderr以显示错误消息
        sys.stderr = original_stderr
        raise 