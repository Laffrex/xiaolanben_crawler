from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
import pandas as pd
from ..base_crawler import BaseCrawler
from ..company.company_crawler import CompanyCrawler
from ..data_extractor import DataExtractor
import openpyxl
from openpyxl import load_workbook
from xlb.utils.excel_manager import ExcelFileManager

class GroupMembersCrawler(BaseCrawler):
    """集团成员公司数据提取爬虫"""
    
    def __init__(self, driver, group_output_file, members_output_file=None):
        """
        初始化集团成员爬虫
        
        Args:
            driver: WebDriver实例
            group_output_file: 集团数据输出文件路径
            members_output_file: 集团成员数据输出文件路径，默认为与集团数据相同的文件
        """
        super().__init__(driver, group_output_file)
        self.data_extractor = DataExtractor(driver, group_output_file)
        
        # 设置集团成员数据输出文件，默认使用与集团数据相同的文件
        if members_output_file is None:
            self.members_output_file = group_output_file
        else:
            self.members_output_file = members_output_file
            
        # 创建自定义的数据提取器，用于处理集团成员数据
        self.members_data_extractor = CustomDataExtractor(driver, self.members_output_file)
    
    def initialize_output_file(self):
        """初始化输出文件，使用 ExcelFileManager 确保所需表格存在"""
        print(f"检查输出文件: {self.members_output_file}")
        
        try:
            # 使用 ExcelFileManager 初始化文件
            file_manager = ExcelFileManager(self.members_output_file)
            
            # 定义需要的表格
            required_tables = ['APP', 'Website', '微信公众号', '微信小程序', '其他媒体']
            
            # 初始化表格
            if file_manager.initialize_tables(required_tables):
                print("输出文件检查完成")
                return True
            else:
                print("输出文件初始化失败")
                return False
                
        except Exception as e:
            print(f"初始化输出文件时出错: {str(e)}")
            return False
    
    def extract_members_data(self, recursive=False):
        """
        提取集团成员数据
        
        Args:
            recursive: 是否递归提取集团成员的数据，默认为False
        
        Returns:
            bool: 提取是否成功
        """
        try:
            # 1. 读取集团成员数据
            try:
                members_df = pd.read_excel(self.output_file, sheet_name='集团成员')
                print(f"读取到 {len(members_df)} 个集团成员")
            except Exception as e:
                print(f"读取集团成员数据失败: {str(e)}")
                print("请确保已经运行过集团股东爬虫，并且'集团成员'表格存在")
                return False
            
            # 2. 如果不需要递归提取，直接返回
            if not recursive:
                print("未开启递归提取，跳过集团成员数据提取")
                return True
            
            # 3. 初始化输出文件
            if not self.initialize_output_file():
                print("初始化输出文件失败，无法继续提取数据")
                return False
            
            # 4. 递归提取集团成员数据
            print(f"\n开始递归提取集团成员数据，输出文件: {self.members_output_file}")
            
            # 记录成功提取的成员数量
            success_count = 0
            
            # 遍历集团成员
            for index, row in members_df.iterrows():
                member_name = row['成员名']
                member_url = row['成员链接']
                
                print(f"\n正在处理集团成员 [{index+1}/{len(members_df)}]: {member_name}")
                
                # 创建公司爬虫实例，使用自定义的数据提取器
                company_crawler = CustomCompanyCrawler(self.driver, self.members_output_file, member_url, self.members_data_extractor)
                
                # 提取公司数据
                if company_crawler.get_company_and_website_info():
                    success_count += 1
                    print(f"成功提取集团成员 {member_name} 的数据")
                else:
                    print(f"提取集团成员 {member_name} 的数据失败")
                
                # 等待一段时间，避免请求过于频繁
                time.sleep(3)
            
            print(f"\n递归提取完成，成功提取 {success_count}/{len(members_df)} 个集团成员的数据")
            return True
            
        except Exception as e:
            print(f"提取集团成员数据时出错: {str(e)}")
            return False


class CustomDataExtractor(DataExtractor):
    """自定义数据提取器，用于处理集团成员数据"""
    
    def save_to_excel(self, df, sheet_name):
        """保存数据到Excel文件的指定表格，采用追加模式"""
        try:
            print(f"正在保存数据到文件: {self.output_file}")
            print(f"表格名称: {sheet_name}")
            print(f"数据行数: {len(df)}")
            
            # 读取现有数据
            try:
                existing_df = self._read_existing_data(sheet_name, df.columns.tolist())
                if not existing_df.empty:
                    # 合并数据
                    combined_df = pd.concat([existing_df, df], ignore_index=True)
                    
                    # 根据表格类型选择去重的列
                    if sheet_name == 'APP':
                        combined_df = combined_df.drop_duplicates(subset=['产品链接'], keep='last')
                    elif sheet_name == 'Website':
                        combined_df = combined_df.drop_duplicates(subset=['网站链接'], keep='last')
                    elif sheet_name == '微信公众号':
                        combined_df = combined_df.drop_duplicates(subset=['链接'], keep='last')
                    elif sheet_name == '微信小程序':
                        combined_df = combined_df.drop_duplicates(subset=['链接'], keep='last')
                    elif sheet_name == '其他媒体':
                        combined_df = combined_df.drop_duplicates(subset=['链接'], keep='last')
                    
                    # 使用父类的save_to_excel方法保存合并后的数据
                    return super().save_to_excel(combined_df, sheet_name)
                else:
                    # 如果没有现有数据，直接使用父类的save_to_excel方法
                    return super().save_to_excel(df, sheet_name)
            except Exception as e:
                print(f"读取或合并数据时出错: {str(e)}，尝试直接保存")
                # 如果读取失败，直接使用父类的save_to_excel方法
                return super().save_to_excel(df, sheet_name)
        except Exception as e:
            print(f"CustomDataExtractor保存数据到Excel时出错: {str(e)}")
            print(f"尝试保存的文件路径: {self.output_file}")
            return False
    
    def process_media_data(self):
        """处理媒体数据并分类保存，直接在内存中处理，不保存Media表"""
        # 检查是否有内存中的媒体数据
        if hasattr(self, '_media_data') and self._media_data:
            print("使用内存中的媒体数据进行处理")
            return True
        
        # 如果没有内存中的媒体数据，调用父类的空方法
        print("没有媒体数据需要处理，调用父类方法")
        return super().process_media_data()
    
    def extract_media_content(self, content_container):
        """提取Media内容，覆盖父类方法，不保存到Excel，而是保存在内存中并立即处理"""
        results = []
        media_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-media-item")
        print(f"找到 {len(media_items)} 个Media项")
        
        for item in media_items:
            try:
                # 尝试不同的选择器以适应不同页面的结构
                try:
                    # 集团页面的选择器
                    name = item.find_element(By.CSS_SELECTOR, "div.media-item-name p").text.strip()
                except:
                    try:
                        # 公司页面的选择器
                        name = item.find_element(By.CSS_SELECTOR, "div.content p").text.strip()
                    except:
                        # 通用备选选择器
                        name = item.find_element(By.CSS_SELECTOR, "p").text.strip()
                
                link = item.get_attribute('href')
                results.append({'媒体名': name, '媒体链接': link})
            except Exception as e:
                print(f"提取Media信息出错: {str(e)}")
        
        if not results:
            print("没有找到媒体数据")
            return results
        
        # 将结果保存在内存中
        self._media_data = results
        print(f"已提取 {len(results)} 个媒体数据，保存在内存中")
        
        try:
            # 创建三个空的DataFrame用于存储分类后的数据
            wechat_df = pd.DataFrame(columns=['微信公众号', '链接'])
            miniapp_df = pd.DataFrame(columns=['微信小程序', '链接'])
            other_df = pd.DataFrame(columns=['其他媒体', '链接'])
            
            # 遍历媒体数据进行分类
            for item in results:
                try:
                    media_name = item['媒体名']
                    media_link = item['媒体链接']
                    
                    # 根据链接分类
                    if isinstance(media_link, str):
                        if 'sou.xiaolanben.com/media/wechat/' in media_link:
                            wechat_df = pd.concat([wechat_df, pd.DataFrame({
                                '微信公众号': [media_name],
                                '链接': [media_link]
                            })], ignore_index=True)
                            
                        elif 'sou.xiaolanben.com/media/xcx/' in media_link:
                            miniapp_df = pd.concat([miniapp_df, pd.DataFrame({
                                '微信小程序': [media_name],
                                '链接': [media_link]
                            })], ignore_index=True)
                            
                        else:
                            other_df = pd.concat([other_df, pd.DataFrame({
                                '其他媒体': [media_name],
                                '链接': [media_link]
                            })], ignore_index=True)
                except Exception as e:
                    print(f"处理单个媒体项时出错: {str(e)}, 项目内容: {item}")
                    continue
            
            # 保存分类后的数据，并与现有数据合并
            try:
                if not wechat_df.empty:
                    # 检查是否存在现有数据并合并
                    existing_wechat_df = self._read_existing_data('微信公众号', ['微信公众号', '链接'])
                    if not existing_wechat_df.empty:
                        print(f"合并 {len(existing_wechat_df)} 条现有微信公众号数据")
                        wechat_df = pd.concat([existing_wechat_df, wechat_df], ignore_index=True)
                        # 去重
                        wechat_df = wechat_df.drop_duplicates(subset=['链接'], keep='last')
                    
                    self.save_to_excel(wechat_df, '微信公众号')
                    print(f"保存了 {len(wechat_df)} 个微信公众号记录")
            except Exception as e:
                print(f"保存微信公众号数据时出错: {str(e)}")
            
            try:
                if not miniapp_df.empty:
                    # 检查是否存在现有数据并合并
                    existing_miniapp_df = self._read_existing_data('微信小程序', ['微信小程序', '链接'])
                    if not existing_miniapp_df.empty:
                        print(f"合并 {len(existing_miniapp_df)} 条现有微信小程序数据")
                        miniapp_df = pd.concat([existing_miniapp_df, miniapp_df], ignore_index=True)
                        # 去重
                        miniapp_df = miniapp_df.drop_duplicates(subset=['链接'], keep='last')
                    
                    self.save_to_excel(miniapp_df, '微信小程序')
                    print(f"保存了 {len(miniapp_df)} 个微信小程序记录")
            except Exception as e:
                print(f"保存微信小程序数据时出错: {str(e)}")
            
            try:
                if not other_df.empty:
                    # 检查是否存在现有数据并合并
                    existing_other_df = self._read_existing_data('其他媒体', ['其他媒体', '链接'])
                    if not existing_other_df.empty:
                        print(f"合并 {len(existing_other_df)} 条现有其他媒体数据")
                        other_df = pd.concat([existing_other_df, other_df], ignore_index=True)
                        # 去重
                        other_df = other_df.drop_duplicates(subset=['链接'], keep='last')
                    
                    self.save_to_excel(other_df, '其他媒体')
                    print(f"保存了 {len(other_df)} 个其他媒体记录")
            except Exception as e:
                print(f"保存其他媒体数据时出错: {str(e)}")
            
            print(f"处理了 {len(results)} 个媒体数据")
        except Exception as e:
            print(f"处理媒体数据时出错: {str(e)}")
            if 'results' in locals():
                print(f"媒体数据项数: {len(results)}")
        
        return results
    
    def initialize_tables(self):
        """检查表格是否存在，但不再负责创建表格
        
        Returns:
            bool: 检查是否通过
        """
        # 定义需要的表格结构 - 只包含产品相关表格，不包含股东数据表格
        # 这是因为 CustomDataExtractor 只用于处理集团成员的产品数据
        table_structures = {
            'APP': ['产品名', '产品链接'],
            'Website': ['网站名', '网站链接'],
            '微信公众号': ['微信公众号', '链接'],
            '微信小程序': ['微信小程序', '链接'],
            '其他媒体': ['其他媒体', '链接']
        }
        
        try:
            # 仅检查必要的表格是否存在
            if os.path.exists(self.output_file):
                # 尝试打开文件
                excel_file = pd.ExcelFile(self.output_file)
                
                # 检查需要的表格是否存在
                missing_sheets = []
                for sheet_name in table_structures.keys():
                    if sheet_name not in excel_file.sheet_names:
                        missing_sheets.append(sheet_name)
                
                if missing_sheets:
                    print(f"警告: 缺少以下表格: {', '.join(missing_sheets)}")
                    return False
                return True
            else:
                print(f"警告: 文件不存在: {self.output_file}")
                return False
        except Exception as e:
            print(f"检查表格存在性时出错: {str(e)}")
            return False

    def get_media_data_from_memory(self):
        """从内存中获取媒体数据，这个方法会被extract_media_content调用后使用"""
        # 这里我们假设媒体数据已经被extract_media_content方法提取并存储在self._media_data中
        if hasattr(self, '_media_data') and self._media_data:
            return self._media_data
        else:
            print("内存中没有媒体数据")
            return []


class CustomCompanyCrawler(CompanyCrawler):
    """自定义公司爬虫，使用自定义的数据提取器"""
    
    def __init__(self, driver, output_file, url, data_extractor=None):
        super().__init__(driver, output_file, url)
        if data_extractor:
            self.data_extractor = data_extractor 