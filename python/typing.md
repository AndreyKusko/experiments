# Типизация 
https://docs.python.org/3/library/typing.html#typing.get_type_hints

```
    import typing as t
    # Callable, Iterator, Union, Optional, List
    import requests

    : Tuple[dict]
    : List[dict]
    : t.Tuple[t.Tuple[int, str, dt.date], ...]  # кортеж кортежей с числом, строкой, datetime, троеточие значит еще кортежи
    : Optional[str]  # или стринга или еще что-то (None) но вероятно стринга
    : requests.Response:

    async def my_func(connection, name: str, rules: Optional[List[dict]] = None) -> dict: 
        Tuple[List[dict], str]

```