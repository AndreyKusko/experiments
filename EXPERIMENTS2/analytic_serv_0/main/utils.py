import typing as tp
from urllib.parse import urljoin, urlparse


def parse_uri_data(uri):
    """
    Изымает данные ссылки из ссылки uri базы данных

    postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
    """
    result = urlparse(uri)
    raw_options = [d.split("=") for d in result.query.split("&") if d]
    options = dict(raw_options) if raw_options else dict()
    return result, options


class ParseLink:
    options: tp.Optional[dict] = None
    url: tp.Optional[str] = None
    path: tp.Optional[str] = None
    url_path: tp.Optional[str] = None

    def __init__(self, link):
        result = urlparse(link)
        raw_options = [d.split("=") for d in result.query.split("&") if d]
        self.options = dict(raw_options) if raw_options else dict()
        self.url = f"{result.scheme}://{result.netloc}"
        self.path = result.path
        self.url_path = urljoin(self.url, self.path)
