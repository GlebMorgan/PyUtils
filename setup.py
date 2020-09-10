from pathlib import Path
from setuptools import setup


if __name__ != '__main__':
    raise RuntimeError("setup.py should never be imported")

README = Path('./README.md')

setup(
        name="utils",
        version="1.0.dev2",
        author="GlebMorgan",
        author_email="glebmorgan@gmail.com",
        description="Python utilities for cross-project use",
        long_description=README.read_text(),
        long_description_content_type="text/markdown",
        url='https://github.com/GlebMorgan/PyUtils',

        python_requires='>=3.8.0',
        # setup_requires
        extras_require={'test': 'pytest'},

        # platforms
        # classifiers
)
