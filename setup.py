from setuptools import setup, find_packages

setup(
    name = 'opentaxii',
    version = '0.0.2',

    packages = find_packages(),
    include_package_data = True,

    package_data = {
        'opentaxii' : ['*.yml']
    },

    dependency_links = [
        'git+https://github.com/TAXIIProject/libtaxii.git#egg=libtaxii-1.1.106'
    ],

    install_requires = [
        'pytz==2014.10',
        'pyyaml',
        'anyconfig',
        'structlog',
        'Flask',
        'sqlalchemy',
        'blinker',
        'bcrypt',
        'pyjwt'
    ],
)
