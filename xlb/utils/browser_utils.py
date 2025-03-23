import os
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
    
    # WebGL 相关配置
    options.add_argument('--use-gl=desktop')  # 使用桌面OpenGL
    options.add_argument('--enable-unsafe-swiftshader')  # 启用SwiftShader
    
    # 设置日志级别
    options.add_argument('--log-level=3')  # 只显示 FATAL 级别的日志
    
    # 禁用日志输出
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # 禁用一些可能导致警告的功能
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver_path = get_driver_path()
        service = Service(driver_path)
        return webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
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