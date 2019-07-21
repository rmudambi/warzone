import re
from urllib import parse, request

WARZONE_COM = 'https://www.warzone.com'
GAME_ID_REGEX = 'a href="MultiPlayer\\?GameID=(\\d+)"'


# Access an API on Warzone
def hit_api(api, params):
    return post_to_api(api, parse.urlencode(params).encode())


# Access an API on Warzone with the given credentials
def hit_api_with_auth(api, params, email, apitoken):
    prms = {'Email': email, 'APIToken': apitoken}
    prms.update(params)

    return hit_api(api, prms)


# Perform a POST request to Warzone
def post_to_api(api, post_data):
    req = request.Request(WARZONE_COM + api, data=post_data)
    return request.urlopen(req).read()


# Retrieve a user's api token using email and password
def get_api_token(email, password):
    return hit_api('/API/GetAPIToken', {'Email': email, 'Password': password})


# Retrieve a page of game ids from the given ladder offset by input amount
def get_ladder_game_ids(ladder_id, offset):
    with request.urlopen(WARZONE_COM + '/LadderGames?ID=' + str(ladder_id) + '&Offset=' + str(offset)) as req:
        html_string = req.read().decode('utf8')

    return re.findall(GAME_ID_REGEX, html_string)


# Retrieve game data
def get_game_data_from_id(game_id, email, api_token):
    return hit_api_with_auth('/API/GameFeed?GameID=' + str(game_id) + '&GetHistory=true&GetSettings=true', {}, email,
                             api_token)
