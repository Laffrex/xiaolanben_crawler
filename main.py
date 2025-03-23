import argparse
import os
import gc
import time
import sys
import io
import warnings
import ctypes
from xlb.auth.auth_manager import AuthManager
from xlb.utils.browser_utils import init_driver
from xlb.crawler.group.shareholder_crawler import ShareholderCrawler as GroupShareholderCrawler
from xlb.crawler.group.group_crawler import GroupCrawler
from xlb.crawler.company.company_crawler import CompanyCrawler
from xlb.crawler.companys_in_group.group_members_crawler import GroupMembersCrawler
from xlb.utils.excel_manager import ExcelFileManager
from colorama import Fore, Style, init

# 设置环境变量来禁用警告
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
os.environ['PYTHONIOENCODING'] = 'utf-8'
# 禁用PIL的基于libpng的警告
os.environ['KIVY_NO_CONSOLELOG'] = '1'
# 禁用WebGL错误
os.environ['PYOPENGL_PLATFORM'] = 'egl'

# 屏蔽PIL/Pillow的警告
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*libpng warning.*')
warnings.filterwarnings('ignore', message='.*WebGL.*')

# 初始化colorama
init()

def disable_win32_error_popup():
    """禁用Windows错误弹窗"""
    if sys.platform == 'win32':
        # 禁用Windows错误报告
        SEM_NOGPFAULTERRORBOX = 0x0002
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)
        # 禁用Windows的错误对话框
        ERROR_SUPPRESS_ABORT = 0
        ctypes.windll.kernel32.SetThreadErrorMode(ERROR_SUPPRESS_ABORT, None)

def disable_libpng_warnings():
    """
    禁用libpng警告
    这是一个更彻底的方法，通过修改库的内部方法来禁止输出
    """
    # 尝试拦截PIL的warning输出
    try:
        import PIL.Image
        # 保存原始方法
        original_open = PIL.Image.open
        
        # 创建一个不会报告警告的包装方法
        def open_without_warnings(*args, **kwargs):
            # 暂时禁用警告
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return original_open(*args, **kwargs)
        
        # 替换原始方法
        PIL.Image.open = open_without_warnings
    except:
        pass
    
    # 禁用selenium的webdriver日志
    try:
        import logging
        logging.getLogger('selenium.webdriver').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        # 禁用其他可能导致噪音的日志
        logging.getLogger('PIL').setLevel(logging.ERROR)
        logging.getLogger('OpenGL').setLevel(logging.ERROR)
        logging.getLogger('selenium').setLevel(logging.ERROR)
    except:
        pass

# 在程序启动时立即调用这些函数
disable_win32_error_popup()
disable_libpng_warnings()

def suppress_stdout_stderr():
    """
    抑制标准输出和标准错误流，隐藏无关的警告消息
    返回原始的stdout和stderr
    """
    # 保存原始的输出流
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # 创建空的输出流来吸收无关输出
    null_output = io.StringIO()
    
    # 重定向标准输出和标准错误流
    sys.stdout = null_output
    sys.stderr = null_output
    
    return original_stdout, original_stderr

def restore_stdout_stderr(original_stdout, original_stderr):
    """
    恢复标准输出和标准错误流
    """
    sys.stdout = original_stdout
    sys.stderr = original_stderr

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='小蓝本数据采集工具')
    parser.add_argument('-f', '--filename', 
                      help='输出Excel文件名（不需要包含.xlsx扩展名）')
    
    # 创建互斥参数组用于选择目标类型
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument('-g', '--group',
                      help='集团页面的URL，例如：https://sou.xiaolanben.com/group/xxx')
    target_group.add_argument('-c', '--company',
                      help='公司页面的URL，例如：https://sou.xiaolanben.com/company/xxx')
    
    # 添加功能选择参数
    parser.add_argument('--all', action='store_true',
                      help='提取所有可用数据')
    parser.add_argument('--shareholders', action='store_true',
                      help='针对于集团提取股东数据')
    parser.add_argument('--products', action='store_true',
                      help='针对于集团提取产品数据（APP、Media、Website）')
    parser.add_argument('--recursive', action='store_true',
                      help='递归提取集团成员的公司数据')
    parser.add_argument('--members-output', metavar='FILENAME',
                      help='集团成员数据输出文件名（不需要包含.xlsx扩展名），默认使用与集团数据相同的文件')
    
    return parser.parse_args()

def release_resources(obj, name="资源"):
    """释放对象资源并执行垃圾回收"""
    if obj is not None:
        del obj
        gc.collect()  # 强制垃圾回收
        print(f"{name}提取完成，已释放相关资源")

def main():
    """主程序入口"""
    # 显示个性签名
    print(Fore.CYAN + r"""
 _        _    ______ ______ _____  _______  __
| |      / \  |  ____|  ____|  __ \|  ____\ \/ /
| |     / _ \ | |__  | |__  | |__) | |__   \  / 
| |    / ___ \|  __| |  __| |  _  /|  __|  /  \ 
| |___/ /   \ \ |    | |    | | \ \| |____/ /\ \
|______/     \_\_|    |_|    |_|  \_\______/_/\_\
""" + Fore.YELLOW + "\n小蓝本数据采集工具 - By LAFFREX" + Style.RESET_ALL)
    
    # 显示版本和启动时间
    print(f"{Fore.GREEN}版本: v1.0.0{Style.RESET_ALL}")
    print(f"{Fore.GREEN}启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}\n")
    
    args = parse_arguments()
    
    # 如果没有指定具体功能，默认提取所有数据
    if not (args.all or args.shareholders or args.products):
        args.all = True
    
    # 根据数据类型设置默认文件名
    if not args.filename:
        args.filename = 'xiaolanben_group' if args.group else 'xiaolanben_company'
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, f"{args.filename}.xlsx")
    
    # 设置集团成员输出文件
    members_output_file = None
    if args.members_output:
        members_output_file = os.path.join(current_dir, f"{args.members_output}.xlsx")
    
    # 创建文件管理器并初始化表格
    file_manager = ExcelFileManager(output_file)
    
    # 根据要执行的功能确定需要初始化的表格
    required_tables = []
    if args.group:
        if args.all or args.shareholders:
            required_tables.extend(['集团成员', '对外投资', '投资方'])
        if args.all or args.products:
            required_tables.extend(['APP', 'Website', '微信公众号', '微信小程序', '其他媒体'])
    else:  # 公司数据
        required_tables.extend(['APP', 'Website', '微信公众号', '微信小程序', '其他媒体'])
    
    # 初始化表格，如果失败则退出程序
    print("\n开始初始化输出文件...")
    if not file_manager.initialize_tables(required_tables):
        print("表格初始化失败，程序退出")
        return
    
    # 如果有独立的集团成员输出文件，也初始化它
    if members_output_file and members_output_file != output_file:
        members_file_manager = ExcelFileManager(members_output_file)
        if not members_file_manager.initialize_tables(['APP', 'Website', '微信公众号', '微信小程序', '其他媒体']):
            print("集团成员表格初始化失败，程序退出")
            return
    
    try:
        # 隐藏浏览器初始化和操作过程中的无关警告消息
        original_stdout, original_stderr = suppress_stdout_stderr()
        
        # 使用统一的浏览器初始化函数
        driver = init_driver()
        
        # 恢复标准输出流以显示我们的提示信息
        restore_stdout_stderr(original_stdout, original_stderr)
        
        # 创建认证管理器
        auth_manager = AuthManager(driver)
        
        # 执行登录
        print("\n开始登录...")
        if not auth_manager.login():
            print("登录失败，程序退出")
            return
        
        if args.group:
            # 按顺序执行各个爬虫，确保只有一个爬虫在操作文件
            
            # 1. 首先处理股东数据（如果需要）
            if args.all or args.shareholders:
                print("\n开始获取集团股东数据...")
                # 在操作浏览器前隐藏输出
                original_stdout, original_stderr = suppress_stdout_stderr()
                shareholder_crawler = GroupShareholderCrawler(driver, output_file, args.group)
                shareholder_crawler.get_shareholder_info()
                # 恢复输出
                restore_stdout_stderr(original_stdout, original_stderr)
                # 手动释放资源，确保文件句柄关闭
                release_resources(shareholder_crawler, "股东数据")
            
            # 2. 然后处理产品数据（如果需要）
            if args.all or args.products:
                print("\n开始获取集团产品数据...")
                # 在操作浏览器前隐藏输出
                original_stdout, original_stderr = suppress_stdout_stderr()
                group_crawler = GroupCrawler(driver, output_file, args.group)
                group_crawler.get_company_and_website_info()
                # 恢复输出
                restore_stdout_stderr(original_stdout, original_stderr)
                # 手动释放资源
                release_resources(group_crawler, "产品数据")
            
            # 3. 最后处理递归提取集团成员数据（如果需要）
            if args.recursive:
                print("\n开始递归提取集团成员数据...")
                # 在操作浏览器前隐藏输出
                original_stdout, original_stderr = suppress_stdout_stderr()
                members_crawler = GroupMembersCrawler(driver, output_file, members_output_file)
                members_crawler.extract_members_data(recursive=True)
                # 恢复输出
                restore_stdout_stderr(original_stdout, original_stderr)
                # 手动释放资源
                release_resources(members_crawler, "集团成员数据")
        
        else:
            # 处理公司数据
            if args.all or args.products:
                print("\n开始获取公司产品数据...")
                # 在操作浏览器前隐藏输出
                original_stdout, original_stderr = suppress_stdout_stderr()
                company_crawler = CompanyCrawler(driver, output_file, args.company)
                company_crawler.get_company_and_website_info()
                # 恢复输出
                restore_stdout_stderr(original_stdout, original_stderr)
                # 手动释放资源
                release_resources(company_crawler, "公司数据")
        
    except Exception as e:
        # 确保恢复输出流
        try:
            restore_stdout_stderr(original_stdout, original_stderr)
        except:
            pass
        print(f"程序执行出错: {str(e)}")
    finally:
        # 确保恢复输出流
        try:
            restore_stdout_stderr(original_stdout, original_stderr)
        except:
            pass
        # 等待用户确认后关闭浏览器
        input("\n按回车键关闭浏览器...")
        # 隐藏关闭浏览器时可能出现的错误
        original_stdout, original_stderr = suppress_stdout_stderr()
        driver.quit()
        restore_stdout_stderr(original_stdout, original_stderr)

if __name__ == "__main__":
    main() 