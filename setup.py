#!/usr/bin/env python3

#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.


import setuptools

with open('README.md') as f:
    long_description = ''.join(f.readlines())

setuptools.setup(
    name='pakon_light',
    version='1.2.1',
    packages=setuptools.find_packages(exclude=['tests']),
    include_package_data=True,
    description='Pakon services.',
    long_description=long_description,
    author='CZ.NIC, z.s.p.o. (http://www.nic.cz/)',
    author_email='kontakt@nic.cz',

    # All versions are fixed just for case. Once in while try to check for new versions.
    install_requires=[
        'sqlalchemy>=1.3.7',
        'cachetools>=4.1.0'
    ],

    # Do not use test_require or build_require, because then it's not installed and is
    # able to be used only by setup.py util. We want to use it manually.
    # Actually it could be all in dev-requirements.txt but it's good to have it here
    # next to run dependencies and have it separated by purposes.
    extras_require={
        'devel': [
            'pylint==2.1.0',
            'pytest==3.1.1',
        ],
    },

    entry_points={
        'console_scripts': [
            'pakon-create-db = pakon_light.cli:create_db',
            'pakon-archive = pakon_light.cli:archive',
        ],
    },

    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    zip_safe=False,
)
