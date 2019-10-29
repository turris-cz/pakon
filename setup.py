from setuptools import find_packages, setup
from pakon import __version__


setup(
    name='pakon-light',
    version=__version__,
    author='CZ.NIC, z.s.p.o. (http://www.nic.cz/)',
    author_email='packaging@turris.cz',
    packages=find_packages(),
    url='https://gitlab.labs.nic.cz/turris/pakon',
    license='GPL-3.0-only',
    description='Pakon is a system for monitoring network traffic',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=[
        'pyuci @ git+https://gitlab.labs.nic.cz/turris/pyuci.git',
    ],
    entry_points={
        'console_scripts': [
            'pakon-maintain = pakon.maintain.__main__:main',
            'pakon-handler = pakon.handler:main',
            'pakon-monitor = pakon.monitor:main',
            'pakon-show = pakon.show:main',
        ]
    },
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
    ],
    python_requires='~=3.6',
    zip_safe=True,
)
