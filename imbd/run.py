import os
import re
import json

import requests
from bs4 import BeautifulSoup
import pandas as pd

# Please use your own API key here
# You can register at https://www.omdbapi.com/apikey.aspx
OMBD_API_KEY = os.getenv('OMBD_API_KEY')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'en-US,en;q=0.9',
}


def main():
    df = pd.DataFrame(scraper())
    df = df.apply(oscar_calculator, axis=1)
    df = df.apply(lambda row: review_penalizer(row, df['votes'].max()), axis=1)
    df.to_csv('modified_top_20_movies.csv', index=False)


def review_penalizer(row, max_votes):
    """
    Benchmark is the biggest vote number.
    Compare every movie’s number of ratings to this and penalize each of them based on the following rule:
    Every 100k deviation from the maximum translates to a point deduction of 0.1.
    """
    row['rating'] = round(row['rating'] - (max_votes - row['votes']) // 100_000 * 0.1, 2)
    return row


def oscar_calculator(row):
    """
    The Oscars should mean something, shouldn’t they? Here are the rewards for them:
    * 1 or 2 oscars → 0.3 point
    * 3 or 5 oscars → 0.5 point
    * 6 to 10 oscars → 1 point
    * 10+ oscars → 1.5 point
    """
    if row['num_oscars'] == 1 or row['num_oscars'] == 2:
        row['rating'] = round(row['rating'] + 0.3, 2)
    elif row['num_oscars'] >= 3 and row['num_oscars'] <= 5:
        row['rating'] = round(row['rating'] + 0.5, 2)
    elif row['num_oscars'] >= 6 and row['num_oscars'] <= 10:
        row['rating'] = round(row['rating'] + 1, 2)
    elif row['num_oscars'] > 10:
        row['rating'] = round(row['rating'] + 1.5, 2)
    return row


def __get_number_of_oscars(awards_value):
    if value := re.search(r"Won (\d+) Oscars", awards_value):
        return int(value.group(1))
    return 0


def __parse_oscars_by_scraping(movie_ref):
    movie_soup = BeautifulSoup(
        requests.get(f'https://www.imdb.com{movie_ref}/awards', timeout=30, headers=HEADERS).text,
        'html.parser',
    )

    return __get_number_of_oscars(
        movie_soup.find("div", {"data-testid": "awards"})
        .find("a", {"aria-label": "See more awards and nominations"})
        .text
    )


def __collect_movie_infos_by_scraping(movie):
    return {
        'name': movie.select('td.titleColumn')[0].select('a')[0].get_text(),
        'rating': float(movie.select('strong')[0].get_text()),
        'votes': int(movie.find('span', {'name': 'nv'})['data-value']),
        'num_oscars': __parse_oscars_by_scraping(movie.select("a")[0]["href"]),
    }


def __collect_movie_infos_by_ombd(movie_id):
    infos = json.loads(
        requests.get(
            f"http://www.omdbapi.com/?i={movie_id}&apikey={OMBD_API_KEY}", timeout=30
        ).text
    )

    return {
        'name': infos['Title'],
        'rating': float(infos['imdbRating']),
        'votes': int(infos['imdbVotes'].replace(',', '')),
        'num_oscars': __get_number_of_oscars(infos['Awards']),
    }


def __collect_raw_movie_list():
    soup = BeautifulSoup(
        requests.get('https://www.imdb.com/chart/top', timeout=30, headers=HEADERS).text,
        "html.parser",
    )
    return soup.find('tbody', {'class': 'lister-list'}).find_all('tr')[:20]


def scraper():
    """
    Scrape the following properties for each movie from the IMDB TOP 250 list.
    It is part to design the data structure for it:
    * Rating
    * Number of ratings
    * Number of Oscars
    * Title of the movie
    """
    movies = __collect_raw_movie_list()

    movie_properties = []
    for movie in movies:
        movie_ref = movie.find('td', {'class': 'titleColumn'}).find('a')['href']
        if OMBD_API_KEY:
            movie_prop = __collect_movie_infos_by_ombd(movie_ref.split('/')[2])
        else:
            movie_prop = __collect_movie_infos_by_scraping(movie)
        movie_properties.append(movie_prop)

    return movie_properties


if __name__ == '__main__':
    main()
