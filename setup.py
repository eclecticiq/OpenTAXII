from os.path import join, dirname
from setuptools import setup, find_packages

__version__ = None
execfile('opentaxii/_version.py')

CURRENT_DIR = dirname(__file__)

def get_file_contents(filename):
    with open(join(CURRENT_DIR, filename)) as fp:
        return fp.read()

setup(
    name = 'opentaxii',
    description = 'Intelworks TAXII server implementation',
    long_description = get_file_contents('README.rst'),
    url = 'https://github.com/Intelworks/OpenTAXII',
    author = 'Intelworks',
    author_email = 'opentaxii@intelworks.com',
    version = __version__,
    license = 'BSD License',
    packages = find_packages(exclude=['tests']),
    include_package_data = True,
    package_data = {
        'opentaxii' : ['*.yml']
    },
    entry_points = {
        'console_scripts' : [
            'opentaxii-run-dev = opentaxii.cli.run:run_in_dev_mode',
            'opentaxii-create-account = opentaxii.cli.auth:create_account',
            'opentaxii-create-services = opentaxii.cli.persistence:create_services',
            'opentaxii-create-collections = opentaxii.cli.persistence:create_collections',
        ]
    },
    install_requires = [
        'pytz==2014.10',
        'pyyaml',
        'anyconfig',
        'structlog',
        'Flask',
        'sqlalchemy',
        'blinker',
        'bcrypt',
        'pyjwt',
        'libtaxii>=1.1.106'
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Internet',
        'Topic :: Security',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
