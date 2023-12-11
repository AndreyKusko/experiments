

# Ошибки Errors

```
# Перехватывание ошибки в try
    except:
# Перехватить указанное исколючение и получить соотвтетсвующий экземпляр
    except name as value:
# Перехватить перечисленные исклчения
    except (name1, name2)
# Перехватить перечисленные исклчения как экземпляр
    except (name1, name2) as value:

# Выполняется если не было исключения
    else:
# Fanaly Блок выполняется всегда
    finally:
    если return будет в try и в finally вернутся резльтат finally
   try:
        return 'qwe'
    ...
    finally:
        return 'asd'
    >>> asd


    try
        ...
    except: NameError:
        ...
    except IndexError:
        ... 
    except KeyError
        ...
    except (AttributError, TypeError, SyntexError):
        ...
    else:
        ...
```
