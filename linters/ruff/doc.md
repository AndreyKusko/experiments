# линтер ruff // linter ruff
    
    
    ruff check.
    -ignore=I,EM,FBT,TRY003,$101,D1,FA,ANN1011
    --line-length=1201
    -fixable=ALL\
    -select=ALL \
    --unsafe-fixes

ruff format .

https://youtu.be/G3JKtB8tgvg?t=1447


Как pyproject.toml может выглядеть
Для конфигурации ruff (в бонус пресет для тестов)

    [tool.ruff]
    fix = true
    unsafe-fixes = true
    line-length = 120
    select = ["'ALL']
    ignore = ["D1", "D203", "D213", "FA102", "ANN101"]
    cache-dir = "/tmp/ruff-cache/"
    [tool.ruff./sort]
    no-lines-before = ["standard-library", "local-folder"]
    known-third-party = 0
    known-local-folder = [whole_app"]
    [tool.ruff.extend-per-file-ignores)
    "tests/"py" = [ANN401", "S'101", "S311"]


конфигурация для ruff и vscode 

    "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnPaste": true,
    "editor.formatOnType": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
    "source.fixAll": true,
    "source.organizelmports": true
    }
    }
