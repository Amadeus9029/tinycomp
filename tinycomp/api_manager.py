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

class APIKeyManager:
    """Manages TinyPNG API keys, including loading, saving, and validation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API key manager.
        
        Args:
            api_key (str, optional): Initial API key to use. If not provided,
                                   will try to get from environment or saved keys.
        """
        self.api_keys_file = "tinypng_api_keys.json"
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
        
        # 添加对不同操作系统的支持
        import platform
        system = platform.system().lower()
        
        if system != 'windows':
            # Linux 和 MacOS 可能需要这些额外选项
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

    def _get_temp_email(self) -> Tuple[Optional[str], Optional[webdriver.Chrome]]:
        """Get temporary email address from temporary email service."""
        print("Getting temporary email...")
        
        chrome_options = self._configure_chrome_options()
        
        try:
            # 直接使用 ChromeDriverManager，不需要指定 ChromeType
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.get("https://www.nimail.cn/index.html")
            
            random_email_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '随机邮箱')]"))
            )
            random_email_btn.click()
            
            time.sleep(2)
            
            email_username_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="mailuser"]'))
            )
            email_username = email_username_element.get_attribute("value")
            email = f"{email_username}@nimail.cn"
            
            apply_email_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '申请邮箱')]"))
            )
            apply_email_btn.click()
            
            time.sleep(3)
            print(f"Temporary email activated: {email}")
            
            return email, driver
        except Exception as e:
            print(f"Failed to get temporary email: {str(e)}")
            if 'driver' in locals() and driver:
                driver.quit()
            return None, None

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

    def _check_chrome_installation(self) -> bool:
        """检查 Chrome 浏览器是否已安装并可用"""
        try:
            # 直接使用 ChromeDriverManager，不需要 ChromeType
            ChromeDriverManager().driver_version()
            return True
        except Exception as e:
            print("\n警告: Chrome 浏览器配置检查失败")
            print("自动更新 API key 功能需要 Chrome 浏览器。")
            print("请确保：")
            print("1. 已安装 Chrome 浏览器")
            print("2. Chrome 浏览器版本正常")
            print(f"错误详情: {str(e)}\n")
            return False

    def get_new_api_key(self) -> Optional[str]:
        """Get new API key and save it."""
        # 在实际需要使用 Chrome 时才检查
        if not self._check_chrome_installation():
            print("无法自动获取新的 API key，请手动设置 API key 或修复 Chrome 配置。")
            return None
            
        email, driver = self._get_temp_email()
        if not email or not driver:
            return None
        
        try:
            new_key = self._request_new_api_key(email, driver)
            if new_key:
                # Add new key to saved keys
                api_keys = self._load_api_keys()
                if new_key not in api_keys:
                    api_keys.append(new_key)
                    self._save_api_keys(api_keys)
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