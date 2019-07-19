from urllib import parse, request


wlnet = 'https://www.warlight.net'


def hit_api(api, params):
    return postToApi(api, parse.urlencode(params).encode())


def hit_api_with_auth(api, params, email, apitoken):
    prms = {'Email': email, 'APIToken': apitoken}
    prms.update(params)

    return hit_api(api, prms)


def postToApi(api, post_data):
    req = request.Request(wlnet + api, data=post_data)
    return request.urlopen(req).read()

