from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
try:
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    from selenium.webdriver import ActionChains
import time
from ..base_crawler import BaseCrawler
from ..data_extractor import DataExtractor
import pandas as pd

class CompanyCrawler(BaseCrawler):
    def __init__(self, driver, output_file, url):
        super().__init__(driver, output_file)
        self.data_extractor = DataExtractor(driver, output_file)
        self.company_url = url

    def process_popup_content(self, pane, item_selector, sheet_name, extract_method=None):
        """处理弹出框内容的通用方法
        
        Args:
            pane: 标签页面板元素
            item_selector: 要查找的项目选择器
            sheet_name: Excel表格名称
            extract_method: 可选的提取方法，如果为None则在弹出框中执行默认提取逻辑
            
        Returns:
            bool: 是否在弹出框中成功处理了数据
        """
        processed = False
        # 检查是否有"查看更多"按钮
        try:
            # 使用find_elements而不是find_element，这样在找不到元素时不会抛出异常
            more_buttons = pane.find_elements(By.CSS_SELECTOR, "span.more")
            if not more_buttons:
                # 如果没有找到按钮，安静地返回False
                return False
                
            more_button = more_buttons[0]
            print(f"找到{sheet_name}标签的'查看更多'按钮，准备点击...")
            more_button.click()
            print(f"已点击{sheet_name}的'查看更多'按钮，等待弹窗加载...")
            time.sleep(2)
            
            # 等待弹出框加载
            try:
                dialog_body = self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "el-dialog__body"))
                )
                print("弹出框已加载")
                
                # 在弹出框中获取内容容器
                product_more_content = dialog_body.find_element(By.CLASS_NAME, "product-more-content")
                
                # 检查内容是否为空
                items = product_more_content.find_elements(By.CSS_SELECTOR, item_selector)
                if items:
                    print(f"发现 {len(items)} 个{sheet_name}项目，开始加载更多数据...")
                    self.data_extractor.scroll_container(product_more_content)
                    
                    if extract_method:
                        # 使用提供的方法提取数据
                        extract_method(product_more_content)
                    else:
                        # 根据sheet_name执行默认提取逻辑
                        if sheet_name == 'APP':
                            results = []
                            for item in items:
                                try:
                                    link = item.get_attribute('href')
                                    name_element = item.find_element(By.CSS_SELECTOR, "p.name span.text")
                                    name = name_element.text.strip()
                                    results.append({'产品名': name, '产品链接': link})
                                except:
                                    # 不输出具体错误，只是跳过这一项
                                    continue
                            
                            if results:
                                df = pd.DataFrame(results)
                                self.data_extractor.save_to_excel(df, sheet_name)
                                print(f"成功保存 {len(results)} 条{sheet_name}记录到Excel文件")
                    
                    processed = True
                else:
                    print(f"{sheet_name}标签内容为空，跳过处理")
            except TimeoutException:
                print("弹出框加载超时")
            finally:
                # 无论处理成功与否，都尝试关闭弹出框
                popup_closed = False
                
                # 方法1：点击关闭按钮
                try:
                    print("尝试通过ESC键关闭弹出框...")
                    ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
                    print("通过ESC键关闭弹出框成功")
                    popup_closed = True
                except:
                    # 不输出具体错误，只提示ESC键关闭失败
                    print("通过ESC键关闭弹出框失败")
        except:
            # 不输出具体错误，只返回False表示没有处理
            return False
        
        return processed

    def get_company_and_website_info(self):
        """获取产品信息并分类保存"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 1. 访问公司页面
                print(f"\n===== 正在访问公司页面: {self.company_url} =====")
                self.driver.get(self.company_url)
                
                # 2. 检查登录状态
                if not self.check_login_status():
                    print("登录状态检查: 已失效，需要重新登录")
                    return False
                
                # 3. 定位到产品信息section
                try:
                    product_section = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "section.component-company-product#page-menu-project-info"))
                    )
                    print("已找到产品信息区域，准备提取数据...")
                except TimeoutException:
                    print("未找到产品信息区域，页面可能加载不完整")
                    retry_count += 1
                    continue
                
                # 4. 处理标签页
                try:
                    # 获取标签页容器
                    tabs_container = product_section.find_element(By.CSS_SELECTOR, "div[role='tablist'].el-tabs__nav.is-top")
                    print("已找到产品信息标签页容器")
                    
                    # 获取所有标签页
                    tabs = tabs_container.find_elements(By.CSS_SELECTOR, "div[role='tab']")
                    print(f"找到 {len(tabs)} 个产品标签页")
                    
                    # 打印所有标签页的文本和状态
                    for i, tab in enumerate(tabs):
                        tab_id = tab.get_attribute('id')
                        tab_text = tab.text
                        tab_class = tab.get_attribute('class')
                        tab_disabled = 'is-disabled' in tab_class
                        tab_content = tab.text.split('•')[-1].strip() if '•' in tab.text else ''
                        
                        print(f"标签 {i+1}: {tab_text}, ID={tab_id}, 状态={'禁用' if tab_disabled else '启用'}")
                    
                    # 统计处理成功的标签数
                    processed_tabs = 0
                    
                    # 处理APP标签页
                    try:
                        app_tab = tabs_container.find_element(By.CSS_SELECTOR, "div#tab-app[role='tab']")
                        # 检查标签是否被禁用或内容为null
                        app_tab_class = app_tab.get_attribute('class')
                        app_tab_disabled = 'is-disabled' in app_tab_class
                        app_tab_content = app_tab.text.split('•')[-1].strip() if '•' in app_tab.text else ''
                        
                        if app_tab_disabled or app_tab_content == 'null':
                            print("APP标签被禁用或内容为空，跳过处理")
                        else:
                            app_tab.click()
                            print("\n===== 准备处理APP标签 =====")
                            time.sleep(2)
                            
                            # 检查标签页是否被正确选中
                            tab_class = app_tab.get_attribute('class')
                            if 'is-active' in tab_class:
                                print("APP标签已正确选中")
                            else:
                                print("警告: APP标签可能未正确选中")
                            
                            # 等待APP内容加载
                            app_pane = self.wait.until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "div#pane-app[role='tabpanel']"))
                            )
                            
                            # 尝试在弹出框中处理
                            processed_in_popup = self.process_popup_content(
                                app_pane, 
                                "a.component-app-item", 
                                "APP",
                                extract_method=self.data_extractor.extract_app_content if hasattr(self.data_extractor, "extract_app_content") else None
                            )
                            
                            # 如果没有在弹出框中处理过数据，则使用常规方式处理
                            if not processed_in_popup:
                                print("数据无需弹窗展示，直接从页面提取APP数据")
                                # 常规方式处理：获取内容容器
                                content_container = app_pane.find_element(By.CSS_SELECTOR, "div.content-item")
                                
                                # 检查内容是否为空
                                app_items = content_container.find_elements(By.CSS_SELECTOR, "a.component-app-item")
                                if app_items:
                                    print(f"发现 {len(app_items)} 个APP项目，开始加载更多数据...")
                                    self.data_extractor.scroll_container(content_container)
                                    
                                    # 使用提取方法处理数据
                                    if hasattr(self.data_extractor, "extract_app_content"):
                                        self.data_extractor.extract_app_content(content_container)
                                    else:
                                        # 默认提取逻辑
                                        results = []
                                        for index, item in enumerate(app_items):
                                            try:
                                                link = item.get_attribute('href')
                                                name_element = item.find_element(By.CSS_SELECTOR, "p.name span.text")
                                                name = name_element.text.strip()
                                                results.append({'产品名': name, '产品链接': link})
                                            except Exception as e:
                                                print(f"提取第 {index + 1} 个APP信息出错: {str(e)}")
                                        
                                        # 保存到Excel
                                        if results:
                                            df = pd.DataFrame(results)
                                            self.data_extractor.save_to_excel(df, 'APP')
                                            print(f"成功保存 {len(results)} 条APP记录到Excel文件")
                                            processed_tabs += 1
                                else:
                                    print("APP标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理APP标签时出错: {str(e)}")
                    
                    # 处理Media标签页
                    try:
                        media_tab = tabs_container.find_element(By.CSS_SELECTOR, "div#tab-media[role='tab']")
                        # 检查标签是否被禁用或内容为null
                        media_tab_class = media_tab.get_attribute('class')
                        media_tab_disabled = 'is-disabled' in media_tab_class
                        media_tab_content = media_tab.text.split('•')[-1].strip() if '•' in media_tab.text else ''
                        
                        if media_tab_disabled or media_tab_content == 'null':
                            print("Media标签被禁用或内容为空，跳过处理")
                        else:
                            media_tab.click()
                            print("\n===== 准备处理Media标签 =====")
                            time.sleep(2)
                            
                            # 检查标签页是否被正确选中
                            tab_class = media_tab.get_attribute('class')
                            if 'is-active' in tab_class:
                                print("Media标签已正确选中")
                            else:
                                print("警告: Media标签可能未正确选中")
                            
                            # 等待Media内容加载
                            media_pane = self.wait.until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "div#pane-media[role='tabpanel']"))
                            )
                            
                            # 尝试在弹出框中处理
                            processed_in_popup = self.process_popup_content(
                                media_pane, 
                                "a.component-media-item", 
                                "Media", 
                                extract_method=self.data_extractor.extract_media_content
                            )
                            
                            # 如果没有在弹出框中处理过数据，则使用常规方式处理
                            if not processed_in_popup:
                                print("数据无需弹窗展示，直接从页面提取Media数据")
                                # 常规方式处理：获取内容容器
                                content_container = media_pane.find_element(By.CSS_SELECTOR, "div.content-item")
                                
                                # 检查内容是否为空
                                if content_container.find_elements(By.CSS_SELECTOR, "a.component-media-item"):
                                    print("发现媒体数据，开始加载更多数据...")
                                    self.data_extractor.scroll_container(content_container)
                                    self.data_extractor.extract_media_content(content_container)
                                    processed_tabs += 1
                                else:
                                    print("Media标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理Media标签时出错: {str(e)}")
                    
                    # 处理Website标签页
                    try:
                        website_tab = tabs_container.find_element(By.CSS_SELECTOR, "div#tab-website[role='tab']")
                        # 检查标签是否被禁用或内容为null
                        website_tab_class = website_tab.get_attribute('class')
                        website_tab_disabled = 'is-disabled' in website_tab_class
                        website_tab_content = website_tab.text.split('•')[-1].strip() if '•' in website_tab.text else ''
                        
                        if website_tab_disabled or website_tab_content == 'null':
                            print("Website标签被禁用或内容为空，跳过处理")
                        else:
                            website_tab.click()
                            print("\n===== 准备处理Website标签 =====")
                            time.sleep(2)
                            
                            # 检查标签页是否被正确选中
                            tab_class = website_tab.get_attribute('class')
                            if 'is-active' in tab_class:
                                print("Website标签已正确选中")
                            else:
                                print("警告: Website标签可能未正确选中")
                            
                            # 等待Website内容加载
                            website_pane = self.wait.until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "div#pane-website[role='tabpanel']"))
                            )
                            
                            # 尝试在弹出框中处理
                            processed_in_popup = self.process_popup_content(
                                website_pane, 
                                "a.component-website-item", 
                                "Website", 
                                extract_method=self.data_extractor.extract_website_content
                            )
                            
                            # 如果没有在弹出框中处理过数据，则使用常规方式处理
                            if not processed_in_popup:
                                print("数据无需弹窗展示，直接从页面提取Website数据")
                                # 常规方式处理：获取内容容器
                                content_container = website_pane.find_element(By.CSS_SELECTOR, "div.content-item")
                                
                                # 检查内容是否为空
                                if content_container.find_elements(By.CSS_SELECTOR, "a.component-website-item"):
                                    print("发现网站数据，开始加载更多数据...")
                                    self.data_extractor.scroll_container(content_container)
                                    self.data_extractor.extract_website_content(content_container)
                                    processed_tabs += 1
                                else:
                                    print("Website标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理Website标签时出错: {str(e)}")
                    
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