# imbd
An application that scrapes data from IMDB and adjusts IMDB ratings based on some rules.

## Requirements
You need Python version 3.8+ and an API key for OMDB API. You can register at https://www.omdbapi.com/apikey.aspx. You will be able to make 1000 API calls in the free tier.

## How to run
1. I used Makefile to run build commands. To install packages please run `make build-all`
1. Activate venv `source .venv/bin/activte`
1. Set PYTHONPATH `export PYTHONPATH="$PWD"`.
1. If you want to use OMBD API add your API key to environment variables. `export OMBD_API_KEY=<YOUR_API_KEY>` else just go to the next step.
1. You can run script with `python imbd/run.py`
1. Output is saved to root folder.

## How to test
1. Run `make test`.