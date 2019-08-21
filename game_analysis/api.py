from json import loads
from re import findall
from urllib import parse, request

WARZONE_COM = 'https://www.warzone.com'
GAME_ID_REGEX = 'a href="MultiPlayer\\?GameID=(\\d+)"'


# Access an API on Warzone
def hit_api(api, params):
    return post_to_api(api, parse.urlencode(params).encode())


# Access an API on Warzone with the given credentials
def hit_api_with_auth(email, apitoken, api, params):
    prms = {'Email': email, 'APIToken': apitoken}
    prms.update(params)

    return hit_api(api, prms)


# Perform a POST request to Warzone
def post_to_api(api, post_data):
    req = request.Request(WARZONE_COM + api, data=post_data)
    return request.urlopen(req).read()


# Retrieve a user's api token using email and password
def get_api_token(email, password):
    api_token_response = hit_api('/API/GetAPIToken', {'Email': email, 'Password': password})
    return loads(api_token_response)['APIToken']


# Retrieve a page of game ids from the given ladder offset by input amount
def get_ladder_game_ids(ladder_id, offset, max_results=50):
    with request.urlopen(WARZONE_COM + '/LadderGames?ID=' + str(ladder_id) + '&Offset=' + str(offset)) as req:
        html_string = req.read().decode('utf8')

    ladder_game_ids = findall(GAME_ID_REGEX, html_string)
    return ladder_game_ids[0:min(len(ladder_game_ids), max_results)]


# Retrieve game data
def get_game_data_from_id(email, api_token, game_id):
    return hit_api_with_auth(email, api_token, 
            '/API/GameFeed?GameID=' + str(game_id) + '&GetHistory=true&GetSettings=true', {})
