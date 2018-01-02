#!/usr/bin/env python3
import requests
import os
import time
import datetime
import json

def rate_limit(rate = 1):
    period = 1 / rate
    def decorator(fun):
        last_called = [0]
        def wrapped(*args, **kwargs):
            while time.time() < last_called[0] + period:
                time.sleep(last_called[0] + period - time.time())
            last_called[0] = time.time()
            return fun(*args, **kwargs)
        return wrapped
    return decorator

def retry(times, except_handler):
    def decorator(fun):
        def wrapped(*args, **kwargs):
            for i in range(times-1):
                try:
                    return fun(*args, **kwargs)
                except Exception as e:
                    if except_handler:
                        except_handler(e)
            return fun(*args, **kwargs)
        return wrapped
    return decorator

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

now = time.mktime(datetime.datetime.utcnow().timetuple())
half_year_ago = now - 60 * 60 * 24 * 182

def get_token():
    r = requests.post(
        'https://www.reddit.com/api/v1/access_token',
        data = { 'grant_type': 'client_credentials' },
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    r.raise_for_status()
    return r.json()['access_token']

def handle_request_exception(e):
    time.sleep(60)

@retry(3, handle_request_exception)
@rate_limit(1)
def get_tsvs(token, generation, after):
    r = requests.get(
        'https://oauth.reddit.com/r/SVExchange/search',
        headers = {
            'Authorization': 'bearer ' + token,
            'User-Agent': 'svex-crawler/0.1 by Cu3PO42'
        },
        params = {
            'q': 'flair:"TSV (Gen ' + str(generation) + ')" AND (NOT flair:banned) AND nsfw:no',
            'include_facets': 'false',
            'show': 'all',
            'sort': 'new',
            'restrict_sr': 'true',
            't': 'all',
            'syntax': 'lucene',
            'after': after or 'none',
            'limit': '100'
        }
    )
    r.raise_for_status()
    data = r.json()['data']
    return (data['after'], data['children'])

def get_all_tsvs(token, generation):
    print('Getting all TSVs for generation ' + str(generation))
    tsvs = [[] for i in range(4096)]
    after = None
    while True:
        print('Requesting all threads before ' + str(after))
        (after, res) = get_tsvs(token, generation, after)
        for e in res:
            e = e['data']
            tsvs[int(e['title'])].append({ 'user': e['author'], 'link': e['id'] })
            if int(e['created_utc']) <= half_year_ago:
                break
        else:
            if len(res) > 0 and after is not None:
                continue
        break
    return tsvs

def main():
    token = get_token()
    print('Obtained authorization token')
    res = { 
        'tsvs6': get_all_tsvs(token, 6),
        'tsvs7': get_all_tsvs(token, 7),
        'last_updated_at': int(now),
        'version': '1'
    }
    with open('tsvs.json', 'w') as out:
        json.dump(res, out)

if __name__ == '__main__':
    main()