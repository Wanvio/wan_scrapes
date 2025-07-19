from setuptools import setup, find_packages

setup(
    name="wan-scraps",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4",
        "requests",
        "python-dotenv",
        "pyfiglet",
        "colorama"
    ],
    entry_points={
        "console_scripts": [
            "wan-scraps=wan_scraps.main:main",
        ],
    },
    author="Your Name",
    description="Web scraper and Discord reporter for structured web content",
    license="MIT",
)
