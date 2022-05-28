from pathlib import Path

from setuptools import find_packages, setup

from covid_berlin_scraper import __title__

setup(
    name='covid-berlin-scraper',
    version='0.10.2',
    description=__title__,
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    url='https://www.github.com/jakubvalenta/covid-berlin-scraper',
    author='Jakub Valenta',
    author_email='jakub@jakubvalenta.cz',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'dateparser',
        'feedparser',
        'lxml',
        'python-dateutil',
        'regex',
        'requests',
        'sqlalchemy~=1.4',
    ],
    entry_points={
        'console_scripts': [
            'covid-berlin-scraper=covid_berlin_scraper.cli:main'
        ]
    },
    include_package_data=True,
)
