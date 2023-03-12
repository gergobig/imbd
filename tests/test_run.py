from unittest.mock import patch
import requests

import pytest
import pandas as pd

from imbd.run import (
    __collect_raw_movie_list,
    __collect_movie_infos_by_ombd,
    __parse_oscars_by_scraping,
    __get_number_of_oscars,
    oscar_calculator,
    review_penalizer,
)


@patch.object(requests, 'get')
def test_collect_raw_movie_list(mock_get):
    mock_get.return_value.text = (
        '<tbody class="lister-list"><tr>Mock movie 1</tr><tr>Mock movie 2</tr></tbody>'
    )

    result = __collect_raw_movie_list()
    assert len(result) == 2
    assert result[0].get_text() == 'Mock movie 1'
    assert result[1].get_text() == 'Mock movie 2'


@patch.object(requests, 'get')
def test_collect_movie_infos_by_ombd(mock_get):
    mock_get.return_value.text = '{"Title":"Mock movie","Awards":"Nominated for 1 Oscar. 15 wins & 60 nominations total","imdbRating":"7.6","imdbVotes":"691,435"}'

    assert __collect_movie_infos_by_ombd('dummy_id') == {
        'name': 'Mock movie',
        'rating': 7.6,
        'votes': 691435,
        'num_oscars': 0,
    }


@pytest.mark.parametrize(
    'mock_value,expected_value',
    [
        (
            '<div data-testid="awards"><a aria-label="See more awards and nominations">Nominated for 7 Oscars</a></div>',
            0,
        ),
        (
            '<div data-testid="awards"><a aria-label="See more awards and nominations">Won 7 Oscars</a></div>',
            7,
        ),
    ],
)
@patch.object(requests, 'get')
def test_parse_oscars_by_scraping(mock_get, mock_value, expected_value):
    mock_get.return_value.text = mock_value

    assert __parse_oscars_by_scraping('/dummy_ref/') == expected_value


@pytest.mark.parametrize(
    'input_value,expected_value',
    [
        (
            'Nominated 7 Oscars',
            0,
        ),
        (
            '14 Oscars',
            0,
        ),
        (
            'hikulapikula 4 Oscars',
            0,
        ),
        (
            'Won 3 Oscars',
            3,
        ),
        (
            'Won 14 Oscars',
            14,
        ),
    ],
)
def test_get_number_of_oscars(input_value, expected_value):
    assert __get_number_of_oscars(input_value) == expected_value


@pytest.mark.parametrize(
    'input_value,expected_value',
    [
        (
            pd.Series({'name': 'Movie 1', 'rating': 9.3, 'votes': 0, 'num_oscars': 0}),
            9.3,
        ),
        (
            pd.Series({'name': 'Movie 2', 'rating': 9.3, 'votes': 0, 'num_oscars': 3}),
            9.8,
        ),
        (
            pd.Series({'name': 'Movie 3', 'rating': 9.3, 'votes': 0, 'num_oscars': 10}),
            10.3,
        ),
        (
            pd.Series({'name': 'Movie 3', 'rating': 9.3, 'votes': 0, 'num_oscars': 11}),
            10.8,
        ),
        (
            pd.Series({'name': 'Movie 3', 'rating': 9.3, 'votes': 0, 'num_oscars': 1}),
            9.6,
        ),
    ],
)
def test_oscar_calculator(input_value, expected_value):
    assert oscar_calculator(input_value)['rating'] == expected_value


@pytest.mark.parametrize(
    'input_value,expected_value',
    [
        (
            pd.Series({'name': 'Movie 1', 'rating': 9.3, 'votes': 250_000, 'num_oscars': 0}),
            9.1,
        ),
        (
            pd.Series({'name': 'Movie 2', 'rating': 9.3, 'votes': 490_000, 'num_oscars': 3}),
            9.3,
        ),
        (
            pd.Series({'name': 'Movie 3', 'rating': 9.3, 'votes': 100_000, 'num_oscars': 10}),
            8.9,
        ),
    ],
)
def test_review_penalizer(input_value, expected_value):
    max_value = 500_000

    assert review_penalizer(input_value, max_value)['rating'] == expected_value
