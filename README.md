# TinyComp

TinyComp is a Python package that helps you compress images using the TinyPNG API. It provides both a command-line interface and a Python API for easy integration into your projects.

## Features

- Automatic API key management and rotation
- Automatic API key acquisition when needed
- Batch image compression
- Batch image scaling (no API needed)
- Support for multiple image formats (PNG, JPG, JPEG, GIF, BMP, WebP)
- Progress bar for tracking compression/scaling status
- Multi-threaded processing for better performance
- Automatic handling of API usage limits
- Automatic API key update through web automation
- Fixed-size normalization with crop or pad mode

## Installation

```bash
pip install tinycomp-amadeus
```

## Usage

### Command Line Interface

#### Compressing Images

```bash
# Basic compression
tinycomp compress --source ./images --target ./compressed

# With custom API key
tinycomp compress --source ./images --target ./compressed --api-key YOUR_API_KEY

# Set number of threads
tinycomp compress --source ./images --target ./compressed --threads 4

# Enable automatic API key updates when needed
tinycomp compress --source ./images --target ./compressed --auto-update-key
```

#### Managing API Keys

```bash
# Update API key (checks current key first)
tinycomp update-key

# Force update API key even if current one is valid
tinycomp update-key --force
```

#### Scaling Images

```bash
# Scale all images in a directory (proportional, no API needed)
tinycomp scale --source ./images --target ./scaled -sc 0.5

# Scale by width (keeps aspect ratio)
tinycomp scale --source ./images --target ./scaled -w 800

# Scale by height (keeps aspect ratio)
tinycomp scale --source ./images --target ./scaled -he 600

# Normalize all images to a fixed size (1024x1024, center-crop to fit)
tinycomp scale --source ./images --target ./scaled --size 1024x1024

# Normalize with white padding (image fits inside, empty space filled white)
tinycomp scale --source ./images --target ./scaled --size 512x512 --fit pad

# Specify resampling algorithm (default: lanczos)
tinycomp scale --source ./images --target ./scaled -w 800 --method bicubic

# Preserve original bit depth (8-bit P→palette, L→grayscale; default behavior)
tinycomp scale --source ./images --target ./scaled --size 1024x1024

# Disable bit-depth preservation (force RGB 24-bit output)
tinycomp scale --source ./images --target ./scaled --size 1024x1024 --keep-depth false
```

### Python API

```python
from tinycomp import TinyCompressor

# Initialize compressor
compressor = TinyCompressor(api_key="YOUR_API_KEY")  # API key is optional

# Enable automatic API key updates
compressor = TinyCompressor(auto_update_key=True)

# Compress a single image
compressor.compress_image("input.png", "output.png")

# Compress multiple images
compressor.compress_directory("./images", "./compressed")

# Update API key programmatically
from tinycomp.api_manager import APIKeyManager
api_manager = APIKeyManager()
new_key = api_manager.get_new_api_key()
```

#### Image Scaling

```python
from tinycomp import TinyScaler

scaler = TinyScaler()

# Proportional scaling
scaler.scale_image("input.png", "output.png", scale=0.5)
scaler.scale_image("input.png", "output.png", width=800)
scaler.scale_image("input.png", "output.png", height=600)

# Fixed size normalization
scaler.scale_image("input.png", "output.png", size=(1024, 1024), fit="crop")
scaler.scale_image("input.png", "output.png", size=(512, 512), fit="pad")

# Specify resampling algorithm (choices: nearest, bilinear, bicubic, lanczos, box, hamming; default: lanczos)
scaler.scale_image("input.png", "output.png", width=800, method="bicubic")

# Preserve original bit depth (P→8-bit palette, L→8-bit grayscale; default: True)
scaler.scale_image("input.png", "output.png", size=(1024, 1024))

# Disable bit-depth preservation (force RGB 24-bit)
scaler.scale_image("input.png", "output.png", size=(1024, 1024), keep_depth=False)

# Batch scale with method set globally at init
scaler = TinyScaler(method="lanczos")
scaler.scale_directory("./images", "./scaled", size=(1024, 1024))
```

## Configuration

You can configure TinyComp using environment variables:

- `TINYCOMP_API_KEY`: Your TinyPNG API key
- `TINYCOMP_MAX_THREADS`: Maximum number of compression threads (default: 4)

## Requirements

- Python 3.6 or higher
- Chrome/Chromium browser (for automatic API key updates)
- ChromeDriver matching your Chrome version

## API Key Management

TinyComp includes an automatic API key management system that:

1. Automatically rotates between multiple API keys
2. Monitors remaining API usage
3. Can automatically obtain new API keys when needed
4. Saves API keys for future use

The package offers two modes for handling API key depletion:

1. Default mode: Stops compression and notifies when the API key runs out
2. Auto-update mode: Automatically obtains new API keys when needed (use `--auto-update-key` flag)

The automatic key update feature requires:
- Chrome/Chromium browser installed
- ChromeDriver in your system PATH or in the working directory
- Internet connection for accessing TinyPNG website

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 