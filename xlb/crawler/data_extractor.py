from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import os
import time
from openpyxl import load_workbook

class DataExtractor:
    def __init__(self, driver, output_file):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.output_file = output_file
        # 不再自动初始化表格，由 ExcelFileManager 统一管理
        # self.initialize_tables()

    # 保留方法但修改实现，仅作检查用途
    def initialize_tables(self):
        """检查表格是否存在，但不再负责创建表格
        
        Returns:
            bool: 检查是否通过
        """
        table_structures = {
            'APP': ['产品名', '产品链接'],
            'Website': ['网站名', '网站链接'],
            '微信公众号': ['微信公众号', '链接'],
            '微信小程序': ['微信小程序', '链接'],
            '其他媒体': ['其他媒体', '链接'],
            '集团成员': ['成员名', '成员链接'],
            '对外投资': ['被投资方', '被投资方链接'],
            '投资方': ['投资方', '投资方链接']
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

    def save_to_excel(self, df, sheet_name):
        """保存数据到Excel文件的指定表格"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"正在保存数据到文件: {self.output_file}")
                print(f"表格名称: {sheet_name}")
                print(f"数据行数: {len(df)}")
                
                if os.path.exists(self.output_file):
                    # 如果文件存在，使用openpyxl引擎以追加模式打开
                    try:
                        with pd.ExcelWriter(self.output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                    except Exception as e:
                        print(f"使用追加模式保存失败: {str(e)}，尝试使用覆盖模式")
                        # 如果追加模式失败，尝试读取所有表格，然后重新写入
                        try:
                            # 读取所有现有表格（除了当前要保存的表格）
                            excel_file = pd.ExcelFile(self.output_file)
                            all_sheets = {}
                            for sheet in excel_file.sheet_names:
                                if sheet != sheet_name:
                                    all_sheets[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
                            
                            # 创建新的Excel文件
                            with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                                # 先写入当前数据
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                                # 再写入其他表格
                                for sheet, data in all_sheets.items():
                                    data.to_excel(writer, sheet_name=sheet, index=False)
                        except Exception as inner_e:
                            print(f"覆盖模式也失败: {str(inner_e)}，尝试创建新文件")
                            # 如果读取现有表格失败，直接创建新文件
                            with pd.ExcelWriter(f"{self.output_file}.new", engine='openpyxl') as writer:
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                            # 备份原文件并重命名新文件
                            if os.path.exists(self.output_file):
                                os.rename(self.output_file, f"{self.output_file}.bak")
                            os.rename(f"{self.output_file}.new", self.output_file)
                else:
                    # 如果文件不存在，创建新文件
                    with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                print(f"成功保存 {len(df)} 条记录到 {sheet_name} 表格")
                return True
                
            except Exception as e:
                print(f"保存数据到Excel时出错 (尝试 {retry_count+1}/{max_retries}): {str(e)}")
                print(f"尝试保存的文件路径: {self.output_file}")
                retry_count += 1
                time.sleep(2)  # 等待2秒后重试
        
        print(f"保存数据失败，已达到最大重试次数 ({max_retries})")
        return False

    def extract_app_content(self, content_container):
        """提取APP内容"""
        results = []
        app_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-app-item")
        print(f"找到 {len(app_items)} 个APP项")
        
        for item in app_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "p.name span.text").text.strip()
                link = item.get_attribute('href')
                results.append({'产品名': name, '产品链接': link})
            except Exception as e:
                print(f"提取APP信息出错: {str(e)}")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('APP', ['产品名', '产品链接'])
                if not existing_df.empty:
                    print(f"合并 {len(existing_df)} 条现有APP数据")
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    df = df.drop_duplicates(subset=['产品链接'], keep='last')
            except Exception as e:
                print(f"读取现有APP数据时出错: {str(e)}")
            
            self.save_to_excel(df, 'APP')
            print(f"保存了 {len(df)} 个APP记录")
        return results

    def extract_media_content(self, content_container):
        """提取Media内容并直接分类处理"""
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

    def extract_website_content(self, content_container):
        """提取Website内容"""
        results = []
        website_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-website-item")
        print(f"找到 {len(website_items)} 个Website项")
        
        for item in website_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.website-item-name p").text.strip()
                link = item.get_attribute('href')
                results.append({'网站名': name, '网站链接': link})
            except Exception as e:
                print(f"提取Website信息出错: {str(e)}")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('Website', ['网站名', '网站链接'])
                if not existing_df.empty:
                    print(f"合并 {len(existing_df)} 条现有Website数据")
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    df = df.drop_duplicates(subset=['网站链接'], keep='last')
            except Exception as e:
                print(f"读取现有Website数据时出错: {str(e)}")
            
            self.save_to_excel(df, 'Website')
            print(f"保存了 {len(df)} 个Website记录")
        return results

    def scroll_container(self, content_container):
        """滚动加载内容 - 优化版"""
        max_scroll_attempts = 50  # 增加最大滚动次数，适应更多内容
        scroll_timeout = time.time() + 60  # 增加超时时间到60秒

        scroll_count = 0
        last_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
        
        while scroll_count < max_scroll_attempts and time.time() < scroll_timeout:
            # 1. 首先滚动到底部
            self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
            time.sleep(2.5)  # 等待时间略微延长
            
            # 2. 计算当前容器的可见高度
            container_height = self.driver.execute_script(
                "return arguments[0].clientHeight || arguments[0].offsetHeight;", content_container)
            
            # 3. 向上滚动一小段距离（约20%的容器高度）
            scroll_up_distance = int(container_height * 0.2)
            current_scroll = self.driver.execute_script("return arguments[0].scrollTop;", content_container)
            self.driver.execute_script(
                "arguments[0].scrollTo(0, arguments[1]);", 
                content_container, 
                max(0, current_scroll - scroll_up_distance)
            )
            time.sleep(1)  # 等待短暂时间
            
            # 4. 再次向下滚动到底部
            self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
            time.sleep(1)  # 等待内容加载
            
            # 5. 计算新的滚动高度
            new_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
            
            # 如果高度没有变化，说明已经到达底部
            if new_height == last_height:
                # 连续两次高度相同，可能已到达底部
                # 再尝试一次回弹操作，确保真的到底了
                if scroll_count > 0:  # 至少已经滚动过一次
                    # 最后一次回弹尝试
                    self.driver.execute_script(
                        "arguments[0].scrollTo(0, arguments[1]);", 
                        content_container, 
                        max(0, current_scroll - scroll_up_distance * 2)  # 尝试滚动更大距离
                    )
                    time.sleep(1.5)
                    self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
                    time.sleep(1.5)
                    
                    final_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
                    if final_height == new_height:
                        print("已到达底部")
                        break
                    else:
                        # 最后一次回弹找到了更多内容
                        new_height = final_height
                else:
                    print("已到达底部")
                    break
            
            last_height = new_height
            scroll_count += 1
            print(f"滚动次数: {scroll_count}, 当前高度: {new_height}")

        
        if time.time() >= scroll_timeout:
            print("滚动加载超时")
        elif scroll_count >= max_scroll_attempts:
            print("达到最大滚动次数")

    def extract_group_members(self, content_container):
        """提取集团成员信息"""
        results = []
        member_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
        print(f"找到 {len(member_items)} 个集团成员")
        
        for item in member_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.name-impact p.name").text.strip()
                link = item.get_attribute('href')
                results.append({'成员名': name, '成员链接': link})
            except Exception as e:
                print(f"提取集团成员信息出错: {str(e)}")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('集团成员', ['成员名', '成员链接'])
                if not existing_df.empty:
                    print(f"合并 {len(existing_df)} 条现有集团成员数据")
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    df = df.drop_duplicates(subset=['成员链接'], keep='last')
            except Exception as e:
                print(f"读取现有集团成员数据时出错: {str(e)}")
            
            # 使用增强的save_to_excel方法保存
            self.save_to_excel(df, '集团成员')
            print(f"保存了 {len(df)} 个集团成员记录")
        return results

    def extract_investments(self, content_container):
        """提取对外投资信息"""
        results = []
        investment_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
        print(f"找到 {len(investment_items)} 个对外投资")
        
        for item in investment_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.name-impact p.name").text.strip()
                link = item.get_attribute('href')
                results.append({'被投资方': name, '被投资方链接': link})
            except Exception as e:
                print(f"提取对外投资信息出错: {str(e)}")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('对外投资', ['被投资方', '被投资方链接'])
                if not existing_df.empty:
                    print(f"合并 {len(existing_df)} 条现有对外投资数据")
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    df = df.drop_duplicates(subset=['被投资方链接'], keep='last')
            except Exception as e:
                print(f"读取现有对外投资数据时出错: {str(e)}")
            
            # 使用增强的save_to_excel方法保存
            self.save_to_excel(df, '对外投资')
            print(f"保存了 {len(df)} 个对外投资记录")
        return results

    def extract_investors(self, content_container):
        """提取投资方信息"""
        results = []
        investor_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
        print(f"找到 {len(investor_items)} 个投资方")
        
        for item in investor_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.name-impact p.name").text.strip()
                link = item.get_attribute('href')
                results.append({'投资方': name, '投资方链接': link})
            except Exception as e:
                print(f"提取投资方信息出错: {str(e)}")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('投资方', ['投资方', '投资方链接'])
                if not existing_df.empty:
                    print(f"合并 {len(existing_df)} 条现有投资方数据")
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    df = df.drop_duplicates(subset=['投资方链接'], keep='last')
            except Exception as e:
                print(f"读取现有投资方数据时出错: {str(e)}")
            
            # 使用增强的save_to_excel方法保存
            self.save_to_excel(df, '投资方')
            print(f"保存了 {len(df)} 个投资方记录")
        return results

    def process_media_data(self):
        """处理媒体数据并分类保存（为保持向后兼容性而保留，实际处理已在extract_media_content中完成）"""
        print("媒体数据已在提取时处理，无需再次处理")
        return True 

    def _read_existing_data(self, sheet_name, columns):
        """读取现有Excel表格数据的辅助方法"""
        try:
            if os.path.exists(self.output_file):
                try:
                    # 尝试读取指定表格
                    existing_df = pd.read_excel(self.output_file, sheet_name=sheet_name)
                    
                    # 检查列名是否匹配
                    if all(col in existing_df.columns for col in columns):
                        # 只保留需要的列
                        existing_df = existing_df[columns]
                        return existing_df
                    else:
                        print(f"表格 {sheet_name} 的列名不匹配，将创建新表格")
                        return pd.DataFrame(columns=columns)
                except Exception as e:
                    print(f"读取表格 {sheet_name} 时出错: {str(e)}")
                    return pd.DataFrame(columns=columns)
            else:
                print(f"文件 {self.output_file} 不存在，将创建新文件")
                return pd.DataFrame(columns=columns)
        except Exception as e:
            print(f"读取现有数据时出错: {str(e)}")
            return pd.DataFrame(columns=columns) 