# encoding: utf-8

from setuptools import setup, find_packages, Command
import sys, os

version = '0.7.3'

from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='vladiate',
    version=version,
    description="Vladiate is a strict validation tool for CSV files",
    long_description="""Vladiate is a strict validation tool for CSV files""",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Intended Audience :: Developers",
    ],
    keywords='',
    author='Dustin Ingram',
    author_email='github@dustingram.com',
    url='http://github.com/di/vladiate',
    license='MIT',
    packages=find_packages(exclude=['examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    entry_points={
        'console_scripts': [
            'vladiate = vladiate.main:main',
        ]
    }, )
