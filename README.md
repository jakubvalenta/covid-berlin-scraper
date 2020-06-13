# Scraper for Covid-19 Data in Berlin

This program downloads data on the number of coronavirus cases, recovered cases
and deaths in Berlin, Germany from the official press releases of the city of
Berlin: [Pressemitteilungen der Senatsverwaltung für Gesundheit, Pflege und
Gleichstellung](https://www.berlin.de/sen/gpg/service/presse/2020/).

See [covid-berlin-data](https://www.github.com/jakubvalenta/covid-berlin-data)
for the data itself (updated daily).

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

This program works in three steps:

1. Download press releases from the current RSS feed and save their metadata in
   a database in the passed cache directory:

    ``` shell
    $ ./covid-berlin-scraper --cache my_cache_dir --verbose download-feed
    ```

2. Download press releases from the press release archive and save their
   metadata in the same database:

    ``` shell
    $ ./covid-berlin-scraper --cache my_cache_dir --verbose download-archives
    ```

3. Download and parse the content of all press releases stored in the database
   and generate a CSV output:

    ``` shell
    $ ./covid-berlin-scraper --cache my_cache_dir --verbose parse-press-releases \
        -o my_output.csv \
        --output-hosp my_output_incl_hospitalized.csv
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
