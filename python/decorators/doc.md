# Декораторы
- [простой декоратор](https://passingcuriosity.com/2009/writing-view-decorators-for-django/)
- [Более сложный декоратор](https://habr.com/post/145709/)

**Для декортора @login_required бязательно нужен request или что-то с user иначе шаласть неудастся**

**Из декортора можно послать информацию в функцию. Из функции в декоратор - нет. Концепт...**
**Но можно можно послать инфу в декоратор другим способом... (См ниже)**

**Пример с работы** 
```
def my_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            ...
```

**Пример самого простого декоратора**
the_func - здесь сама функция (она типа становится позиционным аргументом
```
def my_decorator(the_func):
    print('My decorator worked')
    return the_func

@my_decorator
def my_function(qwe):
    print('my_function worked', qwe)
    . . .
    return qwe
    
my_function(123)

# Сначала сработает декоратор, потом функция
    >>>> My decorator worked
    >>>> my_function worked, 123
```
**Посмотреть через декоратор сколько выполняется функция**
```
def my_decorator(original_function):      
    def wrapper(*args,**kwargs):
        import datetime                 
        before = datetime.datetime.now()                     
        x = original_function(*args, **kwargs)                
        print("Elapsed Time = {0}".format(datetime.datetime.now()-before))  
        print('infinite_decorator')
        return x                                             
    return wrapper                                   
    
@infinite_decorator
def my_func(stuff):
    import time
    print(time.sleep(3))
    print('func_a(stuff)', stuff)

func_a(1)
# Или
    def my_decorator(original_function):   
        import datetime                 
        before = datetime.datetime.now() 
        def wrapper(*args,**kwargs):            
            x = original_function(*args,**kwargs)            
            print("Elapsed Time = {0}".format(datetime.datetime.now()-before))                  
            return x        
        return wrapper  
```
**... Типа: создать декоратор, который будет вызывать функцию вечно вечно.**
```
def my_deco(func):
    def wrapper(*args, **kwargs):
        x = 1
        while x:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                pass
    return wrapper

@my_deco
def my_fucntion(qwe):
    time.sleep(2)
    print('my_fucntion', qwe)
    raise Exception('123')

my_fucntion(123)
```

**Декоратором может получать информацию из позиционных аргументов**
Можно написать особую обработку входящей информации
```
# Пример 1. Получение информации из request
    def my_decorator(the_func):
        def wraper(request, *args, **kwargs):
            print(request.user.username)
            return the_func(request, *args, **kwargs)
        return wraper

    @my_decorator
    def my_function(request):
        . . .
        return render(request, "my_html.html", context)

    >>>> cheytin@mail.ru

# Пример 2. Можно задать и просто строчку
    def if_green(function):
        def run_function_if_green(color, *args, **kwargs):
            if color == 'green':
                return function(*args, **kwargs)
        return run_function_if_green

    @if_green
    def print_if_green(color):
        print('what a nice color!')

    print_if_green('green')
    print_if_green('red')
    >>>> green what a nice color!

# Пример 3. Послать даже целую модель, но понадобится импортировтаь wraps
    from django.utils.functional import wraps

    def my_decorator(model_class, redirect_url):
        def decorator(the_func):
            def wraper(request, *args, **kwargs):
                product = model_class.objects.get(id=1)
                print(product.title, redirect_url)
                return the_func(*args, **kwargs)
            return wraps(the_func)(wraper)
        return decorator

        @my_decorator(Product, '/')
        def my_function(*args,  **kwargs):
            return

        >>>> Product title 1 /
# или 
    from django.utils.functional import wraps

    def my_decorator(model_class, redirect_url=None, *args, **kwargs):
        def decorator(the_func):
            def wraper(request, *args, **kwargs):
                product = model_class.objects.get(id=1)
                print(product.title, redirect_url)
                return the_func(*args, **kwargs)
            return wraps(the_func)(wraper)
        return decorator

    @my_decorator(Product, redirect_url='/')
        def my_function(*args,  **kwargs):
            return

        >>>> Product title 1 /

# Пример 4. Из request,  другого позиционного аргумента функции или args и kwargs
    def my_decorator(the_func):
        def wraper(*args, **kwargs):
            print(args)
            return the_func(*args, **kwargs)
        return wraper

    @my_decorator
    def my_function(*args,  **kwargs):
        return

my_function('green')

    >>>> ('green',)
```

**Из декоратора можно послать какую-нибудь информацию в функию.**
```
    def my_decorator(function):
        def wrap_function(*args, **kwargs):
            kwargs['str'] = 'Hello!'
            return function(*args, **kwargs)
        return wrap_function

    @my_decorator
    def my_function(*args,  **kwargs):
        print(kwargs['str'])
        return

    >>>> Hello!
```

**Декоратором можно поймать ошибку, произошедшую в функции, проверить регистрацию и сделать что-ниубдь**
Скажем, перейти на другую страничку. Но для этого понадобится фукция внутри
```
    def my_decorator(the_func):
        def wraper(*args, **kwargs):
            try:
                return the_func(*args, **kwargs)
            except ObjectDoesNotExist:
                return redirect('/tape/')
        return wraper

    @my_decorator
    def my_function(request):
        raise ObjectDoesNotExist
        return render(request, "my_html.html", context)
```

