
# Python  // Питон


ультернативные питоны
https://youtu.be/xURoyC_qBlE?t=1133
Ускорение кода
jpython 
iron python
cpython - компилируемый близнец питона +
python
руру
python-nogil
mурус

pyston примерно на 10% быстрее cpython
    pyston "lite" - python + JIT
    pyston "pro" - drop-in замена питона
nuitka - python → bin  превращает всю программу в бинарник

Pylnstaller Переключились погорели

3.9-nogil и получили  10х ускорение
Взяли mypy и значительно ускорили код

есть еще 
mojo
codon



mojo - новый компилируемый язык + python



посмотреть все операции, выполняемые функцией 

    
    >>> def greet(name, question):
    ...    return "Hello, " + name + "! How's it " + question + "?"
    The real implementation is slightly faster than that because it uses the BUILD_STRING opcode as an optimization. But functionally they’re the same:
    
    >>> import dis
    >>> dis.dis(greet)
     
      2           0 LOAD_CONST               1 ('Hello, ')
                  2 LOAD_FAST                0 (name)
                  4 FORMAT_VALUE             0
                  6 LOAD_CONST               2 ("! How's it ")
                  8 LOAD_FAST                1 (question)
                 10 FORMAT_VALUE             0
                 12 LOAD_CONST               3 ('?')
                 14 BUILD_STRING             5
                 16 RETURN_VALUE 
