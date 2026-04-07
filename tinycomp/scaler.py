"""
Image scaler using Pillow (PIL) for local batch scaling
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Union, Tuple
from PIL import Image
from tqdm import tqdm


class TinyScaler:
    """
    A class for scaling images locally using Pillow.
    """

    SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

    RESAMPLE_MODES = {
        'NEAREST':    Image.Resampling.NEAREST,
        'BILINEAR':   Image.Resampling.BILINEAR,
        'BICUBIC':    Image.Resampling.BICUBIC,
        'LANCZOS':    Image.Resampling.LANCZOS,
        'BOX':        Image.Resampling.BOX,
        'HAMMING':    Image.Resampling.HAMMING,
    }

    def __init__(self, max_workers: int = 4, method: str = 'LANCZOS'):
        """
        Initialize the TinyScaler.

        Args:
            max_workers (int): Maximum number of concurrent scaling threads.
            method (str): Resampling algorithm. Choices: NEAREST, BILINEAR,
                          BICUBIC, LANCZOS (default), BOX, HAMMING.
        """
        self.max_workers = max_workers
        self.method = self.RESAMPLE_MODES.get(method.upper(), Image.Resampling.LANCZOS)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _calc_proportional(self, orig_w: int, orig_h: int,
                           width: Optional[int] = None,
                           height: Optional[int] = None,
                           scale: Optional[float] = None) -> Tuple[int, int]:
        """Calculate proportional dimensions."""
        if scale is not None:
            return int(orig_w * scale), int(orig_h * scale)
        if width is not None:
            return width, int(orig_h * (width / orig_w))
        if height is not None:
            return int(orig_w * (height / orig_h)), height
        raise ValueError('At least one of scale, width, or height must be provided')

    def _fit_image(self, img: Image.Image, target_w: int, target_h: int,
                    resample) -> Image.Image:
        """
        Resize image to cover target box, then center-crop to exact target size.
        Result is always exactly (target_w, target_h).
        """
        orig_w, orig_h = img.size
        scale = max(target_w / orig_w, target_h / orig_h)
        fill_w, fill_h = int(orig_w * scale), int(orig_h * scale)
        resized = img.resize((fill_w, fill_h), resample)

        left = (fill_w - target_w) // 2
        top = (fill_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    def _pad_image(self, img: Image.Image, target_w: int, target_h: int,
                   bg_color: Tuple[int, ...], resample) -> Image.Image:
        """
        Resize image to fit inside target box (keeping aspect ratio),
        then paste onto a bg-color canvas of exactly (target_w, target_h).
        Result is always exactly (target_w, target_h).
        """
        orig_w, orig_h = img.size
        scale = min(target_w / orig_w, target_h / orig_h)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        resized = img.resize((new_w, new_h), resample)

        canvas = Image.new('RGBA' if img.mode == 'RGBA' else 'RGB', (target_w, target_h), bg_color)
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        if img.mode == 'RGBA':
            canvas.paste(resized, (paste_x, paste_y), mask=resized.split()[3])
        else:
            canvas.paste(resized, (paste_x, paste_y))
        return canvas

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def scale_image(self, source_path: str, target_path: str,
                    width: Optional[int] = None,
                    height: Optional[int] = None,
                    scale: Optional[float] = None,
                    size: Optional[Tuple[int, int]] = None,
                    fit: Optional[str] = None,
                    method: Optional[str] = None,
                    keep_depth: bool = True) -> Dict[str, str]:
        """
        Scale / resize a single image.

        Modes (mutually exclusive):
          - proportional: specify width OR height OR scale
          - fixed size  : specify size=(W,H) with fit='crop' or 'pad'

        Args:
            source_path (str): Path to the source image.
            target_path (str): Path where the output will be saved.
            width (int, optional): Target width in pixels (proportional mode).
            height (int, optional): Target height in pixels (proportional mode).
            scale (float, optional): Scale ratio, e.g. 0.5 = half, 2 = double.
            size (tuple, optional): Fixed (width, height) to normalize to.
            fit (str, optional): How to handle mismatch with size.
                                  'crop' = cover & center-crop  (default when size given)
                                  'pad'  = fit inside, pad remainder with bg color.
            method (str, optional): Resampling algorithm override.
                                    Choices: NEAREST, BILINEAR, BICUBIC, LANCZOS, BOX, HAMMING.
                                    Defaults to the TinyScaler instance's method.
            keep_depth (bool): If True (default), P→8-bit palette and L→8-bit grayscale are
                              preserved after scaling. Set False to force RGB output.

        Returns:
            dict: Result with 'status' and 'message'.
        """
        try:
            with Image.open(source_path) as img:
                resample = self.RESAMPLE_MODES.get(
                    method.upper(), self.method
                ) if method else self.method

                orig_mode = img.mode

                if img.mode == 'GIF' and not img.is_animated:
                    img = img.convert('RGBA')
                elif img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')

                if size is not None:
                    target_w, target_h = size
                    if fit == 'pad':
                        bg = (255, 255, 255)
                        output = self._pad_image(img, target_w, target_h, bg, resample)
                        if output.mode == 'RGB':
                            output = output.convert('RGB')
                    else:  # default: crop
                        output = self._fit_image(img, target_w, target_h, resample)
                        if output.mode == 'RGBA':
                            output = output.convert('RGB')
                else:
                    new_w, new_h = self._calc_proportional(
                        img.size[0], img.size[1],
                        width=width, height=height, scale=scale
                    )
                    output = img.resize((new_w, new_h), resample)
                    if output.mode == 'RGBA':
                        output = output.convert('RGB')

                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                if keep_depth and orig_mode == 'P' and output.mode == 'RGB':
                    output = output.convert('P', palette=Image.Palette.WEB)
                elif keep_depth and orig_mode == 'L' and output.mode == 'RGB':
                    output = output.convert('L')

                output.save(target_path)

            return {'status': 'success', 'message': 'Image scaled successfully'}
        except Exception as e:
            return {'status': 'failed', 'message': f'Scaling failed: {str(e)}'}

    def scale_directory(self, source_dir: str, target_dir: str,
                        width: Optional[int] = None,
                        height: Optional[int] = None,
                        scale: Optional[float] = None,
                        size: Optional[Tuple[int, int]] = None,
                        fit: Optional[str] = None,
                        method: Optional[str] = None,
                        keep_depth: bool = True,
                        skip_existing: bool = True) -> Dict[str, Union[int, float]]:
        """
        Scale all supported images in a directory.

        Args:
            source_dir (str): Source directory containing images.
            target_dir (str): Target directory for scaled images.
            width, height, scale: Proportional scaling options.
            size (tuple, optional): Fixed (width, height) to normalize to.
            fit (str, optional): 'crop' (default) or 'pad'.
            method (str, optional): Resampling algorithm. Defaults to instance method.
            keep_depth (bool): Preserve P/L modes after scaling. Default True.
            skip_existing (bool): Skip files already in target.

        Returns:
            dict: Statistics.
        """
        image_files = self._get_image_files(source_dir)

        if skip_existing:
            image_files = [f for f in image_files if self._should_process(f, source_dir, target_dir)]

        total_files = len(image_files)
        if total_files == 0:
            return {'total': 0, 'processed': 0, 'success': 0, 'failed': 0, 'percent': 100.0}

        stats = {'total': total_files, 'processed': 0, 'success': 0, 'failed': 0}

        def _scale_file(fp):
            rel = os.path.relpath(fp, source_dir)
            tgt = os.path.join(target_dir, rel)
            return self.scale_image(fp, tgt, width=width, height=height,
                                    scale=scale, size=size, fit=fit,
                                    method=method, keep_depth=keep_depth)

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
        """Get all supported image files recursively."""
        image_files = []
        for root, _, files in os.walk(directory):
            for name in files:
                file_path = os.path.join(root, name)
                _, file_ext = os.path.splitext(name)
                if file_ext.lower() in self.SUPPORTED_EXTENSIONS:
                    image_files.append(file_path)
        return image_files

    def _should_process(self, file_path: str, source_dir: str, target_dir: str) -> bool:
        """Skip if target already exists."""
        relative_path = os.path.relpath(file_path, source_dir)
        target_path = os.path.join(target_dir, relative_path)
        return not os.path.exists(target_path)
