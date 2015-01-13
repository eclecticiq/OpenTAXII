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
        'libtaxii==1.1.105-SNAPSHOT',
        'Flask',
        'sqlalchemy',
        'blinker',
        'pyyaml',
        'gunicorn',
        'redis'
    ],

    dependency_links = [
        'git+https://github.com/TAXIIProject/libtaxii.git#egg=libtaxii',
    ]
)
