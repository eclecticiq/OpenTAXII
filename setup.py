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
        'intelworks-common',
        'structlog',
        'Flask',
        'sqlalchemy',
        'blinker',
        'gunicorn',
        'redis'
    ],
)
