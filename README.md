# Coronavirus Berlin Scraper

Download data about the spread of SARS-CoV-2/Covid-19 from the official daily
press releases of the city of Berlin ([Pressemitteilungen der Senatsverwaltung
für Gesundheit, Pflege und
Gleichstellung](https://www.berlin.de/sen/gpg/service/presse/2020/)).

The data includes:

- date and time of the press release
- total number of cases
- total number of recovered cases
- total number of people who died

## Installation

### Mac

``` shell
$ brew install python
$ pip install pipenv
$ make setup
```

### Arch Linux

``` shell
# pacman -S pipenv
$ make setup
```

### Other systems

Install these dependencies manually:

- Python >= 3.7
- pipenv

Then run:

``` shell
$ make setup
```

## Usage

``` shell
$ ./covid-berlin-scraper
    --config config.sample.json \
    --cache cache/ \
    --output covid_berlin_data.csv \
    --verbose
```

## Help

See all command line options:

``` shell
$ ./covid-berlin-scraper --help
```

## Development

### Installation

``` shell
$ make setup-dev
```

### Testing and linting

``` shell
$ make test
$ make lint
```

### Help

``` shell
$ make help
```

## Contributing

__Feel free to remix this project__ under the terms of the [Apache License,
Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
