# Aiohttp

- https://habr.com/ru/post/337420/
- https://habr.com/ru/post/421625/
- https://ru.coursera.org/lecture/diving-in-python/piervyie-shaghi-s-asyncio-8XNAV **<- тут еще есть другие лекции**
- http://onreader.mdl.ru/UsingAsyncioPython3/content/Ch03.html
**Слышал об алгебраических эффектах?**
- https://overreacted.io/algebraic-effects-for-the-rest-of-us/
- https://docs.python.org/3/library/asyncio-task.html#creating-tasks
**Async aio не умеет по умолчанию делать асинхронные запросы к бд
Нужны спец драйверы например, asynpg
async postgres
- https://github.com/MagicStack/asyncpg
**Coroutines and Tasks**
- https://docs.python.org/3/library/asyncio-task.html#creating-tasks

пример функции 
```
async def send_post_somewhere(data: dict) -> ClientResponse:
    headers = {"Content-Type": "application/json", "Authorization": HRM_TOKEN}
    async with aiohttp.ClientSession(headers=headers) as client_session:
        link = "".join([MAIN_URL, MY_LOGIC_LINK])
        response = await client_session.post(link, json=data)
        return response
```
**в функции запускается через await**
используется на все запросы, на которых функция может заблокироваться. 
`result = await my_async_function(data)`

если просто запустить функцию в консоли, вернется корутина, запускать через event loop.
`r = asyncio.get_event_loop().run_until_complete( my_async_function(data) )`


### Запросы к сторонним ресурсам
сессия хранит хедеры, а вот куки лучше запихивать отдельно.
- https://docs.aiohttp.org/en/stable/client_advanced.html#custom-request-headers
Для передачи данных в виде json лучше юзать аттрибут json, data - байтовые строки и т.д.
```
aiohttp.ClientSession()  # <- лучше делать запросы через ClientSession. Он асинхронный.

async def send_post_somewhere(data: dict) -> ClientResponse:
    headers = {"Content-Type": "application/json", "Authorization": HRM_TOKEN}
    async with aiohttp.ClientSession(headers=headers) as client_session: 
        link = "".join([MAIN_URL, MY_LOGIC_LINK])
        response = await client_session.post(link, json=data)
        return response
```
```
client_session = aiohttp.ClientSession()  # <- лучше делать запросы через ClientSession. Он асинхронный.

r = asyncio.get_event_loop().run_until_complete(
    client_session.post('
        http://127.0.0.1:8000/api/my_api_link/', json=data, 
        headers=headers  # <- headers лучше переносить в атрибут при обределении ClientSession 
        ))
```