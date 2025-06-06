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
    # Initialize compressor
    compressor = TinyCompressor(
        api_key=args.api_key,
        max_workers=args.threads,
        auto_update_key=args.auto_update_key
    )
    
    # Check if source is a directory or file
    if os.path.isdir(args.source):
        # Compress directory
        print(f"Compressing directory: {args.source}")
        stats = compressor.compress_directory(
            args.source,
            args.target,
            skip_existing=args.skip_existing
        )
        
        # Print results
        print("\nCompression completed!")
        print(f"Total files: {stats['total']}")
        print(f"Successfully compressed: {stats['success']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success rate: {stats['percent']:.1f}%")
        if stats.get('keys_used'):
            print(f"API keys used: {stats['keys_used']}")
        
    else:
        # Compress single file
        print(f"Compressing file: {args.source}")
        result = compressor.compress_image(args.source, args.target)
        
        if result['status'] == 'success':
            print("File compressed successfully!")
        else:
            print(f"Compression failed: {result['message']}")

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