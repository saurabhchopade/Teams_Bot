"""Setup script for the Microsoft Teams Interview Bot."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="teams-interview-bot",
    version="1.0.0",
    author="Teams Interview Bot Team",
    author_email="support@teamsinterviewbot.com",
    description="AI-powered interview bot for Microsoft Teams with voice integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/teams-interview-bot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Conferencing",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "coverage>=7.3.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "teams-interview-bot=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yml", "*.yaml"],
    },
    keywords="microsoft teams interview bot ai voice azure openai",
    project_urls={
        "Bug Reports": "https://github.com/your-org/teams-interview-bot/issues",
        "Source": "https://github.com/your-org/teams-interview-bot",
        "Documentation": "https://teams-interview-bot.readthedocs.io/",
    },
)