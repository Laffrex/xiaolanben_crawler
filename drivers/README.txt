ChromeDriver使用说明

1. 查看Chrome版本：
   - 打开Chrome浏览器
   - 点击右上角三个点
   - 点击"帮助" -> "关于Google Chrome"
   - 记下版本号（例如：115.0.5790.171）

2. 下载对应版本ChromeDriver：
   - 访问：https://sites.google.com/chromium.org/driver/
   - 下载与Chrome版本匹配的chromedriver_win32.zip

3. 放置驱动：
   - 解压下载的zip文件
   - 将chromedriver.exe直接放在本目录（drivers目录）下
   - 不要创建子文件夹
   - 确保文件名为"chromedriver.exe"

注意事项：
- 首次使用必须下载对应版本的ChromeDriver
- 如果更新了Chrome浏览器，需要重新下载对应版本的驱动
- 如果运行时提示版本不匹配，请重新执行上述步骤
- 请勿修改驱动文件名，必须保持为"chromedriver.exe"

常见问题：
1. 提示"未找到ChromeDriver"
   - 检查是否已将chromedriver.exe放入drivers目录
   - 确认文件名是否正确

2. 提示"版本不匹配"
   - 检查Chrome浏览器版本
   - 下载完全匹配的ChromeDriver版本
   - 替换drivers目录中的chromedriver.exe

3. 提示"无法访问ChromeDriver"
   - 确保没有其他程序正在使用ChromeDriver
   - 重启程序重试 