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
USER_AGENT = 'svex-crawler/0.1 by Cu3PO42'

now = time.mktime(datetime.datetime.utcnow().timetuple())
half_year_ago = now - 60 * 60 * 24 * 182

def get_token():
    r = requests.post(
        'https://www.reddit.com/api/v1/access_token',
        headers = {
            'User-Agent': USER_AGENT
        },
        data = { 'grant_type': 'client_credentials' },
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    r.raise_for_status()
    return r.json()['access_token']

def handle_request_exception(e):
    print('Request failed')
    time.sleep(60)

@retry(3, handle_request_exception)
@rate_limit(1)
def get_tsvs(token, lower, upper, after):
    r = requests.get(
        'https://oauth.reddit.com/r/SVExchange/search',
        headers = {
            'Authorization': 'bearer ' + token,
            'User-Agent': USER_AGENT
        },
        params = {
            'q': '(NOT flair:banned) AND nsfw:no AND (' + ' OR '.join('title:{:04d}'.format(e) for e in range(lower, upper)) + ')',
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

def get_all_tsvs_in_range(token, tsvs6, tsvs7, lower, upper):
    print('Getting all TSVs in range {:04d}..{:04d}'.format(lower, upper))
    after = None
    while True:
        print('Requesting all threads before ' + str(after))
        (after, res) = get_tsvs(token, lower, upper, after)
        print('Got ' + str(len(res)) + ' results')
        for e in res:
            e = e['data']
            if int(e['created_utc']) <= half_year_ago:
                break
            if e['link_flair_text'] == 'TSV (Gen 6)': tsvs6[int(e['title'])].append({ 'user': e['author'], 'link': e['id'] })
            if e['link_flair_text'] == 'TSV (Gen 7)': tsvs7[int(e['title'])].append({ 'user': e['author'], 'link': e['id'] })
        else:
            if len(res) == 100 and after is not None:
                continue
        break

def get_all_tsvs(token):
    tsvs6 = [[] for i in range(4096)]
    tsvs7 = [[] for i in range(4096)]
    step = 30
    for start in range(0, 4096, step):
        get_all_tsvs_in_range(token, tsvs6, tsvs7, start, min(start+step, 4096))
    return (tsvs6, tsvs7)

def main():
    token = get_token()
    print('Obtained authorization token')
    (tsvs6, tsvs7) = get_all_tsvs(token)
    res = { 
        'tsvs6': tsvs6,
        'tsvs7': tsvs7,
        'last_updated_at': int(now),
        'version': '1'
    }
    with open('tsvs.json', 'w') as out:
        json.dump(res, out)

if __name__ == '__main__':
    main()