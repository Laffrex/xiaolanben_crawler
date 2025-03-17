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

    def save_to_excel(self, df, sheet_name):
        """保存数据到Excel文件的指定表格"""
        try:
            print(f"正在保存数据到文件: {self.output_file}")
            print(f"表格名称: {sheet_name}")
            print(f"数据行数: {len(df)}")
            
            if os.path.exists(self.output_file):
                # 如果文件存在，使用openpyxl引擎以追加模式打开
                with pd.ExcelWriter(self.output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # 如果文件不存在，创建新文件
                with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"成功保存 {len(df)} 条记录到 {sheet_name} 表格")
            return True
        except Exception as e:
            print(f"保存数据到Excel时出错: {str(e)}")
            print(f"尝试保存的文件路径: {self.output_file}")
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
            self.save_to_excel(df, 'APP')
        return results

    def extract_media_content(self, content_container):
        """提取Media内容"""
        results = []
        media_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-media-item")
        print(f"找到 {len(media_items)} 个Media项")
        
        for item in media_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.media-item-name p").text.strip()
                link = item.get_attribute('href')
                results.append({'媒体名': name, '媒体链接': link})
            except Exception as e:
                print(f"提取Media信息出错: {str(e)}")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            self.save_to_excel(df, 'Media')
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
            self.save_to_excel(df, 'Website')
        return results

    def scroll_container(self, content_container):
        """滚动加载内容"""
        max_scroll_attempts = 30
        scroll_timeout = time.time() + 60
        scroll_count = 0
        last_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
        
        print("开始滚动加载内容...")
        while scroll_count < max_scroll_attempts and time.time() < scroll_timeout:
            # 滚动到底部
            self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
            time.sleep(2)
            
            # 计算新的滚动高度
            new_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
            if new_height == last_height:
                print("已到达底部")
                break
            
            last_height = new_height
            scroll_count += 1
            print(f"滚动次数: {scroll_count}")
        
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
            try:
                with pd.ExcelWriter(self.output_file, engine='openpyxl', mode='a' if os.path.exists(self.output_file) else 'w') as writer:
                    df.to_excel(writer, sheet_name='集团成员', index=False)
                print(f"保存了 {len(results)} 个集团成员记录")
            except Exception as e:
                print(f"保存集团成员数据时出错: {str(e)}")
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
            try:
                with pd.ExcelWriter(self.output_file, engine='openpyxl', mode='a' if os.path.exists(self.output_file) else 'w') as writer:
                    df.to_excel(writer, sheet_name='对外投资', index=False)
                print(f"保存了 {len(results)} 个对外投资记录")
            except Exception as e:
                print(f"保存对外投资数据时出错: {str(e)}")
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
            try:
                with pd.ExcelWriter(self.output_file, engine='openpyxl', mode='a' if os.path.exists(self.output_file) else 'w') as writer:
                    df.to_excel(writer, sheet_name='投资方', index=False)
                print(f"保存了 {len(results)} 个投资方记录")
            except Exception as e:
                print(f"保存投资方数据时出错: {str(e)}")
        return results

    def process_media_data(self):
        """处理媒体数据并分类保存"""
        try:
            # 读取Excel文件中的Media表
            df = pd.read_excel(self.output_file, sheet_name='Media')
            
            # 创建三个空的DataFrame用于存储分类后的数据
            wechat_df = pd.DataFrame(columns=['微信公众号', '链接'])
            miniapp_df = pd.DataFrame(columns=['微信小程序', '链接'])
            other_df = pd.DataFrame(columns=['其他媒体', '链接'])
            
            # 遍历Media表中的每一行
            for index, row in df.iterrows():
                media_name = row['媒体名']
                media_link = row['媒体链接']
                
                # 根据链接分类，不考虑@符号
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
            
            # 使用ExcelWriter保存多个表格
            with pd.ExcelWriter(self.output_file, engine='openpyxl', mode='a') as writer:
                # 删除原有的Media表（如果存在）
                if 'Media' in writer.book.sheetnames:
                    idx = writer.book.sheetnames.index('Media')
                    writer.book.remove(writer.book.worksheets[idx])
                
                # 保存新的分类表格
                if not wechat_df.empty:
                    wechat_df.to_excel(writer, sheet_name='微信公众号', index=False)
                    print(f"保存了 {len(wechat_df)} 个微信公众号记录")
                if not miniapp_df.empty:
                    miniapp_df.to_excel(writer, sheet_name='微信小程序', index=False)
                    print(f"保存了 {len(miniapp_df)} 个微信小程序记录")
                if not other_df.empty:
                    other_df.to_excel(writer, sheet_name='其他媒体', index=False)
                    print(f"保存了 {len(other_df)} 个其他媒体记录")
                
            print("媒体数据分类完成！")
            return True
            
        except Exception as e:
            print(f"处理媒体数据时出错: {str(e)}")
            # 添加更详细的错误信息
            if 'df' in locals():
                print(f"DataFrame的列名: {df.columns.tolist()}")
            return False 