# encoding: utf-8

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

__version__ = "0.0.24"


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ["-x", "tests"]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def readme():
    with open("README.rst") as f:
        return f.read()


setup(
    name="vladiate",
    version=__version__,
    description="Vladiate is a strict validation tool for CSV files",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Developers",
    ],
    keywords="validate CSV vampires",
    author="Dustin Ingram",
    author_email="github@dustingram.com",
    url="http://github.com/di/vladiate",
    license="MIT",
    long_description=readme(),
    packages=find_packages(exclude=["examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    extras_require={"s3": ["boto"]},
    tests_require=["pretend", "pytest", 'black;python_version>="3.6"'],
    cmdclass={"test": PyTest},
    entry_points={
        "console_scripts": [
            "vladiate = vladiate.main:main",
        ]
    },
)
