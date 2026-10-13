from .utils import safe_get, retry, build_url, parse_date, atomic_write


def fetch(url):
    return safe_get(url)
