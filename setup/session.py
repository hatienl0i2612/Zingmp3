from .module import *
from .utils import removeCharacters

session = requests.Session()


def get_req(url, headers=None, params=None, proxies=None, tries=1, timeout=1, type=None):
    tries_count = 0
    try:
        res = session.get(url=url, headers=headers, params=params, proxies=proxies)
        if res.ok or res.status_code in [502, 503]:
            if type == 'json':
                return res.json()
            elif type == 'text':
                text = res.text
                return removeCharacters(text)
            elif type == 'content':
                return res.content
            return res
        if not res.ok:
            return None
    except (client.IncompleteRead, requests.ConnectionError, requests.RequestException) as e:
        tries_count += 1
        if tries_count >= tries:
            return None
        time.sleep(timeout)
    return


def post_req(url, headers, data=None, tries=1, timeout=3, type=None, type_send='data', proxies=None):
    tries_count = 0
    res = None
    try:
        if type_send == 'data':
            res = session.post(url=url, headers=headers, data=data, proxies=proxies)
        elif type_send == 'json':
            res = session.post(url=url, headers=headers, json=data, proxies=proxies)
        if res.ok or res.status_code in [502, 503]:
            if type == 'json':
                return res.json()
            elif type == 'text':
                return removeCharacters(res.text)
            elif type == 'content':
                return res.content
            return res
        if not res.ok:
            return None
    except (client.IncompleteRead, requests.ConnectionError, requests.RequestException) as e:
        tries_count += 1
        if tries_count >= tries:
            return None
        time.sleep(timeout)
    return None


def update_cookies(cookies, headers=None, url_check=None, key_work_check=None):
    session.cookies.update(cookies)
    if url_check:
        res = get_req(url=url_check, headers=headers)
        if key_work_check in res.url:
            return False
    return True
