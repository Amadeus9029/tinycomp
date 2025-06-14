from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tinycomp-amadeus",
    version="0.1.2",
    author="Amadeus9029",
    author_email="965720890@qq.com",
    description="A Python package for compressing images using TinyPNG API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Amadeus9029/tinycomp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
    install_requires=[
        "tinify",
        "requests",
        "tqdm",
        "beautifulsoup4",
        "selenium",
        "fake-useragent"
    ],
    entry_points={
        'console_scripts': [
            'tinycomp=tinycomp.cli:main',
        ],
    },
) 