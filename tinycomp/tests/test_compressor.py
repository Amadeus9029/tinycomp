"""
Tests for the TinyCompressor class
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from tinycomp import TinyCompressor

class TestTinyCompressor(unittest.TestCase):
    """Test cases for TinyCompressor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compressor = TinyCompressor(api_key="YYKcY8Z99BDJnjvZhgRWJQqqvNFKhlcL")
        self.test_image = "test.png"
        self.test_output = "output.png"
    
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

if __name__ == '__main__':
    unittest.main() 