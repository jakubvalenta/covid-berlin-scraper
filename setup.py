from pathlib import Path

from setuptools import find_packages, setup

from covid_berlin_scraper import __title__

setup(
    name='covid-berlin-scraper',
    version='0.1.0',
    description=__title__,
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    url='https://www.github.com/jakubvalenta/covid-berlin-scraper',
    author='Jakub Valenta',
    author_email='jakub@jakubvalenta.cz',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'dateparser',
        'feedparser',
        'lxml',
        'regex',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'covid-berlin-scraper=covid_berlin_scraper.cli:main'
        ]
    },
)
