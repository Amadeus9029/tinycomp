"""
Tests for the TinyCompressor class
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from ..compressor import TinyCompressor
from ..api_manager import APIKeyManager
import json
import shutil

class TestTinyCompressor(unittest.TestCase):
    """Test cases for TinyCompressor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_image = os.path.join(self.test_dir, 'test_files', 'test_image.png')
        self.test_output = os.path.join(self.test_dir, 'test_files', 'output.png')

    @patch('tinycomp.compressor.tinify.from_file')
    def test_compress_image_success(self, mock_from_file):
        """Test successful image compression."""
        # Mock the tinify.from_file() call
        mock_source = MagicMock()
        mock_from_file.return_value = mock_source
        
        # Mock successful compression
        result = self.compressor.compress_image(self.test_image, self.test_output)
        
        # 验证返回值
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message'], 'Image compressed successfully')
        
        # 验证调用
        mock_from_file.assert_called_once_with(self.test_image)
        mock_source.to_file.assert_called_once_with(self.test_output)
    
    def test_get_image_files(self):
        """Test getting supported image files from directory."""
        # Create temporary test directory with some files
        test_dir = "test_dir"
        os.makedirs(test_dir, exist_ok=True)
        
        # Create test files
        test_files = [
            "test1.png",
            "test2.jpg",
            "test3.txt",  # Unsupported extension
            "test4.jpeg"
        ]
        
        for file in test_files:
            with open(os.path.join(test_dir, file), 'w') as f:
                f.write("test")
        
        # Get image files
        image_files = self.compressor._get_image_files(test_dir)
        
        # Verify results
        self.assertEqual(len(image_files), 3)  # Should find 3 supported images
        
        # Clean up
        for file in test_files:
            os.remove(os.path.join(test_dir, file))
        os.rmdir(test_dir)
    
    def test_should_compress(self):
        """Test should_compress method."""
        # Create test directories
        source_dir = "test_source"
        target_dir = "test_target"
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)
        
        # Create test file
        test_file = os.path.join(source_dir, "test.png")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Test when target doesn't exist
        self.assertTrue(
            self.compressor._should_compress(test_file, source_dir, target_dir)
        )
        
        # Create target file
        target_file = os.path.join(target_dir, "test.png")
        with open(target_file, 'w') as f:
            f.write("test")
        
        # Test when target exists
        self.assertFalse(
            self.compressor._should_compress(test_file, source_dir, target_dir)
        )
        
        # Clean up
        os.remove(test_file)
        os.remove(target_file)
        os.rmdir(source_dir)
        os.rmdir(target_dir)

    @patch('tinycomp.api_manager.webdriver.Chrome')
    @patch('tinycomp.api_manager.ChromeDriverManager')
    def test_chrome_driver_available(self, mock_manager, mock_chrome):
        """测试 Chrome 驱动可用的情况"""
        # 模拟 ChromeDriverManager
        mock_manager.return_value.install.return_value = '/path/to/chromedriver'
        
        # 模拟 Chrome webdriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        self.compressor = TinyCompressor(auto_update_key=True)
        
        # 验证 Chrome 检查成功
        self.assertTrue(self.compressor.api_manager._check_chrome_installation())

    def test_chrome_driver_not_available(self):
        """测试 Chrome 驱动不可用的情况"""
        with patch('tinycomp.api_manager.ChromeDriverManager') as mock_manager:
            # 模拟 ChromeDriverManager 抛出异常
            mock_manager.return_value.driver_version.side_effect = Exception("Chrome not found")
            
            self.compressor = TinyCompressor(auto_update_key=True)
            
            # 验证无法获取新的 API key
            result = self.compressor.api_manager.get_new_api_key()
            self.assertIsNone(result)

    def test_chrome_installation(self):
        """测试 Chrome 安装功能"""
        api_manager = APIKeyManager()
        
        try:
            # 删除已存在的 Chrome 和 ChromeDriver（如果有）
            chrome_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tinycomp', 'chrome')
            driver_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tinycomp', 'chromedriver')
            
            if os.path.exists(chrome_dir):
                shutil.rmtree(chrome_dir)
            if os.path.exists(driver_dir):
                shutil.rmtree(driver_dir)
            
            # 测试首次安装
            chrome_installed, chrome_path = api_manager._check_chrome_installation()
            self.assertFalse(chrome_installed, "Chrome 不应该已经安装")
            
            # 测试下载安装 Chrome
            chrome_path = api_manager._get_portable_chrome()
            self.assertIsNotNone(chrome_path, "Chrome 安装失败")
            self.assertTrue(os.path.exists(chrome_path), "Chrome 可执行文件不存在")
            
            # 测试获取 Chrome 版本
            chrome_version = api_manager._get_chrome_version(chrome_path)
            self.assertIsNotNone(chrome_version, "无法获取 Chrome 版本")
            print(f"Chrome 版本: {chrome_version}")
            
            # 测试 ChromeDriver 安装
            driver_installed, driver_path = api_manager._check_chromedriver_installation(chrome_version)
            self.assertFalse(driver_installed, "ChromeDriver 不应该已经安装")
            
            # 测试下载安装 ChromeDriver
            driver_path = api_manager._download_chromedriver(chrome_version)
            self.assertIsNotNone(driver_path, "ChromeDriver 安装失败")
            self.assertTrue(os.path.exists(driver_path), "ChromeDriver 可执行文件不存在")
            
            # 测试重复检查（应该返回已安装）
            chrome_installed, chrome_path = api_manager._check_chrome_installation()
            self.assertTrue(chrome_installed, "Chrome 应该已经安装")
            
            driver_installed, driver_path = api_manager._check_chromedriver_installation(chrome_version)
            self.assertTrue(driver_installed, "ChromeDriver 应该已经安装")
            
        finally:
            # 清理测试文件
            if os.path.exists(chrome_dir):
                shutil.rmtree(chrome_dir)
            if os.path.exists(driver_dir):
                shutil.rmtree(driver_dir)

    def test_chrome_download_and_email(self):
        """测试 Chrome 下载和临时邮箱功能"""
        api_manager = APIKeyManager()
        
        try:
            # 获取临时邮箱（这会触发 Chrome 和 ChromeDriver 的安装）
            email, driver = api_manager._get_temp_email()
            
            # 验证结果
            self.assertIsNotNone(email, "获取临时邮箱失败")
            self.assertIsNotNone(driver, "Chrome 驱动初始化失败")
            self.assertTrue('@nimail.cn' in email, "邮箱格式不正确")
            
            print(f"成功获取临时邮箱: {email}")
            
        finally:
            # 关闭 driver
            if 'driver' in locals() and driver:
                driver.quit()

    def test_api_key_management(self):
        """测试 API key 管理功能"""
        api_manager = APIKeyManager()
        
        # 删除现有的 API key 文件
        if os.path.exists(api_manager.api_keys_file):
            os.remove(api_manager.api_keys_file)
        
        try:
            # 测试获取新的 API key
            new_key = api_manager.get_new_api_key()
            self.assertIsNotNone(new_key, "获取新的 API key 失败")
            self.assertTrue(len(new_key) > 20, "API key 格式不正确")
            
            # 验证 key 是否被保存
            self.assertTrue(os.path.exists(api_manager.api_keys_file), "API key 文件未创建")
            
            # 读取保存的 keys
            with open(api_manager.api_keys_file, 'r') as f:
                saved_keys = json.load(f)
            self.assertIn(new_key, saved_keys['api_keys'], "API key 未被正确保存")
            
            # 测试 key 验证
            result = api_manager._get_compression_count(new_key)
            self.assertTrue(result['success'], "API key 验证失败")
            self.assertTrue(result['remaining'] > 0, "API key 已用尽")
            
            print(f"API key 测试成功，剩余配额: {result['remaining']}")
            
        finally:
            # 清理测试文件
            if os.path.exists(api_manager.api_keys_file):
                os.remove(api_manager.api_keys_file)

    def test_compress_directory(self):
        """测试文件夹图片压缩功能"""
        # 创建测试目录
        source_dir = os.path.join(self.test_dir, 'images')
        output_dir = os.path.join(self.test_dir, 'output')
        
        # 确保测试目录存在
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建测试图片
        test_images = [
            ('test1.png', b'\x89PNG\r\n\x1a\n'),
            ('test2.jpg', b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00'),
            ('test3.jpeg', b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00'),
            ('test4.txt', b'This is not an image'),  # 非图片文件
        ]
        
        # 写入测试文件
        created_files = []
        try:
            for filename, content in test_images:
                file_path = os.path.join(source_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(content)
                created_files.append(file_path)
                
            # 创建压缩器实例
            compressor = TinyCompressor()
            
            # 执行文件夹压缩
            results = compressor.compress_directory(source_dir, output_dir)
            
            # 验证结果
            self.assertIsInstance(results, list)
            
            # 检查是否处理了所有支持的图片格式
            supported_images = [f for f in test_images if f[0].lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.assertEqual(len(results), len(supported_images))
            
            # 检查输出目录中的文件
            output_files = os.listdir(output_dir)
            self.assertEqual(len(output_files), len(supported_images))
            
            # 验证每个输出文件
            for filename, _ in supported_images:
                output_path = os.path.join(output_dir, filename)
                self.assertTrue(os.path.exists(output_path))
                self.assertTrue(os.path.getsize(output_path) > 0)
                
        finally:
            # 清理测试文件
            for file_path in created_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                
            # 清理输出目录中的文件
            for filename in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, filename))
            
            # 删除测试目录
            if os.path.exists(source_dir):
                os.rmdir(source_dir)
            if os.path.exists(output_dir):
                os.rmdir(output_dir)

    def test_compress_directory_with_subdirs(self):
        """测试带子目录的文件夹压缩功能"""
        # 创建测试目录结构
        source_dir = os.path.join(self.test_dir, 'images')
        output_dir = os.path.join(self.test_dir, 'output')
        subdir = os.path.join(source_dir, 'subdir')
        
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(subdir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建测试图片
        test_files = [
            (os.path.join(source_dir, 'test1.png'), b'\x89PNG\r\n\x1a\n'),
            (os.path.join(subdir, 'test2.jpg'), b'\xFF\xD8\xFF\xE0\x00\x10JFIF'),
        ]
        
        created_files = []
        try:
            # 创建测试文件
            for file_path, content in test_files:
                with open(file_path, 'wb') as f:
                    f.write(content)
                created_files.append(file_path)
            
            # 执行压缩
            compressor = TinyCompressor()
            results = compressor.compress_directory(source_dir, output_dir, recursive=True)
            
            # 验证结果
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), len(test_files))
            
            # 验证输出目录结构
            output_subdir = os.path.join(output_dir, 'subdir')
            self.assertTrue(os.path.exists(output_subdir))
            
            # 验证所有文件都被正确压缩
            for source_path, _ in test_files:
                rel_path = os.path.relpath(source_path, source_dir)
                output_path = os.path.join(output_dir, rel_path)
                self.assertTrue(os.path.exists(output_path))
                self.assertTrue(os.path.getsize(output_path) > 0)
                
        finally:
            # 清理测试文件和目录
            for file_path in created_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # 递归删除所有创建的目录
            if os.path.exists(source_dir):
                shutil.rmtree(source_dir)
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

    def test_compress_directory_with_auto_key(self):
        """测试文件夹图片压缩功能（包含自动获取API key）"""
        # 创建测试目录
        source_dir = os.path.join(self.test_dir, 'images')
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')  # 移到项目根目录
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        print(f"\n输出目录已创建: {output_dir}")
        
        try:
            print("\n开始测试自动获取 API key 和图片压缩...")
            
            # 初始化API管理器
            api_manager = APIKeyManager()
            
            # 1. 检查是否有可用的API key
            current_key = api_manager.current_key
            if current_key:
                print(f"找到已存在的API key: {current_key}")
                result = api_manager._get_compression_count(current_key)
                if result['success'] and result['remaining'] > 0:
                    print(f"当前API key有效，剩余配额: {result['remaining']}")
                    has_valid_key = True
                else:
                    print("当前API key已失效或配额不足")
                    has_valid_key = False
            else:
                print("未找到API key")
                has_valid_key = False
            
            # 2. 如果没有有效的key，需要获取新key
            if not has_valid_key:
                print("需要获取新的API key...")
                
                # 2.1 检查Chrome和ChromeDriver
                chrome_installed, chrome_path = api_manager._check_chrome_installation()
                if not chrome_installed:
                    print("Chrome未安装，开始下载便携版Chrome...")
                    chrome_path = api_manager._get_portable_chrome()
                    self.assertIsNotNone(chrome_path, "下载Chrome失败")
                
                # 2.2 获取Chrome版本并检查ChromeDriver
                chrome_version = api_manager._get_chrome_version(chrome_path)
                self.assertIsNotNone(chrome_version, "获取Chrome版本失败")
                
                driver_installed, driver_path = api_manager._check_chromedriver_installation(chrome_version)
                if not driver_installed:
                    print("ChromeDriver未安装，开始下载...")
                    driver_path = api_manager._download_chromedriver(chrome_version)
                    self.assertIsNotNone(driver_path, "下载ChromeDriver失败")
                
                # 2.3 获取新的API key
                print("开始获取新的API key...")
                new_key = api_manager.get_new_api_key()
                self.assertIsNotNone(new_key, "获取新的API key失败")
                print(f"成功获取新的API key: {new_key}")
                
                # 2.4 设置并保存新的API key
                api_manager.current_key = new_key
                current_key = new_key
                api_manager.force_save_key(current_key)  # 强制保存key
                
                # 2.5 验证key是否已保存
                saved_keys = api_manager._load_api_keys()
                self.assertIn(current_key, saved_keys, "API key未被正确保存")
                print(f"已验证API key已保存到文件: {api_manager.api_keys_file}")
                
                # 2.6 验证key是否有效
                result = api_manager._get_compression_count(current_key)
                self.assertTrue(result['success'], "新获取的API key无效")
                print(f"新API key验证成功，剩余配额: {result['remaining']}")
            
            # 3. 使用API key进行压缩测试
            compressor = TinyCompressor(api_key=current_key)
            
            # 执行文件夹压缩
            print(f"\n开始压缩文件夹: {source_dir}")
            print(f"输出目录: {output_dir}")
            results = compressor.compress_directory(source_dir, output_dir)
            
            # 验证输出目录是否存在
            self.assertTrue(os.path.exists(output_dir), "输出目录不存在")
            output_files = os.listdir(output_dir)
            print(f"\n输出目录中的文件: {output_files}")
            
            # 验证结果
            self.assertIsInstance(results, dict, "压缩结果应该是字典类型")
            self.assertIn('total', results, "结果中应包含 'total' 字段")
            self.assertIn('processed', results, "结果中应包含 'processed' 字段")
            self.assertIn('success', results, "结果中应包含 'success' 字段")
            self.assertIn('failed', results, "结果中应包含 'failed' 字段")
            self.assertIn('percent', results, "结果中应包含 'percent' 字段")
            
            # 验证压缩是否成功
            self.assertEqual(results['success'], results['processed'], 
                            "所有处理的文件都应该压缩成功")
            self.assertEqual(results['failed'], 0, 
                            "不应该有失败的文件")
            self.assertEqual(results['percent'], 100.0, 
                            "压缩完成率应为100%")
            
            print("\n压缩测试完成！")
            print(f"处理结果: 总计{results['total']}个文件，"
                  f"成功{results['success']}个，"
                  f"失败{results['failed']}个，"
                  f"完成率{results['percent']}%")
            print(f"\n压缩后的文件保存在: {output_dir}")
            
        except Exception as e:
            print(f"\n测试过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def test_compress_directory_with_existing_key(self):
        """测试使用已存在的API key进行文件夹压缩"""
        # 创建测试目录
        source_dir = os.path.join(self.test_dir, 'images')
        output_dir = os.path.join(self.test_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用现有的API key文件
        api_keys_file = "tinypng_api_keys.json"
        
        try:
            # 创建压缩器实例
            compressor = TinyCompressor(auto_update_key=False)  # 不自动更新key
            
            # 执行文件夹压缩
            print(f"使用现有API key压缩文件夹: {source_dir}")
            results = compressor.compress_directory(source_dir, output_dir)
            
            # 验证结果
            self.assertIsInstance(results, list)
            self.assertTrue(len(results) > 0, "没有找到可压缩的图片")
            
            # 验证所有文件都被成功压缩
            for result in results:
                self.assertEqual(result['status'], 'success', 
                               f"使用现有key压缩失败: {result.get('message', '')}")
                
        finally:
            # 清理输出目录
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

if __name__ == '__main__':
    unittest.main() 