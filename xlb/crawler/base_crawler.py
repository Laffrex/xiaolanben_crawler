from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import time

class BaseCrawler:
    def __init__(self, driver, output_file):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.output_file = output_file

    def check_login_status(self):
        """检查登录状态"""
        if "login" in self.driver.current_url:
            print("登录状态已失效，需要重新登录")
            return False
        return True

    def close_dialog(self):
        """关闭弹出框"""
        try:
            print("\n正在关闭弹出框...")
            # 点击弹出框外的区域来关闭它
            dialog = self.driver.find_element(By.CLASS_NAME, "el-dialog__wrapper")
            self.driver.execute_script("arguments[0].click();", dialog)
            # 等待弹出框消失
            self.wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "el-dialog__wrapper")))
            print("弹出框已关闭")
            time.sleep(2)  # 给页面一些时间来响应
            return True
        except Exception as e:
            print(f"关闭弹出框时出错: {str(e)}")
            # 尝试使用 Escape 键关闭
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(2)
                print("使用 Escape 键关闭弹出框")
                return True
            except Exception as e2:
                print(f"使用 Escape 键关闭弹出框时出错: {str(e2)}")
                return False 