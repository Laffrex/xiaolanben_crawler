import argparse
import os
import gc
import time
from xlb.auth.auth_manager import AuthManager
from xlb.utils.browser_utils import init_driver
from xlb.crawler.group.shareholder_crawler import ShareholderCrawler as GroupShareholderCrawler
from xlb.crawler.group.group_crawler import GroupCrawler
from xlb.crawler.company.company_crawler import CompanyCrawler
from xlb.crawler.companys_in_group.group_members_crawler import GroupMembersCrawler
from xlb.utils.excel_manager import ExcelFileManager

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
        # 使用统一的浏览器初始化函数
        driver = init_driver()
        
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
                shareholder_crawler = GroupShareholderCrawler(driver, output_file, args.group)
                shareholder_crawler.get_shareholder_info()
                # 手动释放资源，确保文件句柄关闭
                release_resources(shareholder_crawler, "股东数据")
            
            # 2. 然后处理产品数据（如果需要）
            if args.all or args.products:
                print("\n开始获取集团产品数据...")
                group_crawler = GroupCrawler(driver, output_file, args.group)
                group_crawler.get_company_and_website_info()
                # 手动释放资源
                release_resources(group_crawler, "产品数据")
            
            # 3. 最后处理递归提取集团成员数据（如果需要）
            if args.recursive:
                print("\n开始递归提取集团成员数据...")
                members_crawler = GroupMembersCrawler(driver, output_file, members_output_file)
                members_crawler.extract_members_data(recursive=True)
                # 手动释放资源
                release_resources(members_crawler, "集团成员数据")
        
        else:
            # 处理公司数据
            if args.all or args.products:
                print("\n开始获取公司产品数据...")
                company_crawler = CompanyCrawler(driver, output_file, args.company)
                company_crawler.get_company_and_website_info()
                # 手动释放资源
                release_resources(company_crawler, "公司数据")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        # 等待用户确认后关闭浏览器
        input("\n按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    main() 