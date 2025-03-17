from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from ..base_crawler import BaseCrawler
from ..data_extractor import DataExtractor
import pandas as pd

class CompanyCrawler(BaseCrawler):
    def __init__(self, driver, output_file, url):
        super().__init__(driver, output_file)
        self.data_extractor = DataExtractor(driver, output_file)
        self.company_url = url

    def get_company_and_website_info(self):
        """获取产品信息并分类保存"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 1. 访问公司页面
                print(f"正在访问公司页面: {self.company_url}")
                self.driver.get(self.company_url)
                
                # 2. 检查登录状态
                if not self.check_login_status():
                    print("登录状态已失效，需要重新登录")
                    return False
                
                # 3. 定位到产品信息section
                try:
                    product_section = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "section.component-company-product#page-menu-project-info"))
                    )
                    print("已找到产品信息区域")
                except TimeoutException:
                    print("未找到产品信息区域")
                    retry_count += 1
                    continue
                
                # 4. 处理标签页
                try:
                    # 获取标签页容器
                    tabs_container = product_section.find_element(By.CSS_SELECTOR, "div[role='tablist'].el-tabs__nav.is-top")
                    print("已找到标签页容器")
                    
                    # 获取所有标签页
                    tabs = tabs_container.find_elements(By.CSS_SELECTOR, "div[role='tab']")
                    print(f"找到 {len(tabs)} 个标签页")
                    
                    # 打印所有标签页的文本和状态
                    for i, tab in enumerate(tabs):
                        tab_id = tab.get_attribute('id')
                        tab_text = tab.text
                        tab_class = tab.get_attribute('class')
                        tab_disabled = 'is-disabled' in tab_class
                        tab_content = tab.text.split('•')[-1].strip() if '•' in tab.text else ''
                        
                        print(f"标签 {i+1}: {tab_text} (ID: {tab_id}, 禁用状态: {tab_disabled}, 内容: {tab_content})")
                    
                    # 处理APP标签页
                    try:
                        app_tab = tabs_container.find_element(By.CSS_SELECTOR, "div#tab-app[role='tab']")
                        # 检查标签是否被禁用或内容为null
                        app_tab_class = app_tab.get_attribute('class')
                        app_tab_disabled = 'is-disabled' in app_tab_class
                        app_tab_content = app_tab.text.split('•')[-1].strip() if '•' in app_tab.text else ''
                        
                        if app_tab_disabled or app_tab_content == 'null':
                            print("APP标签被禁用或内容为null，跳过处理")
                        else:
                            app_tab.click()
                            print("\n处理APP标签页")
                            time.sleep(2)
                            
                            # 等待APP内容加载
                            app_pane = self.wait.until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "div#pane-app[role='tabpanel']"))
                            )
                            
                            # 获取内容容器
                            content_container = app_pane.find_element(By.CSS_SELECTOR, "div.content-item")
                            
                            # 检查内容是否为空
                            app_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-app-item")
                            if app_items:
                                print(f"找到 {len(app_items)} 个APP项")
                                self.data_extractor.scroll_container(content_container)
                                
                                # 提取APP数据
                                results = []
                                for item in app_items:
                                    try:
                                        link = item.get_attribute('href')
                                        name_element = item.find_element(By.CSS_SELECTOR, "p.name span.text")
                                        name = name_element.text.strip()
                                        results.append({'产品名': name, '产品链接': link})
                                    except Exception as e:
                                        print(f"提取APP信息出错: {str(e)}")
                                
                                # 保存到Excel
                                if results:
                                    df = pd.DataFrame(results)
                                    self.data_extractor.save_to_excel(df, 'APP')
                                    print(f"保存了 {len(results)} 个APP记录")
                            else:
                                print("APP标签页内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理APP标签页时出错: {str(e)}")
                    
                    # 处理Media标签页
                    try:
                        media_tab = tabs_container.find_element(By.CSS_SELECTOR, "div#tab-media[role='tab']")
                        # 检查标签是否被禁用或内容为null
                        media_tab_class = media_tab.get_attribute('class')
                        media_tab_disabled = 'is-disabled' in media_tab_class
                        media_tab_content = media_tab.text.split('•')[-1].strip() if '•' in media_tab.text else ''
                        
                        if media_tab_disabled or media_tab_content == 'null':
                            print("Media标签被禁用或内容为null，跳过处理")
                        else:
                            media_tab.click()
                            print("\n处理Media标签页")
                            time.sleep(2)
                            
                            # 等待Media内容加载
                            media_pane = self.wait.until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "div#pane-media[role='tabpanel']"))
                            )
                            
                            # 获取内容容器
                            content_container = media_pane.find_element(By.CSS_SELECTOR, "div.content-item")
                            
                            # 检查内容是否为空
                            media_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-media-item")
                            if media_items:
                                print(f"找到 {len(media_items)} 个Media项")
                                self.data_extractor.scroll_container(content_container)
                                
                                # 直接使用extract_media_content方法处理媒体数据
                                self.data_extractor.extract_media_content(content_container)
                            else:
                                print("Media标签页内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理Media标签页时出错: {str(e)}")
                    
                    # 处理Website标签页
                    try:
                        website_tab = tabs_container.find_element(By.CSS_SELECTOR, "div#tab-website[role='tab']")
                        # 检查标签是否被禁用或内容为null
                        website_tab_class = website_tab.get_attribute('class')
                        website_tab_disabled = 'is-disabled' in website_tab_class
                        website_tab_content = website_tab.text.split('•')[-1].strip() if '•' in website_tab.text else ''
                        
                        if website_tab_disabled or website_tab_content == 'null':
                            print("Website标签被禁用或内容为null，跳过处理")
                        else:
                            website_tab.click()
                            print("\n处理Website标签页")
                            time.sleep(2)
                            
                            # 等待Website内容加载
                            website_pane = self.wait.until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "div#pane-website[role='tabpanel']"))
                            )
                            
                            # 获取内容容器
                            content_container = website_pane.find_element(By.CSS_SELECTOR, "div.content-item")
                            
                            # 检查内容是否为空
                            website_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-website-item")
                            if website_items:
                                print(f"找到 {len(website_items)} 个Website项")
                                self.data_extractor.scroll_container(content_container)
                                
                                # 提取Website数据
                                results = []
                                for item in website_items:
                                    try:
                                        link = item.get_attribute('href')
                                        name_element = item.find_element(By.CSS_SELECTOR, "div.website-item-name p")
                                        name = name_element.text.strip()
                                        results.append({'网站名': name, '网站链接': link})
                                    except Exception as e:
                                        print(f"提取Website信息出错: {str(e)}")
                                
                                # 保存到Excel
                                if results:
                                    df = pd.DataFrame(results)
                                    self.data_extractor.save_to_excel(df, 'Website')
                                    print(f"保存了 {len(results)} 个Website记录")
                            else:
                                print("Website标签页内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理Website标签页时出错: {str(e)}")
                    
                except Exception as e:
                    print(f"处理标签页时出错: {str(e)}")
                    retry_count += 1
                    continue
                
                print("\n所有产品数据提取完成")
                return True
                
            except Exception as e:
                print(f"处理页面时出错: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"正在进行第 {retry_count + 1} 次重试...")
                    time.sleep(3)
        
        print(f"已达到最大重试次数 ({max_retries})，跳过该页面")
        return False 