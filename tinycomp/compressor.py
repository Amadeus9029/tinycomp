"""
TinyCompressor class for handling image compression using TinyPNG API
"""

import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Union
from tqdm import tqdm
import tinify
from .api_manager import APIKeyManager

class TinyCompressor:
    """
    A class for compressing images using the TinyPNG API.
    """
    
    SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.svg', '.gif']
    
    def __init__(self, api_key: Optional[str] = None, max_workers: int = 4, auto_update_key: bool = False):
        """
        Initialize the TinyCompressor.
        
        Args:
            api_key (str, optional): TinyPNG API key. If not provided, will try to get from environment
                                   or manage automatically.
            max_workers (int): Maximum number of concurrent compression threads.
            auto_update_key (bool): Whether to automatically get new API keys when current one runs out.
        """
        self.max_workers = max_workers
        self.auto_update_key = auto_update_key
        self.api_manager = APIKeyManager(api_key)
        self.keys_used = set()  # Track used API keys
        
    def compress_image(self, source_path: str, target_path: str) -> Dict[str, str]:
        """
        Compress a single image.
        
        Args:
            source_path (str): Path to the source image.
            target_path (str): Path where the compressed image will be saved.
            
        Returns:
            dict: Compression result containing status and message.
        """
        # Ensure the API key is valid
        if not self.api_manager.check_and_update_api_key():
            if self.auto_update_key:
                print("Current API key is invalid or depleted, requesting new key...")
                new_key = self.api_manager.get_new_api_key()
                if not new_key:
                    return {
                        'status': 'failed',
                        'message': 'Failed to obtain new API key'
                    }
                self.api_manager.current_key = new_key
                tinify.key = new_key
            else:
                return {
                    'status': 'failed',
                    'message': 'No valid API key available. Use --auto-update-key to automatically get new keys.'
                }
        
        # Add current key to used keys set
        if self.api_manager.current_key:
            self.keys_used.add(self.api_manager.current_key)
        
        # Create target directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        try:
            # Compress the image
            source = tinify.from_file(source_path)
            source.to_file(target_path)
            
            return {
                'status': 'success',
                'message': 'Image compressed successfully'
            }
        except tinify.AccountError as e:
            if self.auto_update_key:
                print("API key limit reached, requesting new key...")
                new_key = self.api_manager.get_new_api_key()
                if new_key:
                    self.api_manager.current_key = new_key
                    tinify.key = new_key
                    # Retry compression with new key
                    return self.compress_image(source_path, target_path)
            return {
                'status': 'failed',
                'message': f'API key error: {str(e)}. Use --auto-update-key to automatically get new keys.'
            }
        except tinify.Error as e:
            return {
                'status': 'failed',
                'message': f'Compression failed: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Processing error: {str(e)}'
            }
    
    def compress_directory(self, source_dir: str, target_dir: str, 
                         skip_existing: bool = True) -> Dict[str, Union[int, float]]:
        """
        Compress all supported images in a directory.
        
        Args:
            source_dir (str): Source directory containing images to compress.
            target_dir (str): Target directory for compressed images.
            skip_existing (bool): Whether to skip files that already exist in target directory.
            
        Returns:
            dict: Compression statistics.
        """
        # Get list of files to process
        image_files = self._get_image_files(source_dir)
        
        if skip_existing:
            image_files = [f for f in image_files if self._should_compress(f, source_dir, target_dir)]
        
        total_files = len(image_files)
        if total_files == 0:
            return {
                'total': 0,
                'processed': 0,
                'success': 0,
                'failed': 0,
                'percent': 100.0,
                'keys_used': 0
            }
        
        stats = {
            'total': total_files,
            'processed': 0,
            'success': 0,
            'failed': 0
        }
        
        # Process files with progress bar
        with tqdm(total=total_files, unit="file", desc="Compressing images") as progress_bar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(
                        self._process_single_file, 
                        file_path, 
                        source_dir, 
                        target_dir
                    ): file_path for file_path in image_files
                }
                
                for future in as_completed(future_to_file):
                    result = future.result()
                    stats['processed'] += 1
                    
                    if result['status'] == 'success':
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                        print(f"\nFailed to compress {future_to_file[future]}: {result['message']}")
                        
                    progress_bar.update(1)
        
        stats['percent'] = (stats['success'] / stats['total']) * 100
        stats['keys_used'] = len(self.keys_used)
        return stats
    
    def _get_image_files(self, directory: str) -> List[str]:
        """Get all supported image files in the directory."""
        image_files = []
        
        for root, _, files in os.walk(directory):
            for name in files:
                file_path = os.path.join(root, name)
                _, file_ext = os.path.splitext(name)
                
                if file_ext.lower() in self.SUPPORTED_EXTENSIONS:
                    image_files.append(file_path)
        
        return image_files
    
    def _should_compress(self, file_path: str, source_dir: str, target_dir: str) -> bool:
        """Check if the file should be compressed (skip if target exists)."""
        relative_path = os.path.relpath(file_path, source_dir)
        target_path = os.path.join(target_dir, relative_path)
        return not os.path.exists(target_path)
    
    def _process_single_file(self, file_path: str, source_dir: str, target_dir: str) -> Dict[str, str]:
        """Process a single file for compression."""
        relative_path = os.path.relpath(file_path, source_dir)
        target_path = os.path.join(target_dir, relative_path)
        
        return self.compress_image(file_path, target_path) 