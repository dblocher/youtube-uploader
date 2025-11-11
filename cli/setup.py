"""
Setup configuration for YouTube Uploader CLI
"""
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="youtube-uploader",
    version="0.1.0",
    description="CLI tool to upload videos to YouTube via AWS",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "youtube-uploader=youtube_uploader.cli:cli",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
