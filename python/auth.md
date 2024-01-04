# Authentication // Authorisation

##  Basic auth
Есть всякие приемы, например basic auth. Авторизация по пользователю и паролю.
```
def request_authentication_server(method, link, data):
    MY_TOKEN = "my_user:user_password"
    creds = HTTPBasicAuth(*settings.NEW_TOKEN.split(":"))
# или
    creds = HTTPBasicAuth(MY_TOKEN.split(":"))
# или 
    creds = HTTPBasicAuth(*['myuser', 'mypassword'])

    response = requests.request(method, link="/my-link/", json=data, auth=creds)
    return response
```

