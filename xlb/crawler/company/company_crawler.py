from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from ..base_crawler import BaseCrawler
from ..data_extractor import DataExtractor

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
                    # 获取标签页
                    tabs = product_section.find_elements(By.CSS_SELECTOR, "div.el-tabs__nav-wrap div.el-tabs__item")
                    print(f"找到 {len(tabs)} 个标签页")
                    
                    # 打印所有标签页的文本
                    for i, tab in enumerate(tabs):
                        print(f"标签 {i+1}: {tab.text}")
                    
                    # 处理APP标签页
                    try:
                        app_tab = product_section.find_element(By.CSS_SELECTOR, "div.el-tabs__item[aria-controls='pane-app']")
                        app_tab.click()
                        print("\n处理APP标签页")
                        time.sleep(2)
                        
                        content_container = product_section.find_element(By.CLASS_NAME, "content-item")
                        # 检查内容是否为空
                        if content_container.find_elements(By.CSS_SELECTOR, "a.component-app-item"):
                            self.data_extractor.scroll_container(content_container)
                            self.data_extractor.extract_app_content(content_container)
                        else:
                            print("APP标签页内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理APP标签页时出错: {str(e)}")
                    
                    # 处理Media标签页
                    try:
                        media_tab = product_section.find_element(By.CSS_SELECTOR, "div.el-tabs__item[aria-controls='pane-media']")
                        media_tab.click()
                        print("\n处理Media标签页")
                        time.sleep(2)
                        
                        content_container = product_section.find_element(By.CLASS_NAME, "content-item")
                        # 检查内容是否为空
                        if content_container.find_elements(By.CSS_SELECTOR, "a.component-media-item"):
                            self.data_extractor.scroll_container(content_container)
                            self.data_extractor.extract_media_content(content_container)
                            # 处理媒体数据分类
                            self.data_extractor.process_media_data()
                        else:
                            print("Media标签页内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理Media标签页时出错: {str(e)}")
                    
                    # 处理Website标签页
                    try:
                        website_tab = product_section.find_element(By.CSS_SELECTOR, "div.el-tabs__item[aria-controls='pane-website']")
                        website_tab.click()
                        print("\n处理Website标签页")
                        time.sleep(2)
                        
                        content_container = product_section.find_element(By.CLASS_NAME, "content-item")
                        # 检查内容是否为空
                        if content_container.find_elements(By.CSS_SELECTOR, "a.component-website-item"):
                            self.data_extractor.scroll_container(content_container)
                            self.data_extractor.extract_website_content(content_container)
                        else:
                            print("Website标签页内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理Website标签页时出错: {str(e)}")
                    
                except TimeoutException:
                    print("未找到标签页")
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