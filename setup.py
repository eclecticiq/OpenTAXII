from setuptools import setup, find_packages

setup(
    name = "taxii-server",
    version = "0.0.1",

    packages = find_packages(),
    include_package_data = True,

    package_data = {
        'taxii_server' : ['*.ini', '*.yml']
    },

    install_requires = [
        'libtaxii',
        'Flask',
        'sqlalchemy',
        'blinker',
        'pyyaml',
    ],

    dependency_links = [
        'git+https://github.com/TAXIIProject/libtaxii.git#egg=libtaxii',
        'https://github.com/STIXProject/python-stix/archive/v1.1.1.3.tar.gz',
        'https://github.com/CybOXProject/python-cybox/archive/v2.1.0.9.tar.gz',
    ]
)
