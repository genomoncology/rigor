#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.md") as history_file:
    history = history_file.read()

with open("dev-requirements.txt") as dev_requirements_file:
    tests_require = [r.strip() for r in dev_requirements_file.readlines()]

with open("./src/rigor/version.py") as version_file:
    __version__ = version_file.read().split('"')[1]

setup(
    name="rigor",
    version=__version__,
    url="https://github.com/genomoncology/rigor",
    package_dir={"": "src"},
    packages=[
        "rigor",
    ],
    include_package_data=True,
    package_data={
        "": ["*.jar"],
    },
    install_requires=[
        "addict==2.1.1",
        "aiofiles==0.8.0",
        "beautifulsoup4==4.10.0",
        "click >=8.0.0,<9.0.0",
        "colorama==0.4.3",
        "httpx==0.22.0",
        "hyperlink==17.3.1",
        "importlib-metadata==4.2.0",
        "jmespath==0.9.3",
        "related==0.7.3",
        "structlog==17.2.0",
        "xlwt==1.3.0",
    ],
    setup_requires=[
        "pytest-runner",
    ],
    license="MIT license",
    keywords="",
    description="rigor",
    long_description="%s\n\n%s" % (readme, history),
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "rigor=rigor.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Framework :: Pytest",
    ],
)
