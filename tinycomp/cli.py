"""
Command-line interface for TinyComp
"""

import os
import argparse
from typing import Optional
from .compressor import TinyCompressor
from .api_manager import APIKeyManager

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compress images using TinyPNG API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress images')
    compress_parser.add_argument(
        "--source",
        "-s",
        required=True,
        help="Source directory or file path"
    )
    
    compress_parser.add_argument(
        "--target",
        "-t",
        required=True,
        help="Target directory or file path"
    )
    
    compress_parser.add_argument(
        "--api-key",
        "-k",
        help="TinyPNG API key (optional)"
    )
    
    compress_parser.add_argument(
        "--threads",
        "-n",
        type=int,
        default=4,
        help="Number of compression threads"
    )
    
    compress_parser.add_argument(
        "--skip-existing",
        "-x",
        action="store_true",
        default=True,
        help="Skip existing files in target directory"
    )
    
    compress_parser.add_argument(
        "--auto-update-key",
        "-a",
        action="store_true",
        help="Automatically get new API keys when current one runs out"
    )
    
    # Update API key command
    update_parser = subparsers.add_parser('update-key', help='Update TinyPNG API key')
    update_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force update even if current key is still valid"
    )
    
    return parser.parse_args()

def compress_images(args):
    """Handle image compression command."""
    print("\n开始图片压缩任务...")
    
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
    
    # 2. 如果没有有效的key且启用了auto_update_key，获取新key
    if not has_valid_key and args.auto_update_key:
        print("需要获取新的API key...")
        
        # 2.1 检查Chrome和ChromeDriver
        chrome_installed, chrome_path = api_manager._check_chrome_installation()
        if not chrome_installed:
            print("Chrome未安装，开始下载便携版Chrome...")
            chrome_path = api_manager._get_portable_chrome()
            if not chrome_path:
                print("下载Chrome失败，无法继续操作")
                return
        
        # 2.2 获取Chrome版本并检查ChromeDriver
        chrome_version = api_manager._get_chrome_version(chrome_path)
        if not chrome_version:
            print("获取Chrome版本失败，无法继续操作")
            return
        
        print(f"Chrome 版本: {chrome_version}")
        driver_installed, driver_path = api_manager._check_chromedriver_installation(chrome_version)
        if not driver_installed:
            print("ChromeDriver未安装，开始下载...")
            driver_path = api_manager._download_chromedriver(chrome_version)
            if not driver_path:
                print("下载ChromeDriver失败，无法继续操作")
                return
        
        # 2.3 获取新的API key
        print("开始获取新的API key...")
        new_key = api_manager.get_new_api_key()
        if not new_key:
            print("获取新的API key失败，无法继续操作")
            return
        
        print(f"成功获取新的API key: {new_key}")
        
        # 2.4 设置并保存新的API key
        api_manager.current_key = new_key
        current_key = new_key
        api_manager.force_save_key(current_key)
        
        # 2.5 验证key是否已保存
        saved_keys = api_manager._load_api_keys()
        if current_key not in saved_keys:
            print("API key未被正确保存，无法继续操作")
            return
        print(f"已验证API key已保存到文件: {api_manager.api_keys_file}")
        
        # 2.6 验证key是否有效
        result = api_manager._get_compression_count(current_key)
        if not result['success']:
            print("新获取的API key无效，无法继续操作")
            return
        print(f"新API key验证成功，剩余配额: {result['remaining']}")
    
    # 3. 如果没有有效的key且未启用auto_update_key，退出
    if not has_valid_key and not args.auto_update_key:
        print("没有有效的API key，请使用 --auto-update-key 参数自动获取新key")
        return
    
    # 4. 初始化压缩器并执行压缩
    compressor = TinyCompressor(
        api_key=current_key,
        max_workers=args.threads,
        auto_update_key=args.auto_update_key
    )
    
    # 检查是否是目录或文件
    if os.path.isdir(args.source):
        # 压缩目录
        print(f"\n开始压缩文件夹: {args.source}")
        print(f"输出目录: {args.target}")
        stats = compressor.compress_directory(
            args.source,
            args.target,
            skip_existing=args.skip_existing
        )
        
        # 打印结果
        print("\n压缩完成！")
        print(f"总文件数: {stats['total']}")
        print(f"成功压缩: {stats['success']}")
        print(f"失败数量: {stats['failed']}")
        print(f"成功率: {stats['percent']:.1f}%")
        if stats.get('keys_used'):
            print(f"使用的API key数量: {stats['keys_used']}")
        print(f"\n压缩后的文件保存在: {args.target}")
        
    else:
        # 压缩单个文件
        print(f"\n开始压缩文件: {args.source}")
        result = compressor.compress_image(args.source, args.target)
        
        if result['status'] == 'success':
            print("文件压缩成功！")
            print(f"压缩后的文件保存在: {args.target}")
        else:
            print(f"压缩失败: {result['message']}")

def update_api_key(args):
    """Handle API key update command."""
    api_manager = APIKeyManager()
    
    if not args.force:
        # Check if current key is still valid
        if api_manager.current_key:
            result = api_manager._get_compression_count()
            if result['success'] and result['remaining'] > 50:
                print(f"Current API key is still valid (remaining: {result['remaining']} compressions)")
                print("Use --force to update anyway")
                return
    
    print("Requesting new API key...")
    new_key = api_manager.get_new_api_key()
    
    if new_key:
        print("Successfully obtained and saved new API key")
        print(f"Remaining compressions: {api_manager._get_compression_count(new_key)['remaining']}")
    else:
        print("Failed to obtain new API key")

def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    if args.command == 'compress':
        compress_images(args)
    elif args.command == 'update-key':
        update_api_key(args)
    else:
        print("Please specify a command: compress or update-key")
        print("Use -h or --help for more information")

if __name__ == "__main__":
    main() 