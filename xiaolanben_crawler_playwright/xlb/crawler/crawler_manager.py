from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from .data_extractor import DataExtractor

class CrawlerManager:
    def __init__(self, driver, output_file):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.data_extractor = DataExtractor(driver, output_file)
        self.group_url = "https://sou.xiaolanben.com/group/qccf3189b6854ab40560a1c079b40efa6"

    def get_company_and_website_info(self):
        """获取产品信息并分类保存"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 1. 访问集团页面
                print(f"正在访问集团页面: {self.group_url}")
                self.driver.get(self.group_url)
                
                # 2. 检查登录状态
                if "login" in self.driver.current_url:
                    print("登录状态已失效，需要重新登录")
                    return False
                
                # 3. 点击"查看更多"按钮
                try:
                    # 首先定位到正确的section
                    product_section = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "section.component-company-product#page-menu-project-info"))
                    )
                    
                    more_button = product_section.find_element(By.CSS_SELECTOR, "span.more")
                    more_button.click()
                    print("已点击查看更多按钮")
                except TimeoutException:
                    print("未找到查看更多按钮")
                    retry_count += 1
                    continue
                
                # 等待弹出框加载
                try:
                    dialog_body = self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "el-dialog__body"))
                    )
                    print("弹出框已加载")
                except TimeoutException:
                    print("弹出框加载超时")
                    retry_count += 1
                    continue
                
                # 4. 处理标签页
                try:
                    # 修改选择器，只获取实际的标签页
                    tabs = dialog_body.find_elements(By.CSS_SELECTOR, "div.el-tabs__nav-wrap div.el-tabs__item")
                    print(f"找到 {len(tabs)} 个标签页")
                    
                    # 打印所有标签页的文本
                    for i, tab in enumerate(tabs):
                        print(f"标签 {i+1}: {tab.text}")
                    
                except TimeoutException:
                    print("未找到标签页")
                    retry_count += 1
                    continue
                
                # 处理APP标签页
                try:
                    app_tab = dialog_body.find_element(By.CSS_SELECTOR, "div.el-tabs__item[aria-controls='pane-0']")
                    app_tab.click()
                    print("\n处理APP标签页")
                    time.sleep(2)
                    
                    content_container = dialog_body.find_element(By.CLASS_NAME, "product-more-content")
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
                    media_tab = dialog_body.find_element(By.CSS_SELECTOR, "div.el-tabs__item[aria-controls='pane-1']")
                    media_tab.click()
                    print("\n处理Media标签页")
                    time.sleep(2)
                    
                    content_container = dialog_body.find_element(By.CLASS_NAME, "product-more-content")
                    # 检查内容是否为空
                    if content_container.find_elements(By.CSS_SELECTOR, "a.component-media-item"):
                        self.data_extractor.scroll_container(content_container)
                        self.data_extractor.extract_media_content(content_container)
                    else:
                        print("Media标签页内容为空，跳过处理")
                except Exception as e:
                    print(f"处理Media标签页时出错: {str(e)}")
                
                # 处理Website标签页
                try:
                    website_tab = dialog_body.find_element(By.CSS_SELECTOR, "div.el-tabs__item[aria-controls='pane-2']")
                    website_tab.click()
                    print("\n处理Website标签页")
                    time.sleep(2)
                    
                    content_container = dialog_body.find_element(By.CLASS_NAME, "product-more-content")
                    # 检查内容是否为空
                    if content_container.find_elements(By.CSS_SELECTOR, "a.component-website-item"):
                        self.data_extractor.scroll_container(content_container)
                        self.data_extractor.extract_website_content(content_container)
                    else:
                        print("Website标签页内容为空，跳过处理")
                except Exception as e:
                    print(f"处理Website标签页时出错: {str(e)}")
                
                # 关闭产品弹出框
                try:
                    print("\n正在关闭产品弹出框...")
                    # 点击弹出框外的区域来关闭它
                    dialog = self.driver.find_element(By.CLASS_NAME, "el-dialog__wrapper")
                    self.driver.execute_script("arguments[0].click();", dialog)
                    # 等待弹出框消失
                    self.wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "el-dialog__wrapper")))
                    print("产品弹出框已关闭")
                    time.sleep(2)  # 给页面一些时间来响应
                except Exception as e:
                    print(f"关闭产品弹出框时出错: {str(e)}")
                    # 尝试使用 Escape 键关闭
                    try:
                        from selenium.webdriver.common.keys import Keys
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(2)
                        print("使用 Escape 键关闭产品弹出框")
                    except Exception as e2:
                        print(f"使用 Escape 键关闭弹出框时出错: {str(e2)}")
                
                print("\n所有数据提取完成")
                return True
                
            except Exception as e:
                print(f"处理页面时出错: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"正在进行第 {retry_count + 1} 次重试...")
                    time.sleep(3)
        
        print(f"已达到最大重试次数 ({max_retries})，跳过该产品")
        return False 