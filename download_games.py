import api
import re
from urllib import request

GAME_ID_REGEX = "a href=\"MultiPlayer\\?GameID=(\\d+)\""


def get_api_token(email, password):
    return api.hit_api("/API/GetAPIToken", {"Email": email, "Password": password})


def get_ladder_game_ids(ladder_id, offset):
    with request.urlopen("https://www.warzone.com/LadderGames?ID=" + str(ladder_id) + "&Offset=" + str(offset)) as req:
        html_string = req.read().decode("utf8")

    return re.findall(GAME_ID_REGEX, html_string)


def get_game_data_from_id(game_id, email, api_token):
    return api.hit_api_with_auth("/API/GameFeed?GameID=" + str(game_id) + "&GetHistory=true&GetSettings=true", {},
                                 email, api_token)
