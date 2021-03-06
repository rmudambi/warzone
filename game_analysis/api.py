import logging

from json import loads
from re import findall
from typing import List
from urllib import error, parse, request

WARZONE_COM = 'https://www.warzone.com'
GAME_ID_REGEX = 'a href="MultiPlayer\\?GameID=(\\d+)"'


# Access an API on Warzone
def hit_api(api: str, params: dict) -> bytes:
    return _post_to_api(api, parse.urlencode(params).encode())


# Access an API on Warzone with the given credentials
def hit_api_with_auth(email: str, apitoken: str, api: str,
        params: dict) -> bytes:
    prms = {'Email': email, 'APIToken': apitoken}
    prms.update(params)

    return hit_api(api, prms)


# Perform a POST request to Warzone
def _post_to_api(api: str, post_data: bytes, retry_number: int = 0) -> bytes:
    try:
        url = WARZONE_COM + api
        logging.debug(f'Posting to {url}')
        req = request.Request(url, data=post_data)
        with request.urlopen(req) as response:
            read_bytes: bytes = response.read()
            return read_bytes
    except error.URLError:
        if retry_number < 2:
            logging.warn(f'Error posting to {url}')
            return _post_to_api(api, post_data, retry_number + 1)
        else:
            logging.error(f'Error posting to {url}')
            raise



# Retrieve a user's api token using email and password
def get_api_token(email: str, password: str) -> str:
    try:
        api_token_response = hit_api('/API/GetAPIToken', 
            {'Email': email, 'Password': password})
        api_token: str = loads(api_token_response)['APIToken']
        return api_token
    except error.URLError as e:
        raise error.URLError('Error getting API Token')


# Retrieve a page of game ids from the given ladder offset by input amount
def get_ladder_game_ids(ladder_id: int, offset: int, 
        max_results:int = 50) -> List[int]:
    with request.urlopen(
        f'{WARZONE_COM}/LadderGames?ID={ladder_id}&Offset={offset}'
    ) as req:
        html_string = req.read().decode('utf8')

    ladder_game_ids = findall(GAME_ID_REGEX, html_string)
    return [int(id) for id in ladder_game_ids[:max_results]]


# Retrieve game data
def get_game_data_from_id(email: str, api_token: str, game_id: int) -> bytes:
    return hit_api_with_auth(email, api_token, 
        f'/API/GameFeed?GameID={game_id}&GetHistory=true&GetSettings=true',{})
