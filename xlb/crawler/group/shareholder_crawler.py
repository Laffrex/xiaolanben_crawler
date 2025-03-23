from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from ..base_crawler import BaseCrawler
from ..data_extractor import DataExtractor

class ShareholderCrawler(BaseCrawler):
    def __init__(self, driver, output_file, url):
        super().__init__(driver, output_file)
        self.data_extractor = DataExtractor(driver, output_file)
        self.group_url = url
        # DataExtractor 已经在其构造函数中初始化了所有需要的表格
        # 包括股东数据相关的表格，因此不需要重复初始化
    
    def get_shareholder_info(self):
        """获取股东信息并分类保存"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 1. 访问集团页面
                print(f"正在访问集团页面: {self.group_url}")
                self.driver.get(self.group_url)
                
                # 2. 检查登录状态
                if not self.check_login_status():
                    print("登录状态已失效，需要重新登录")
                    return False
                
                # 3. 定位到股东信息section并点击"查看更多"按钮
                try:
                    shareholder_section = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "section.component-group-shareholder#page-menu-shareholder-info"))
                    )
                    
                    more_button = shareholder_section.find_element(By.CSS_SELECTOR, "span.more")
                    more_button.click()
                    print("已点击查看更多按钮")
                except TimeoutException:
                    print("未找到查看更多按钮")
                    retry_count += 1
                    continue
                
                # 4. 等待弹出框加载
                try:
                    dialog_body = self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "el-dialog__body"))
                    )
                    print("弹出框已加载")
                except TimeoutException:
                    print("弹出框加载超时")
                    retry_count += 1
                    continue
                
                # 5. 处理标签页
                try:
                    # 获取标签页容器
                    tab_list = dialog_body.find_element(By.CSS_SELECTOR, "div.component-my-follow-header div[role='tablist']")
                    tabs = tab_list.find_elements(By.CSS_SELECTOR, "div[role='tab']")
                    print(f"找到 {len(tabs)} 个标签页")
                    
                    # 打印所有标签页的文本
                    for i, tab in enumerate(tabs):
                        print(f"标签 {i+1}: {tab.text}")
                    
                    # 处理集团成员标签
                    try:
                        member_tab = dialog_body.find_element(By.CSS_SELECTOR, "div[id='tab-0']")
                        member_tab.click()
                        print("\n处理集团成员标签")
                        time.sleep(2)
                        
                        content_container = dialog_body.find_element(By.CSS_SELECTOR, "article.content")
                        # 检查内容是否为空
                        if content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item"):
                            self.data_extractor.scroll_container(content_container)
                            self.data_extractor.extract_group_members(content_container)
                        else:
                            print("集团成员标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理集团成员标签时出错: {str(e)}")
                    
                    # 处理对外投资标签
                    try:
                        investment_tab = dialog_body.find_element(By.CSS_SELECTOR, "div[id='tab-1']")
                        investment_tab.click()
                        print("\n处理对外投资标签")
                        time.sleep(2)
                        
                        content_container = dialog_body.find_element(By.CSS_SELECTOR, "article.content")
                        # 检查内容是否为空
                        if content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item"):
                            self.data_extractor.scroll_container(content_container)
                            self.data_extractor.extract_investments(content_container)
                        else:
                            print("对外投资标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理对外投资标签时出错: {str(e)}")
                    
                    # 处理投资方标签
                    try:
                        investor_tab = dialog_body.find_element(By.CSS_SELECTOR, "div[id='tab-2']")
                        investor_tab.click()
                        print("\n处理投资方标签")
                        time.sleep(2)
                        
                        content_container = dialog_body.find_element(By.CSS_SELECTOR, "article.content")
                        # 检查内容是否为空
                        if content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item"):
                            self.data_extractor.scroll_container(content_container)
                            self.data_extractor.extract_investors(content_container)
                        else:
                            print("投资方标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理投资方标签时出错: {str(e)}")
                    
                except TimeoutException:
                    print("未找到标签页")
                    retry_count += 1
                    continue
                
                # 关闭股东弹出框
                if not self.close_dialog():
                    print("无法关闭弹出框，但继续执行")
                
                print("\n所有股东数据提取完成")
                return True
                
            except Exception as e:
                print(f"处理页面时出错: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"正在进行第 {retry_count + 1} 次重试...")
                    time.sleep(3)
        
        print(f"已达到最大重试次数 ({max_retries})，跳过该页面")
        return False 