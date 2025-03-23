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
                    print("正在定位股东信息区域...")
                    shareholder_section = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "section.component-group-shareholder#page-menu-shareholder-info"))
                    )
                    
                    # 检查是否有"查看更多"按钮
                    try:
                        more_button = shareholder_section.find_element(By.CSS_SELECTOR, "span.more")
                        print("找到股东信息区域的'查看更多'按钮，准备点击...")
                        more_button.click()
                        print("已点击股东信息的'查看更多'按钮，等待弹窗加载...")
                        time.sleep(2)  # 等待弹窗加载
                    except:
                        print("未找到查看更多按钮，尝试直接获取股东数据")
                        # 如果没有"查看更多"按钮，可能数据量较少，尝试直接提取
                        try:
                            # 尝试直接从页面提取股东数据
                            content_container = shareholder_section.find_element(By.CSS_SELECTOR, "div.shareholder-content")
                            # 此处添加直接提取逻辑，暂不实现
                            print("页面股东数据较少，无需弹窗展示")
                        except:
                            print("无法直接从页面提取股东数据，继续尝试弹窗获取")
                            raise Exception("需要弹窗获取数据")
                except TimeoutException:
                    print("未找到股东信息区域，页面可能加载不完整")
                    retry_count += 1
                    print(f"正在进行第 {retry_count + 1} 次重试...")
                    continue
                except Exception as e:
                    if "需要弹窗获取数据" not in str(e):
                        print(f"定位股东信息区域时出错: {str(e)}")
                    retry_count += 1
                    continue
                
                # 4. 等待弹出框加载
                try:
                    print("等待弹出框加载...")
                    dialog_body = self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "el-dialog__body"))
                    )
                    print("弹出框已加载")
                except TimeoutException:
                    print("弹出框加载超时")
                    retry_count += 1
                    print(f"正在进行第 {retry_count + 1} 次重试...")
                    continue
                
                # 5. 处理标签页
                try:
                    # 获取标签页容器
                    print("查找标签页容器...")
                    tab_list = dialog_body.find_element(By.CSS_SELECTOR, "div.component-my-follow-header div[role='tablist']")
                    tabs = tab_list.find_elements(By.CSS_SELECTOR, "div[role='tab']")
                    print(f"找到 {len(tabs)} 个标签页")
                    
                    # 打印所有标签页的文本和tabindex属性
                    for i, tab in enumerate(tabs):
                        tab_index = tab.get_attribute('tabindex')
                        print(f"标签 {i+1}: {tab.text}, tabindex={tab_index}")
                    
                    # 统计处理成功的标签数
                    processed_tabs = 0
                    
                    # 处理集团成员标签
                    try:
                        print("\n===== 准备处理集团成员标签 =====")
                        # 查找并点击集团成员标签
                        member_tab = dialog_body.find_element(By.CSS_SELECTOR, "div[id='tab-0']")
                        member_tab.click()
                        print("已点击集团成员标签")
                        time.sleep(2)  # 等待标签页内容加载
                        
                        # 检查标签页是否被正确选中
                        tab_index = member_tab.get_attribute('tabindex')
                        if tab_index == "0":
                            print("集团成员标签已正确选中 (tabindex=0)")
                        else:
                            print(f"警告: 集团成员标签可能未正确选中 (tabindex={tab_index})")
                        
                        # 获取内容容器
                        content_container = dialog_body.find_element(By.CSS_SELECTOR, "div.product-more-content")
                        
                        # 检查内容是否为空
                        member_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
                        if member_items:
                            print(f"发现 {len(member_items)} 个集团成员项目，开始加载更多数据...")
                            
                            # 使用优化版滚动方法，专门处理集团成员
                            if self.data_extractor.scroll_container(content_container, ''):
                                print("数据加载完成，开始提取集团成员信息...")
                                
                                # 重新获取内容容器，避免StaleElementReferenceException
                                content_container = dialog_body.find_element(By.CSS_SELECTOR, "div.product-more-content")
                                
                                # 提取集团成员数据
                                extracted_items = self.data_extractor.extract_group_members(content_container)
                                
                                # 验证提取结果
                                if extracted_items and len(extracted_items) > 0:
                                    print(f"成功提取 {len(extracted_items)} 个集团成员数据")
                                    processed_tabs += 1
                                else:
                                    print("提取集团成员数据为空")
                            else:
                                print("加载集团成员数据失败")
                        else:
                            print("集团成员标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理集团成员标签时出错: {str(e)}")
                    
                    # 处理投资标签
                    try:
                        print("\n===== 准备处理对外投资标签 =====")
                        # 查找并点击对外投资标签
                        investment_tab = dialog_body.find_element(By.CSS_SELECTOR, "div[id='tab-1']")
                        investment_tab.click()
                        print("已点击对外投资标签")
                        time.sleep(2)  # 等待标签页内容加载
                        
                        # 检查标签页是否被正确选中
                        tab_index = investment_tab.get_attribute('tabindex')
                        if tab_index == "0":
                            print("对外投资标签已正确选中 (tabindex=0)")
                        else:
                            print(f"警告: 对外投资标签可能未正确选中 (tabindex={tab_index})")
                        
                        # 获取内容容器
                        content_container = dialog_body.find_element(By.CSS_SELECTOR, "article.content")
                        
                        # 检查内容是否为空
                        investment_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
                        
                        if investment_items:
                            print(f"发现 {len(investment_items)} 个对外投资项目，开始加载更多数据...")
                            
                            # 使用优化版滚动方法，专门处理对外投资
                            if self.data_extractor.scroll_container(content_container, ''):
                                print("数据加载完成，开始提取对外投资信息...")
                                
                                # 重新获取内容容器，避免StaleElementReferenceException
                                content_container = dialog_body.find_element(By.CSS_SELECTOR, "article.content")
                                
                                # 提取对外投资数据
                                extracted_items = self.data_extractor.extract_investments(content_container)
                                
                                # 验证提取结果
                                if extracted_items and len(extracted_items) > 0:
                                    print(f"成功提取 {len(extracted_items)} 个对外投资数据")
                                    processed_tabs += 1
                                else:
                                    print("提取对外投资数据为空")
                            else:
                                print("加载对外投资数据失败")
                        else:
                            print("对外投资标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理对外投资标签时出错: {str(e)}")
                    
                    # 处理投资方标签
                    try:
                        print("\n===== 准备处理投资方标签 =====")
                        # 查找并点击投资方标签
                        investor_tab = dialog_body.find_element(By.CSS_SELECTOR, "div[id='tab-2']")
                        investor_tab.click()
                        print("已点击投资方标签")
                        time.sleep(2)  # 等待标签页内容加载
                        
                        # 检查标签页是否被正确选中
                        tab_index = investor_tab.get_attribute('tabindex')
                        if tab_index == "0":
                            print("投资方标签已正确选中 (tabindex=0)")
                        else:
                            print(f"警告: 投资方标签可能未正确选中 (tabindex={tab_index})")
                        
                        # 获取内容容器
                        content_container = dialog_body.find_element(By.CSS_SELECTOR, "article.content")
                        
                        # 检查内容是否为空
                        investor_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
                        
                        if investor_items:
                            print(f"发现 {len(investor_items)} 个投资方项目，开始加载更多数据...")
                            
                            # 使用优化版滚动方法，专门处理投资方
                            if self.data_extractor.scroll_container(content_container, ''):
                                print("数据加载完成，开始提取投资方信息...")
                                
                                # 重新获取内容容器，避免StaleElementReferenceException
                                content_container = dialog_body.find_element(By.CSS_SELECTOR, "article.content")
                                
                                # 提取投资方数据
                                extracted_items = self.data_extractor.extract_investors(content_container)
                                
                                # 验证提取结果
                                if extracted_items and len(extracted_items) > 0:
                                    print(f"成功提取 {len(extracted_items)} 个投资方数据")
                                    processed_tabs += 1
                                else:
                                    print("提取投资方数据为空")
                            else:
                                print("加载投资方数据失败")
                        else:
                            print("投资方标签内容为空，跳过处理")
                    except Exception as e:
                        print(f"处理投资方标签时出错: {str(e)}")
                    
                    # 检查是否至少处理了一个标签
                    if processed_tabs > 0:
                        print(f"\n成功处理了 {processed_tabs}/{len(tabs)} 个标签页的数据")
                    else:
                        print("\n未能成功处理任何标签页的数据，所有标签页可能都为空或出错")
                        # 如果所有标签都处理失败，但已经尝试了所有标签，仍视为成功
                        if retry_count >= max_retries - 1:
                            print("已尝试所有重试次数，放弃继续尝试")
                            return True
                
                except TimeoutException:
                    print("未找到标签页")
                    retry_count += 1
                    print(f"正在进行第 {retry_count + 1} 次重试...")
                    continue
                
                # 关闭股东弹出框
                try:
                    print("正在关闭弹出框...")
                    if not self.close_dialog():
                        print("无法关闭弹出框，但继续执行")
                    else:
                        print("弹出框已关闭")
                    time.sleep(1)
                except Exception as e:
                    print(f"关闭弹出框时出错: {str(e)}，但继续执行")
                
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

    def close_dialog(self):
        """点击弹窗外部区域关闭弹窗"""
        try:
            # 使用JavaScript点击弹窗外部区域（对话框背景蒙层）
            close_script = """
            // 查找对话框蒙层元素
            const overlay = document.querySelector('.el-dialog__wrapper');
            
            if (overlay) {
                // 点击蒙层而非对话框本身，以关闭对话框
                // 计算蒙层的中心偏上位置，确保点击在对话框外
                const rect = overlay.getBoundingClientRect();
                const clickX = 10; // 靠近左边缘
                const clickY = 10; // 靠近上边缘
                
                // 创建并触发点击事件
                const clickEvent = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: clickX,
                    clientY: clickY
                });
                
                overlay.dispatchEvent(clickEvent);
                return true;
            }
            return false;
            """
            
            result = self.driver.execute_script(close_script)
            return result
        except Exception as e:
            print(f"尝试关闭弹窗时出错: {str(e)}")
            return False 