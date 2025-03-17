from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json

class AuthManager:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.load_credentials()

    def load_credentials(self):
        """从配置文件加载登录凭证"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.username = config['username']
                self.password = config['password']
                self.login_url = config['login_url']
        except FileNotFoundError:
            print("请先创建配置文件 config.json")
            exit(1)

    def login(self):
        """执行登录操作"""
        try:
            # 打开登录页面
            print("正在打开登录页面...")
            self.driver.get(self.login_url)
            
            # 添加短暂延迟确保页面加载
            self.driver.implicitly_wait(5)
            print("页面已打开，正在查找登录表单...")
            
            # 等待并找到用户名输入框
            username_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "phone"))
            )
            print("找到手机号输入框，正在输入...")
            username_input.send_keys(self.username)
            
            # 找到密码输入框
            print("正在输入密码...")
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)
            
            # 点击同意协议按钮
            print("正在点击同意协议按钮...")
            try:
                agree_button = self.wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "checkmark"))
                )
                agree_button.click()
                print("已点击同意协议按钮")
            except TimeoutException:
                print("找不到同意协议按钮或按钮不可点击")
                raise
            
            # 点击登录按钮
            print("正在点击登录按钮...")
            try:
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "login-submit"))
                )
                login_button.click()
                print("已点击登录按钮")
            except TimeoutException:
                print("找不到登录按钮或按钮不可点击")
                raise
            
            # 等待登录成功
            print("等待页面跳转...")
            try:
                self.wait.until(
                    EC.url_changes(self.login_url)
                )
                print(f"当前URL: {self.driver.current_url}")
                print("登录成功！")
                return True
            except TimeoutException:
                print("登录可能失败，请检查登录状态")
                print(f"当前URL: {self.driver.current_url}")
                return False
            
        except TimeoutException:
            print("登录超时，请检查网络连接或登录信息")
            return False
        except Exception as e:
            print(f"登录过程中出现错误: {str(e)}")
            print(f"当前URL: {self.driver.current_url}")
            return False 