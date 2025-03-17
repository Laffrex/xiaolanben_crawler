import argparse
import os
from xlb.auth.auth_manager import AuthManager
from xlb.utils.browser_utils import init_driver
from xlb.crawler.group.shareholder_crawler import ShareholderCrawler as GroupShareholderCrawler
from xlb.crawler.group.group_crawler import GroupCrawler
from xlb.crawler.company.company_crawler import CompanyCrawler

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
                      help='提取股东数据')
    parser.add_argument('--products', action='store_true',
                      help='提取产品数据（APP、Media、Website）')
    
    return parser.parse_args()

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
            # 处理集团数据
            if args.all or args.shareholders:
                print("\n开始获取集团股东数据...")
                shareholder_crawler = GroupShareholderCrawler(driver, output_file, args.group)
                shareholder_crawler.get_shareholder_info()
            
            if args.all or args.products:
                print("\n开始获取集团产品数据...")
                group_crawler = GroupCrawler(driver, output_file, args.group)
                group_crawler.get_company_and_website_info()
        
        else:
            # 处理公司数据
            if args.all or args.products:
                print("\n开始获取公司产品数据...")
                company_crawler = CompanyCrawler(driver, output_file, args.company)
                company_crawler.get_company_and_website_info()
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        # 等待用户确认后关闭浏览器
        input("\n按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    main() 