# setup.py
from setuptools import setup, find_packages

setup(
    name="clearstone-sdk",
    version="0.1.0",
    description="Checkpoint-based debugging for multi-agent AI systems.",
    author="Pablo San Francisco",
    author_email="pablo@clearstone.dev",
    url="https://github.com/Sancauid/clearstone-sdk",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "langchain>=0.1.0",
        "pydantic>=2.0",
        "click>=8.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-asyncio>=0.21"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        'console_scripts': [
            'clearstone=clearstone.cli.main:cli',
        ],
    },
)
