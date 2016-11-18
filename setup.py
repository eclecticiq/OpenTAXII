import os
from setuptools import setup, find_packages

__version__ = None
exec(open('opentaxii/_version.py').read())


def here(*path):
    return os.path.join(os.path.dirname(__file__), *path)


def get_file_contents(filename):
    with open(here(filename)) as fp:
        return fp.read()


# This is a quick and dirty way to include everything from
# requirements.txt as package dependencies.
install_requires = get_file_contents('requirements.txt').split()

setup(
    name='opentaxii',
    description='TAXII server implementation in Python from EclecticIQ',
    long_description=get_file_contents('README.rst'),
    url='https://github.com/EclecticIQ/OpenTAXII',
    author='EclecticIQ',
    author_email='opentaxii@eclecticiq.com',
    version=__version__,
    license='BSD License',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    package_data={
        'opentaxii': ['*.yml']
    },
    entry_points={
        'console_scripts': [
            'opentaxii-run-dev = opentaxii.cli.run:run_in_dev_mode',
            'opentaxii-create-account = opentaxii.cli.auth:create_account',
            ('opentaxii-create-services = '
             'opentaxii.cli.persistence:create_services'),
            ('opentaxii-create-collections = '
             'opentaxii.cli.persistence:create_collections'),
            ('opentaxii-delete-blocks = '
             'opentaxii.cli.persistence:delete_content_blocks'),
        ]
    },
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        "Programming Language :: Python :: 3.4",
        'Topic :: Internet',
        'Topic :: Security',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
