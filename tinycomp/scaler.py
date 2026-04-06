"""
Image scaler using Pillow (PIL) for local batch scaling
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Union
from PIL import Image
from tqdm import tqdm


class TinyScaler:
    """
    A class for scaling images locally using Pillow.
    """

    SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

    def __init__(self, max_workers: int = 4):
        """
        Initialize the TinyScaler.

        Args:
            max_workers (int): Maximum number of concurrent scaling threads.
        """
        self.max_workers = max_workers

    def scale_image(self, source_path: str, target_path: str,
                    width: Optional[int] = None,
                    height: Optional[int] = None,
                    scale: Optional[float] = None) -> Dict[str, str]:
        """
        Scale a single image using Pillow.

        Args:
            source_path (str): Path to the source image.
            target_path (str): Path where the scaled image will be saved.
            width (int, optional): Target width in pixels. Provide width OR height OR scale, not combined.
            height (int, optional): Target height in pixels. Provide width OR height OR scale, not combined.
            scale (float, optional): Scale ratio (e.g. 0.5 = half, 2 = double). Provide width OR height OR scale, not combined.

        Returns:
            dict: Scaling result containing status and message.
        """
        try:
            with Image.open(source_path) as img:
                orig_w, orig_h = img.size

                if scale is not None:
                    new_w = int(orig_w * scale)
                    new_h = int(orig_h * scale)
                elif width is not None:
                    new_w = width
                    new_h = int(orig_h * (width / orig_w))
                elif height is not None:
                    new_h = height
                    new_w = int(orig_w * (height / orig_h))
                else:
                    return {'status': 'failed', 'message': 'Must specify width, height, or scale'}

                scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                scaled.save(target_path)

            return {'status': 'success', 'message': 'Image scaled successfully'}
        except Exception as e:
            return {'status': 'failed', 'message': f'Scaling failed: {str(e)}'}

    def scale_directory(self, source_dir: str, target_dir: str,
                        width: Optional[int] = None,
                        height: Optional[int] = None,
                        scale: Optional[float] = None,
                        skip_existing: bool = True) -> Dict[str, Union[int, float]]:
        """
        Scale all supported images in a directory.

        Args:
            source_dir (str): Source directory containing images.
            target_dir (str): Target directory for scaled images.
            width (int, optional): Target width in pixels.
            height (int, optional): Target height in pixels.
            scale (float, optional): Scale ratio (e.g. 0.5 = half, 2 = double).
            skip_existing (bool): Whether to skip files that already exist.

        Returns:
            dict: Scaling statistics.
        """
        image_files = self._get_image_files(source_dir)

        if skip_existing:
            image_files = [f for f in image_files if self._should_process(f, source_dir, target_dir)]

        total_files = len(image_files)
        if total_files == 0:
            return {
                'total': 0, 'processed': 0, 'success': 0, 'failed': 0,
                'percent': 100.0
            }

        stats = {'total': total_files, 'processed': 0, 'success': 0, 'failed': 0}

        def _scale_file(fp):
            rel = os.path.relpath(fp, source_dir)
            tgt = os.path.join(target_dir, rel)
            return self.scale_image(fp, tgt, width=width, height=height, scale=scale)

        with tqdm(total=total_files, unit="file", desc="Scaling images") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                fut_to_file = {executor.submit(_scale_file, f): f for f in image_files}
                for future in as_completed(fut_to_file):
                    result = future.result()
                    stats['processed'] += 1
                    if result['status'] == 'success':
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                        print(f"\nFailed to scale {fut_to_file[future]}: {result['message']}")
                    pbar.update(1)

        stats['percent'] = (stats['success'] / stats['total']) * 100
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

    def _should_process(self, file_path: str, source_dir: str, target_dir: str) -> bool:
        """Check if the file should be processed (skip if target exists)."""
        relative_path = os.path.relpath(file_path, source_dir)
        target_path = os.path.join(target_dir, relative_path)
        return not os.path.exists(target_path)
