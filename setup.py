#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip

pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile['packages'], r=False)
test_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.md') as history_file:
    history = history_file.read()

setuptools.setup(
    name="rigor",
    version='0.4.3',

    package_dir={
        '': 'src'
    },

    packages=[
        "rigor",
    ],

    include_package_data=True,

    package_data={
        '': ['*.jar'],
    },

    install_requires=requirements,

    tests_require=test_requirements,

    setup_requires=[
        'pytest-runner',
    ],

    license="MIT license",

    keywords='',
    description="rigor",
    long_description="%s\n\n%s" % (readme, history),

    entry_points={
        'console_scripts': [
            'rigor=rigor.cli:main',
        ]
    },

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
