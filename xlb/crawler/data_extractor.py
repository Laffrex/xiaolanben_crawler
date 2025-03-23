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

    def save_to_excel(self, df, sheet_name, excel_path=None):
        """保存数据到Excel，增加返回值表示是否成功"""
        try:
            if excel_path is None:
                excel_path = self.output_file
            
            if os.path.exists(excel_path):
                # 如果文件存在，加载它
                try:
                    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"更新 {sheet_name} 表成功")
                    return True
                except Exception as e:
                    print(f"更新Excel表时出错: {str(e)}")
                    # 如果更新失败，尝试覆盖写入
                    try:
                        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer:
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                        print(f"覆盖写入 {sheet_name} 表成功")
                        return True
                    except Exception as e2:
                        print(f"覆盖写入Excel表时出错: {str(e2)}")
                        return False
            else:
                # 如果文件不存在，创建它
                try:
                    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"创建 {sheet_name} 表成功")
                    return True
                except Exception as e:
                    print(f"创建Excel表时出错: {str(e)}")
                    return False
        except Exception as e:
            print(f"保存Excel表时发生未知错误: {str(e)}")
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

    def scroll_container(self, content_container, content_type=None):
        """滚动加载内容 - 优化增强版，增加对加载更多按钮的处理"""
        max_scroll_attempts = 50  # 适应更多内容的滚动次数
        scroll_timeout = time.time() + 120  # 120秒超时
        progress_interval = 2  # 每滚动5次显示一次详细进度
        
        # 记录初始项目数和加载按钮点击次数
        initial_items_count = 0
        load_more_clicks = 0
        max_load_more_clicks = 20  # 防止无限循环
        
        try:
            # 初始化滚动计数和高度
            scroll_count = 0
            items_before = 0
            
            # 根据内容类型选择合适的选择器
            item_selector = "a.component-shareholder-item"
            if content_type == None or content_type == "":
                # 通用选择器，适用于所有类型
                item_selector = "a.component-shareholder-item, a.component-app-item, a.component-media-item, a.component-website-item"
            
            # 尝试获取初始项目数量
            try:
                items_before = len(content_container.find_elements(By.CSS_SELECTOR, item_selector))
                initial_items_count = items_before
                print(f"初始项目数量: {items_before}")
            except Exception as e:
                print(f"获取初始项目数量出错: {str(e)}")
                
            # 记录初始高度
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
            print(f"初始内容高度: {last_height}px")
            
            # 主循环 - 处理滚动和加载更多按钮
            while (scroll_count < max_scroll_attempts and 
                   time.time() < scroll_timeout and 
                   load_more_clicks < max_load_more_clicks):
                try:
                    # 1. 首先滚动到底部
                    self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
                    time.sleep(2.5)  # 等待内容加载
                    
                    # 2. 检查是否有"加载更多"或"查看更多"按钮
                    load_more_btn = None
                    
                    # 多种可能的查找方式 - 只对股东数据相关内容进行按钮查找
                    if content_type in ['group_members', 'investments', 'investors'] or item_selector == "a.component-shareholder-item":
                        try:
                            # 方式1: 通过文本内容查找加载更多按钮
                            load_more_elements = content_container.find_elements(
                                By.XPATH, 
                                ".//*[contains(text(),'加载更多') or contains(text(),'查看更多') or contains(text(),'加载') or contains(text(),'更多')]"
                            )
                            
                            # 方式2: 通过类名查找加载更多按钮
                            if not load_more_elements:
                                load_more_elements = content_container.find_elements(
                                    By.CSS_SELECTOR, 
                                    ".load-more, .more, .view-more, button.el-button, .el-button--text"
                                )
                            
                            # 检查找到的元素是否可见和可点击
                            for element in load_more_elements:
                                if element.is_displayed() and element.is_enabled():
                                    load_more_btn = element
                                    break
                                    
                            if load_more_btn:
                                btn_text = "无文本"
                                try:
                                    btn_text = load_more_btn.text.strip()
                                except:
                                    pass
                                
                                print(f"找到'加载更多'按钮: {btn_text}")
                                load_more_btn.click()
                                load_more_clicks += 1
                                print(f"已点击'加载更多'按钮 {load_more_clicks} 次")
                                time.sleep(3)  # 等待新内容加载
                                
                                # 获取点击后的项目数量
                                try:
                                    new_items_count = len(content_container.find_elements(By.CSS_SELECTOR, item_selector))
                                    items_diff = new_items_count - items_before
                                    if items_diff > 0:
                                        print(f"点击后项目数量从 {items_before} 增加到 {new_items_count}，新增 {items_diff} 个")
                                        items_before = new_items_count
                                    else:
                                        print(f"点击后项目数量未增加（当前 {new_items_count} 个），可能已加载全部内容")
                                        if load_more_clicks >= 3:  # 连续点击3次没有新数据，认为已加载完成
                                            break
                                except Exception as e:
                                    print(f"获取点击后项目数量出错: {str(e)}")
                                
                                # 继续下一轮循环
                                continue
                        except Exception as e:
                            print(f"查找'加载更多'按钮时出错: {str(e)}")
                    
                    # 3. 如果没有找到加载更多按钮或不是股东数据类型，执行常规滚动操作
                    
                    # 计算当前容器的可见高度
                    container_height = self.driver.execute_script(
                        "return arguments[0].clientHeight || arguments[0].offsetHeight;", content_container)
                    
                    # 向上滚动一小段距离（约20%的容器高度）- 回弹策略
                    scroll_up_distance = int(container_height * 0.2)
                    current_scroll = self.driver.execute_script("return arguments[0].scrollTop;", content_container)
                    self.driver.execute_script(
                        "arguments[0].scrollTo(0, arguments[1]);", 
                        content_container, 
                        max(0, current_scroll - scroll_up_distance)
                    )
                    time.sleep(1)  # 等待短暂时间
                    
                    # 再次向下滚动到底部
                    self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
                    time.sleep(1)  # 等待内容加载
                    
                    # 每隔一定次数显示详细进度
                    if scroll_count % progress_interval == 0:
                        # 尝试获取当前项目数量，用于进度比较
                        try:
                            items_current = len(content_container.find_elements(By.CSS_SELECTOR, item_selector))
                            items_diff = items_current - items_before
                            if items_diff > 0:
                                print(f"进度更新: 已加载 {items_current} 个项目，本次新增 {items_diff} 个")
                                items_before = items_current
                        except:
                            pass
                    
                    # 检查滚动高度变化
                    new_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
                    
                    # 如果高度没有变化，说明可能已经到达底部
                    if new_height == last_height:
                        # 连续两次高度相同，可能已到达底部
                        # 再尝试一次回弹操作，确保真的到底了
                        if scroll_count > 0:  # 至少已经滚动过一次
                            print("检测到可能已到达底部，尝试最后一次回弹...")
                            # 最后一次回弹尝试，使用更大的回弹距离
                            self.driver.execute_script(
                                "arguments[0].scrollTo(0, arguments[1]);", 
                                content_container, 
                                max(0, current_scroll - scroll_up_distance * 2)  # 更大的回弹距离
                            )
                            time.sleep(1.5)
                            self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
                            time.sleep(1.5)
                            
                            final_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
                            if final_height == new_height:
                                # 尝试最后的随机滚动
                                for i in range(3):
                                    random_pos = int(new_height * 0.7 * (i+1)/3)  # 在70%高度范围内的不同位置
                                    self.driver.execute_script(
                                        "arguments[0].scrollTo(0, arguments[1]);", 
                                        content_container, random_pos
                                    )
                                    time.sleep(1)
                                    
                                # 最后再滚动到底部
                                self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", content_container)
                                time.sleep(2)
                                
                                # 再次检查高度
                                very_final_height = self.driver.execute_script("return arguments[0].scrollHeight", content_container)
                                if very_final_height == final_height:
                                    print("已确认到达底部，滚动完成")
                                    
                                    # 最终验证：检查是否获取了所有项目
                                    try:
                                        final_items = len(content_container.find_elements(By.CSS_SELECTOR, item_selector))
                                        print(f"滚动完成! 共加载了 {final_items} 个项目")
                                    except:
                                        pass
                                        
                                    break
                                else:
                                    # 随机滚动找到了更多内容
                                    new_height = very_final_height
                                    print(f"随机滚动后找到更多内容，继续滚动。新高度: {new_height}px")
                            else:
                                # 最后一次回弹找到了更多内容
                                new_height = final_height
                                print(f"回弹操作找到更多内容，继续滚动。新高度: {new_height}px")
                        else:
                            print("首次滚动后未发现更多内容，可能已到达底部")
                            break
                    
                    last_height = new_height
                    scroll_count += 1
                    
                    # 打印滚动进度
                    elapsed_time = time.time() - (scroll_timeout -120)  # 已经过去的时间
                    remaining_time = max(0, scroll_timeout - time.time())
                    progress_percent = min(100, (scroll_count / max_scroll_attempts) * 100)
                    print(f"滚动进度: {progress_percent:.1f}% ({scroll_count}/{max_scroll_attempts}) | 已用时: {elapsed_time:.1f}秒 | 剩余时间: {remaining_time:.1f}秒 | 当前高度: {new_height}px")
                    
                except Exception as e:
                    print(f"滚动过程中出错: {str(e)}，尝试继续滚动")
                    time.sleep(1)  # 遇到错误时短暂暂停
            
            # 检查滚动终止原因
            if time.time() >= scroll_timeout:
                print(f"滚动加载超时 ({scroll_timeout-time.time()+(scroll_timeout-120):.1f}秒)，但已加载部分内容")
            elif scroll_count >= max_scroll_attempts:
                print(f"达到最大滚动次数 ({max_scroll_attempts})，但已加载部分内容")
            elif load_more_clicks >= max_load_more_clicks:
                print(f"达到最大加载更多点击次数 ({max_load_more_clicks})，但已加载部分内容")
                
            # 最终滚动到顶部，确保后续处理从头开始
            self.driver.execute_script("arguments[0].scrollTo(0, 0);", content_container)
            
            # 检查最终结果
            if content_type in ['group_members', 'investments', 'investors'] or item_selector == "a.component-shareholder-item":
                try:
                    final_count = len(content_container.find_elements(By.CSS_SELECTOR, item_selector))
                    print(f"数据加载总结: 初始项目数: {initial_items_count}, 最终项目数: {final_count}, 增加了: {final_count - initial_items_count}")
                    if load_more_clicks > 0:
                        print(f"共点击了'加载更多'按钮 {load_more_clicks} 次")
                except Exception as e:
                    print(f"计算最终项目数时出错: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"滚动容器时出现异常: {str(e)}")
            # 出现异常时尝试滚动到顶部
            try:
                self.driver.execute_script("arguments[0].scrollTo(0, 0);", content_container)
            except:
                pass
            return False

    def extract_group_members(self, content_container):
        """提取集团成员信息 - 增强版，增加数据验证和日志输出"""
        results = []
        
        # 首先确保所有成员项已加载
        print("开始提取集团成员信息...")
        
        # 查找所有集团成员项
        member_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
        original_count = len(member_items)
        print(f"找到 {original_count} 个集团成员")
        
        # 如果数量很少，提示用户可能加载不完整
        if original_count <= 30:  # 小蓝本每页通常显示30条记录
            print(f"警告: 只找到 {original_count} 个成员，可能未完全加载所有数据")
        
        # 提取每个成员信息
        success_count = 0
        error_count = 0
        
        # 使用进度指示器，便于追踪大量数据的提取进度
        progress_interval = max(1, min(50, int(original_count / 10)))  # 至少1个，最多50个，约每10%报告一次
        
        for index, item in enumerate(member_items):
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.name-impact p.name").text.strip()
                link = item.get_attribute('href')
                results.append({'成员名': name, '成员链接': link})
                success_count += 1
                
                # 定期显示进度
                if (index + 1) % progress_interval == 0 or index + 1 == original_count:
                    progress_percent = ((index + 1) / original_count) * 100
                    print(f"提取进度: {progress_percent:.1f}% ({index + 1}/{original_count})")
            except Exception as e:
                error_count += 1
                print(f"提取第 {index + 1} 个集团成员信息出错: {str(e)}")
        
        # 保存到Excel前，先检查提取是否成功
        if success_count == 0:
            print("警告: 未能成功提取任何集团成员信息!")
            return []
        
        print(f"集团成员提取完成: 成功 {success_count} 个, 失败 {error_count} 个, 成功率: {(success_count/original_count*100):.1f}%")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('集团成员', ['成员名', '成员链接'])
                if not existing_df.empty:
                    print(f"发现现有数据 {len(existing_df)} 条，进行合并...")
                    # 检查是否有新增数据
                    new_links = set(df['成员链接']) - set(existing_df['成员链接'])
                    if new_links:
                        print(f"发现 {len(new_links)} 条新数据，将合并到现有数据中")
                    else:
                        print("没有发现新数据，现有数据已包含所有集团成员")
                    
                    # 合并数据
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    original_len = len(df)
                    df = df.drop_duplicates(subset=['成员链接'], keep='last')
                    if original_len > len(df):
                        print(f"去重后减少了 {original_len - len(df)} 条重复记录")
                else:
                    print("没有发现现有数据，将创建新表")
            except Exception as e:
                print(f"读取现有集团成员数据时出错: {str(e)}")
            
            # 使用增强的save_to_excel方法保存
            save_success = self.save_to_excel(df, '集团成员')
            if save_success:
                print(f"成功保存 {len(df)} 条集团成员记录到Excel文件")
            else:
                print(f"保存集团成员数据失败，但已在内存中提取了 {len(results)} 条记录")
        
        return results

    def extract_investments(self, content_container):
        """提取对外投资信息 - 增强版，增加数据验证和日志输出"""
        results = []
        
        # 首先确保所有投资项已加载
        print("开始提取对外投资信息...")
        
        # 查找所有对外投资项
        investment_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
        original_count = len(investment_items)
        print(f"找到 {original_count} 个对外投资")
        
        # 如果数量很少，提示用户可能加载不完整
        if original_count <= 30:  # 小蓝本每页通常显示30条记录
            print(f"警告: 只找到 {original_count} 个对外投资，可能未完全加载所有数据")
        
        # 提取每个投资信息
        success_count = 0
        error_count = 0
        
        # 使用进度指示器，便于追踪大量数据的提取进度
        progress_interval = max(1, min(50, int(original_count / 10)))  # 至少1个，最多50个，约每10%报告一次
        
        for index, item in enumerate(investment_items):
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.name-impact p.name").text.strip()
                link = item.get_attribute('href')
                results.append({'被投资方': name, '被投资方链接': link})
                success_count += 1
                
                # 定期显示进度
                if (index + 1) % progress_interval == 0 or index + 1 == original_count:
                    progress_percent = ((index + 1) / original_count) * 100
                    print(f"提取进度: {progress_percent:.1f}% ({index + 1}/{original_count})")
            except Exception as e:
                error_count += 1
                print(f"提取第 {index + 1} 个对外投资信息出错: {str(e)}")
        
        # 保存到Excel前，先检查提取是否成功
        if success_count == 0:
            print("警告: 未能成功提取任何对外投资信息!")
            return []
        
        print(f"对外投资提取完成: 成功 {success_count} 个, 失败 {error_count} 个, 成功率: {(success_count/original_count*100):.1f}%")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('对外投资', ['被投资方', '被投资方链接'])
                if not existing_df.empty:
                    print(f"发现现有数据 {len(existing_df)} 条，进行合并...")
                    # 检查是否有新增数据
                    new_links = set(df['被投资方链接']) - set(existing_df['被投资方链接'])
                    if new_links:
                        print(f"发现 {len(new_links)} 条新数据，将合并到现有数据中")
                    else:
                        print("没有发现新数据，现有数据已包含所有对外投资")
                    
                    # 合并数据
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    original_len = len(df)
                    df = df.drop_duplicates(subset=['被投资方链接'], keep='last')
                    if original_len > len(df):
                        print(f"去重后减少了 {original_len - len(df)} 条重复记录")
                else:
                    print("没有发现现有数据，将创建新表")
            except Exception as e:
                print(f"读取现有对外投资数据时出错: {str(e)}")
            
            # 使用增强的save_to_excel方法保存
            save_success = self.save_to_excel(df, '对外投资')
            if save_success:
                print(f"成功保存 {len(df)} 条对外投资记录到Excel文件")
            else:
                print(f"保存对外投资数据失败，但已在内存中提取了 {len(results)} 条记录")
        
        return results

    def extract_investors(self, content_container):
        """提取投资方信息 - 增强版，增加数据验证和日志输出"""
        results = []
        
        # 首先确保所有投资方项已加载
        print("开始提取投资方信息...")
        
        # 查找所有投资方项
        investor_items = content_container.find_elements(By.CSS_SELECTOR, "div.content-item a.component-shareholder-item")
        original_count = len(investor_items)
        print(f"找到 {original_count} 个投资方")
        
        # 如果数量很少，提示用户可能加载不完整
        if original_count <= 30:  # 小蓝本每页通常显示30条记录
            print(f"警告: 只找到 {original_count} 个投资方，可能未完全加载所有数据")
        
        # 提取每个投资方信息
        success_count = 0
        error_count = 0
        
        # 使用进度指示器，便于追踪大量数据的提取进度
        progress_interval = max(1, min(50, int(original_count / 10)))  # 至少1个，最多50个，约每10%报告一次
        
        for index, item in enumerate(investor_items):
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.name-impact p.name").text.strip()
                link = item.get_attribute('href')
                results.append({'投资方': name, '投资方链接': link})
                success_count += 1
                
                # 定期显示进度
                if (index + 1) % progress_interval == 0 or index + 1 == original_count:
                    progress_percent = ((index + 1) / original_count) * 100
                    print(f"提取进度: {progress_percent:.1f}% ({index + 1}/{original_count})")
            except Exception as e:
                error_count += 1
                print(f"提取第 {index + 1} 个投资方信息出错: {str(e)}")
        
        # 保存到Excel前，先检查提取是否成功
        if success_count == 0:
            print("警告: 未能成功提取任何投资方信息!")
            return []
        
        print(f"投资方提取完成: 成功 {success_count} 个, 失败 {error_count} 个, 成功率: {(success_count/original_count*100):.1f}%")
        
        # 保存到Excel
        if results:
            df = pd.DataFrame(results)
            # 检查是否存在现有数据并合并
            try:
                existing_df = self._read_existing_data('投资方', ['投资方', '投资方链接'])
                if not existing_df.empty:
                    print(f"发现现有数据 {len(existing_df)} 条，进行合并...")
                    # 检查是否有新增数据
                    new_links = set(df['投资方链接']) - set(existing_df['投资方链接'])
                    if new_links:
                        print(f"发现 {len(new_links)} 条新数据，将合并到现有数据中")
                    else:
                        print("没有发现新数据，现有数据已包含所有投资方")
                    
                    # 合并数据
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重
                    original_len = len(df)
                    df = df.drop_duplicates(subset=['投资方链接'], keep='last')
                    if original_len > len(df):
                        print(f"去重后减少了 {original_len - len(df)} 条重复记录")
                else:
                    print("没有发现现有数据，将创建新表")
            except Exception as e:
                print(f"读取现有投资方数据时出错: {str(e)}")
            
            # 使用增强的save_to_excel方法保存
            save_success = self.save_to_excel(df, '投资方')
            if save_success:
                print(f"成功保存 {len(df)} 条投资方记录到Excel文件")
            else:
                print(f"保存投资方数据失败，但已在内存中提取了 {len(results)} 条记录")
        
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