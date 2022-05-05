from setuptools import find_packages, setup
from pakon import __version__


setup(
    name="pakon",
    version=__version__,
    author="CZ.NIC, z.s.p.o. (http://www.nic.cz/)",
    author_email="packaging@turris.cz",
    packages=find_packages(),
    url="https://gitlab.nic.cz/turris/pakon",
    license="GPL-3.0-only",
    description="Pakon is a system for monitoring network traffic",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "flask",
        "jsonschema",
    ],
    entry_points={
        "console_scripts": [
            "pakon-maintain = pakon.maintain.__main__:main",
            "pakon-handler = pakon.query_socket.__main__:main",  # we may drop exposure here and link the
            "pakon-monitor = pakon.monitor.__main__:main",  # service to the python library instead
            "pakon-show = pakon.show.__main__:main",
        ]
    },
    extras_require={"tests": ["pytest", "flake8", "black"]},
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
    ],
    python_requires="~=3.7",
    zip_safe=True,
)
