"""
API key management for TinyPNG
"""

import os
import json
import time
import random
import string
from typing import List, Dict, Optional, Tuple
import tinify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager
import platform
import requests
import zipfile
import shutil
import subprocess

class APIKeyManager:
    """Manages TinyPNG API keys, including loading, saving, and validation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API key manager.
        
        Args:
            api_key (str, optional): Initial API key to use. If not provided,
                                   will try to get from environment or saved keys.
        """
        self.api_keys_file = os.path.join(os.path.expanduser('~'), '.tinycomp', 'tinypng_api_keys.json')
        os.makedirs(os.path.dirname(self.api_keys_file), exist_ok=True)
        self.current_key = api_key or os.getenv("TINYCOMP_API_KEY")
        
        if not self.current_key:
            self.current_key = self._get_valid_api_key()
    
    def _load_api_keys(self) -> List[str]:
        """Load saved API keys from file."""
        if os.path.exists(self.api_keys_file):
            try:
                with open(self.api_keys_file, 'r') as f:
                    data = json.load(f)
                    return data.get("api_keys", [])
            except Exception as e:
                print(f"Error loading API keys file: {str(e)}")
        return []
    
    def _save_api_keys(self, api_keys: List[str]) -> None:
        """Save API keys to file."""
        try:
            data = {"api_keys": api_keys}
            with open(self.api_keys_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving API keys to file: {str(e)}")
    
    def _get_compression_count(self, api_key: Optional[str] = None) -> Dict[str, any]:
        """
        Get the compression count for an API key.
        
        Args:
            api_key (str, optional): API key to check. If None, uses current key.
            
        Returns:
            dict: Contains compression count information and status.
        """
        result = {
            'compression_count': 0,
            'remaining': 500,
            'success': False,
            'error': None
        }
        
        # If provided new API key, temporarily set it
        old_key = None
        if api_key:
            old_key = tinify.key
            tinify.key = api_key
        
        try:
            # Create a tiny PNG image for validation
            tiny_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            
            # Send request to activate compression_count
            source = tinify.from_buffer(tiny_png)
            
            # Get compression count
            compression_count = getattr(tinify, 'compression_count', 0)
            if compression_count is None:
                compression_count = 0
                
            # Calculate remaining
            remaining = 500 - compression_count
            
            result.update({
                'compression_count': compression_count,
                'remaining': remaining,
                'success': True
            })
            
        except tinify.Error as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = f"Unknown error: {str(e)}"
        
        # Restore original API key
        if old_key:
            tinify.key = old_key
            
        return result
    
    def _get_valid_api_key(self) -> Optional[str]:
        """Get a valid API key from saved keys or environment."""
        # Load saved API keys
        api_keys = self._load_api_keys()
        
        # Check each saved key
        for key in api_keys:
            tinify.key = key
            try:
                result = self._get_compression_count(key)
                if result['success'] and result['remaining'] > 0:
                    return key
            except:
                continue
        
        return None

    def _generate_random_name(self) -> str:
        """Generate random name for registration."""
        first_names = ['Zhang', 'Li', 'Wang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhao', 'Wu', 'Zhou']
        last_names = ['Wei', 'Min', 'Jie', 'Fang', 'Ying', 'Hai', 'Jun', 'Xin', 'Feng', 'Yu']
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _configure_chrome_options(self) -> Options:
        """Configure Chrome options with random fingerprint."""
        chrome_options = Options()
        
        # 添加便携版Chrome的支持
        chrome_options.binary_location = self._get_portable_chrome()
        
        if platform.system().lower() != 'windows':
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        chrome_options.add_argument('--headless')
        
        try:
            ua = UserAgent().chrome
        except:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        chrome_options.add_argument(f'--user-agent={ua}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        return chrome_options

    def _check_and_install_dependencies(self) -> bool:
        """检查并安装必要的依赖"""
        try:
            # 检查是否已安装 requests
            import requests
        except ImportError:
            print("正在安装必要的依赖包...")
            try:
                import pip
                pip.main(['install', 'requests'])
            except Exception as e:
                print(f"安装依赖包失败: {str(e)}")
                return False

        chrome_dir = os.path.join(os.path.dirname(__file__), 'chrome')
        chrome_exe = os.path.join(chrome_dir, 'chrome.exe') if platform.system().lower() == 'windows' else os.path.join(chrome_dir, 'chrome')

        if not os.path.exists(chrome_exe):
            print("首次运行需要下载 Chrome 浏览器...")
            if not self._get_portable_chrome():
                print("下载 Chrome 失败，无法继续操作")
                return False

        return True

    def _get_portable_chrome(self) -> Optional[str]:
        """获取或下载便携版Chrome"""
        # 修改存储路径到用户主目录
        chrome_dir = os.path.join(os.path.expanduser('~'), '.tinycomp', 'chrome')
        os.makedirs(chrome_dir, exist_ok=True)
        
        # 检查是否已存在便携版Chrome
        system = platform.system().lower()
        if system == 'windows':
            chrome_path = os.path.join(chrome_dir, 'chrome-win64', 'chrome.exe')
        elif system == 'darwin':
            if platform.machine().lower() == 'arm64':
                chrome_path = os.path.join(chrome_dir, 'chrome-mac-arm64', 
                    'Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing')
            else:
                chrome_path = os.path.join(chrome_dir, 'chrome-mac-x64',
                    'Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing')
        else:
            chrome_path = os.path.join(chrome_dir, 'chrome-linux64', 'chrome')
        
        if os.path.exists(chrome_path):
            print(f"使用已存在的 Chrome: {chrome_path}")
            return chrome_path
        
        try:
            # 获取最新版本信息
            version_url = "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE"
            response = requests.get(version_url)
            latest_version = response.text.strip()
            
            # 构建下载URL
            if system == 'windows':
                platform_name = 'win64'
                chrome_relative_path = 'chrome-win64/chrome.exe'
            elif system == 'darwin':
                if platform.machine().lower() == 'arm64':
                    platform_name = 'mac-arm64'
                    chrome_relative_path = 'chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
                else:
                    platform_name = 'mac-x64'
                    chrome_relative_path = 'chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
            else:
                platform_name = 'linux64'
                chrome_relative_path = 'chrome-linux64/chrome'
            
            download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{latest_version}/{platform_name}/chrome-{platform_name}.zip"
            
            print(f"正在下载 Chrome {latest_version}...")
            print(f"下载地址: {download_url}")
            
            # 下载到临时文件
            temp_dir = os.path.join(chrome_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            zip_path = os.path.join(temp_dir, 'chrome.zip')
            
            response = requests.get(download_url, stream=True)
            if response.status_code != 200:
                raise Exception(f"下载失败，状态码: {response.status_code}")
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            
            with open(zip_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    f.write(data)
            
            print("\n下载完成，正在解压...")
            
            # 解压到临时目录
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(chrome_dir)
            
            # 清理临时文件
            os.remove(zip_path)
            os.rmdir(temp_dir)
            
            print("Chrome 安装完成")
            return chrome_path
            
        except Exception as e:
            print(f"下载并安装 Chrome 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _check_chrome_installation(self) -> Tuple[bool, Optional[str]]:
        """检查 Chrome 是否已安装
        Returns:
            Tuple[bool, Optional[str]]: (是否已安装, Chrome路径)
        """
        chrome_dir = os.path.join(os.path.dirname(__file__), 'chrome')
        if platform.system().lower() == 'windows':
            chrome_path = os.path.join(chrome_dir, 'chrome-win64', 'chrome.exe')
        elif platform.system().lower() == 'darwin':
            if platform.machine().lower() == 'arm64':
                chrome_path = os.path.join(chrome_dir, 'chrome-mac-arm64', 
                    'Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing')
            else:
                chrome_path = os.path.join(chrome_dir, 'chrome-mac-x64',
                    'Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing')
        else:
            chrome_path = os.path.join(chrome_dir, 'chrome-linux64', 'chrome')
        
        return os.path.exists(chrome_path), chrome_path

    def _check_chromedriver_installation(self, chrome_version: str) -> Tuple[bool, Optional[str]]:
        """检查 ChromeDriver 是否已安装
        Returns:
            Tuple[bool, Optional[str]]: (是否已安装, ChromeDriver路径)
        """
        driver_dir = os.path.join(os.path.dirname(__file__), 'chromedriver')
        system = platform.system().lower()
        
        if system == 'windows':
            driver_path = os.path.join(driver_dir, 'chromedriver-win64', 'chromedriver.exe')
        elif system == 'darwin':
            if platform.machine().lower() == 'arm64':
                driver_path = os.path.join(driver_dir, 'chromedriver-mac-arm64', 'chromedriver')
            else:
                driver_path = os.path.join(driver_dir, 'chromedriver-mac-x64', 'chromedriver')
        else:
            driver_path = os.path.join(driver_dir, 'chromedriver-linux64', 'chromedriver')
        
        exists = os.path.exists(driver_path)
        if exists:
            print(f"找到已安装的 ChromeDriver: {driver_path}")
        return exists, driver_path

    def _get_temp_email(self) -> Tuple[Optional[str], Optional[webdriver.Chrome]]:
        """Get temporary email address from temporary email service."""
        print("正在获取临时邮箱...")
        
        # 检查 Chrome 安装
        chrome_installed, chrome_path = self._check_chrome_installation()
        if not chrome_installed:
            print("Chrome 未安装，开始下载...")
            chrome_path = self._get_portable_chrome()
            if not chrome_path:
                print("Chrome 安装失败")
                return None, None
        
        # 获取 Chrome 版本
        chrome_version = self._get_chrome_version(chrome_path)
        
        # 检查 ChromeDriver 安装
        driver_installed, driver_path = self._check_chromedriver_installation(chrome_version)
        if not driver_installed:
            print("ChromeDriver 未安装，开始下载...")
            driver_path = self._download_chromedriver(chrome_version)
            if not driver_path:
                print("ChromeDriver 安装失败")
                return None, None
        
        try:
            # 配置 Chrome 选项
            chrome_options = Options()
            chrome_options.binary_location = chrome_path
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # 创建 Chrome 实例
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_window_size(1920, 1080)
            
            driver.get("https://www.nimail.cn/index.html")
            
            # 增加等待时间和重试机制
            max_retries = 3
            for retry in range(max_retries):
                try:
                    random_email_btn = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.btn-lg"))
                    )
                    random_email_btn.click()
                    break
                except Exception as e:
                    if retry == max_retries - 1:
                        print(f"无法点击随机邮箱按钮: {str(e)}")
                        driver.quit()
                        return None, None
                    print(f"重试点击随机邮箱按钮 ({retry + 1}/{max_retries})")
                    time.sleep(2)
            
            time.sleep(2)
            
            email_username_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "mailuser"))
            )
            email_username = email_username_element.get_attribute("value")
            email = f"{email_username}@nimail.cn"
            
            apply_email_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-success"))
            )
            apply_email_btn.click()
            
            time.sleep(3)
            print(f"临时邮箱已激活: {email}")
            
            return email, driver
        except Exception as e:
            print(f"获取临时邮箱失败: {str(e)}")
            if 'driver' in locals() and driver:
                driver.quit()
            return None, None

    def _get_chrome_version(self, chrome_path: str) -> str:
        """获取 Chrome 版本号"""
        try:
            if platform.system().lower() == 'windows':
                # 使用 PowerShell 获取文件版本信息
                chrome_path_escaped = chrome_path.replace('\\', '\\\\')
                cmd = f'powershell -command "(Get-Item \'{chrome_path_escaped}\').VersionInfo.FileVersion"'
                try:
                    output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
                    version = output.split('.')[0]  # 只取主版本号
                except:
                    # 如果 PowerShell 命令失败，尝试直接使用一个稳定版本
                    print("无法获取 Chrome 版本，将使用默认版本")
                    version = "114"
            else:
                # Linux 和 Mac 使用命令行参数
                cmd = f'"{chrome_path}" --version'
                try:
                    output = subprocess.check_output(cmd, shell=True).decode()
                    version = output.strip().split(' ')[2].split('.')[0]
                except:
                    print("无法获取 Chrome 版本，将使用默认版本")
                    version = "114"
            
            print(f"Chrome 版本: {version}")
            return version
            
        except Exception as e:
            print(f"获取 Chrome 版本失败: {str(e)}")
            print("将使用默认版本")
            return "114"  # 返回一个稳定的默认版本

    def _download_chromedriver(self, chrome_version: str) -> Optional[str]:
        """下载对应版本的 ChromeDriver"""
        driver_dir = os.path.join(os.path.expanduser('~'), '.tinycomp', 'chromedriver')
        os.makedirs(driver_dir, exist_ok=True)
        
        # 检查是否已存在对应版本的 ChromeDriver
        system = platform.system().lower()
        if system == 'windows':
            driver_path = os.path.join(driver_dir, 'chromedriver-win64', 'chromedriver.exe')
        elif system == 'darwin':
            if platform.machine().lower() == 'arm64':
                driver_path = os.path.join(driver_dir, 'chromedriver-mac-arm64', 'chromedriver')
            else:
                driver_path = os.path.join(driver_dir, 'chromedriver-mac-x64', 'chromedriver')
        else:
            driver_path = os.path.join(driver_dir, 'chromedriver-linux64', 'chromedriver')
        
        if os.path.exists(driver_path):
            print(f"使用已存在的 ChromeDriver: {driver_path}")
            return driver_path
        
        try:
            # 使用 Chrome 版本获取对应的 ChromeDriver
            if system == 'windows':
                platform_name = 'win64'
            elif system == 'darwin':
                platform_name = 'mac-arm64' if platform.machine().lower() == 'arm64' else 'mac-x64'
            else:
                platform_name = 'linux64'
            
            download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/chromedriver-{platform_name}.zip"
            
            print(f"正在下载 ChromeDriver {chrome_version}...")
            print(f"下载地址: {download_url}")
            
            # 下载到临时文件
            temp_dir = os.path.join(driver_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            zip_path = os.path.join(temp_dir, 'chromedriver.zip')
            
            response = requests.get(download_url)
            if response.status_code != 200:
                raise Exception(f"下载失败，状态码: {response.status_code}")
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            print("下载完成，正在解压...")
            
            # 解压到临时目录
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(driver_dir)
            
            # 清理临时文件
            os.remove(zip_path)
            os.rmdir(temp_dir)
            
            # 如果是 Linux 或 Mac，添加执行权限
            if system != 'windows':
                os.chmod(driver_path, 0o755)
            
            print("ChromeDriver 安装完成")
            return driver_path
            
        except Exception as e:
            print(f"下载 ChromeDriver 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _request_new_api_key(self, email: str, driver: webdriver.Chrome) -> Optional[str]:
        """Request new TinyPNG API key using temporary email."""
        print(f"Requesting new TinyPNG API key using email: {email}")
        
        try:
            original_window = driver.current_window_handle
            driver.execute_script("window.open('https://tinify.com/developers', '_blank');")
            time.sleep(2)
            driver.switch_to.window(driver.window_handles[-1])
            
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "name"))
            )
            
            name_input = driver.find_element(By.NAME, "name")
            name_input.send_keys(self._generate_random_name())
            
            email_input = driver.find_element(By.NAME, "email")
            email_input.send_keys(email)
            
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            driver.switch_to.window(original_window)
            
            max_attempts = 15
            for attempt in range(max_attempts):
                print(f"Waiting for confirmation email... ({attempt+1}/{max_attempts})")
                time.sleep(10)
                
                try:
                    tinypng_email = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="inbox"]/tr[2]'))
                    )
                    tinypng_email.click()
                    time.sleep(3)
                    
                    new_window = driver.window_handles[-1]
                    driver.switch_to.window(new_window)
                    
                    dashboard_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Visit your dashboard') or contains(@href, 'dashboard')]"))
                    )
                    dashboard_url = dashboard_link.get_attribute("href")
                    driver.execute_script(f"window.open('{dashboard_url}', '_blank');")
                    time.sleep(3)
                    
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(5)
                    
                    api_key_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/section/div/div/section/div[2]/div[1]/div/div[3]/strong/p"))
                    )
                    key_text = api_key_element.text.strip()
                    
                    if key_text and len(key_text) > 20:
                        print(f"Successfully obtained new API key")
                        return key_text
                    
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {str(e)}")
                    continue
            
            print("Timeout waiting for API key")
            return None
            
        except Exception as e:
            print(f"Failed to request new API key: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()

    def get_new_api_key(self) -> Optional[str]:
        """Get new API key and save it."""
        # 首次使用时才检查和安装依赖
        if not self._check_and_install_dependencies():
            print("无法自动获取新的 API key，请手动设置 API key 或检查环境配置。")
            return None
            
        email, driver = self._get_temp_email()
        if not email or not driver:
            return None
        
        try:
            new_key = self._request_new_api_key(email, driver)
            if new_key:
                # 设置为当前 key
                self.current_key = new_key
                # 保存 key
                api_keys = self._load_api_keys()
                if new_key not in api_keys:
                    api_keys.append(new_key)
                    self._save_api_keys(api_keys)
                    print(f"新的 API key 已保存到: {self.api_keys_file}")
                return new_key
            return None
        finally:
            if driver:
                driver.quit()
    
    def check_and_update_api_key(self) -> bool:
        """
        Check current API key and update if necessary.
        
        Returns:
            bool: True if a valid API key is available, False otherwise.
        """
        if not self.current_key:
            self.current_key = self._get_valid_api_key()
            if not self.current_key:
                return False
        
        tinify.key = self.current_key
        
        # Get API key usage
        result = self._get_compression_count()
        
        if result['success']:
            if result['remaining'] <= 50:  # If less than 50 compressions remaining
                # Try to get a new key
                new_key = self._get_valid_api_key()
                if new_key:
                    self.current_key = new_key
                    tinify.key = new_key
            return True
        else:
            # Current key is invalid, try to get a new one
            new_key = self._get_valid_api_key()
            if new_key:
                self.current_key = new_key
                tinify.key = new_key
                return True
            return False

    def force_save_key(self, api_key: str) -> None:
        """强制保存API key到文件"""
        try:
            api_keys = self._load_api_keys()
            if api_key not in api_keys:
                api_keys.append(api_key)
                self._save_api_keys(api_keys)
                print(f"API key已保存到文件: {self.api_keys_file}")
        except Exception as e:
            print(f"保存API key时出错: {str(e)}") 