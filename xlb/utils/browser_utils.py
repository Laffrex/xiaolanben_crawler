from selenium import webdriver

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
    
    return webdriver.Chrome(options=options) 