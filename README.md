# Jsoner Database

```markdown
`Jsoner` - База данных типа ключ-значение
на основе файлов типа JSON
```

## Использование

### Основы
```python
from jsoner import Database

db = Database('db.json')

 # добавление данных
db.add('key', 'value')

# получение
print(db.get('key')) # 'value'

# сохранение в файл
db.commit()

# изменение
db.update('key', 100)

# увеличение значения на 5
db.incr(key, 5)

# уменьшение значения на 15
db.decr(key, 15)

# удаление
db.delete('key')
```

### Теги

Теги создаются путем добавления словаря из пар Тег: значение

```python
from jsoner import Database
from jsoner.tags import const_tag
from jsoner.errors import ValueIsConstant

db = Database('db.json', autocommit=True)

# тег неизменяемого значения
db.add('pi', 3.14, {const_tag: True})

try:
    db.update('pi', 4)
except ValueIsConstant:
     print('Ключ "pi" - константа')

>>> 'Ключ "pi" - константа'
```

Теги и их значения записываются в словарь `tags`

Файл db.json
```json
{
    "__settings__": {
        "__version__": "0.1", 
        "default": null,
        "tags": {
            "pi": {
                "const": true
            }
        }, 
        "global_tags": {}
    },
    "pi": 3.14
}
```

### Создание своих тегов

С помощью класса `NewTag` можно создавать свои теги

```python
from jsoner import Database
from jsoner.tags import NewTag

db = Database('db.json')

class MyTag(NewTag):

    # создании тега, метод должен вернуть преобразованный аргумент тега
    def create(db: Database, value, tag_arg):
        return tag_arg

    # изменение тега
    def update(db: Database, key: str, old_value, new_value, tag_arg):
        return new_value

    # чтение значения
    def read(db: Database, key: str, value, tag_arg):
        return value
```

### Пример создания своего тега
```python
from jsoner import Database
from jsoner.tags import NewTag
import time

class ttl_tag(NewTag):
    'Time to life - время жизни ключа'

    def create(db: Database, value, tag_arg) -> str:

        # tag_arg в данном случае - время действия ключа
        # в аргументе тега сохранится время, до которого действителен ключ
        
        return tag_arg + time.time()

    def read(db: Database, key, value, tag_arg):

        # если текущее время больше аргумента тега, ключ следует удалить, и вернуть значение по умолчанию
        
        if time.time() <= tag_arg:
            return value
        else:
            db.delete(key)
            return db.data[db.settings]['default']

```

### Методы keys, values, items
```python
from jsoner import Database

db = Database('data.json')

# записанные данные
{
    'Ann': {'age': 30, 'job': 'Data Analyst'},
    'Bob': {'age': 25, 'job': 'Python Developer'},
    'John': {'age': 35, 'job': 'Team Lead'}
}


# получение всех ключей
print(db.keys()) 
>>> ['Ann', 'Bob', 'John']


# получение всех значений
print(db.values()) 
>>> [
    {'age': 30, 'job': 'Data Analyst'}, 
    {'age': 25, 'job': 'Python Developer'}, 
    {'age': 35, 'job': 'Team Lead'}
]


# получение всех пар ключ-значение
print(db.items())
>>> [
    ('Ann', {'age': 30, 'job': 'Data Analyst'}),
    ('Bob', {'age': 25, 'job': 'Python Developer'}),
    ('John', {'age': 35, 'job': 'Team Lead'})
]
```

### Установка значения по умолчанию
```python
from jsoner import Database

db = Database('data.json')

# установка значения по умолчанию
db.set_default(0)

print(db.get('Unknown key'))
>>> 0
```

### Добавление глобальных тегов
Глобальные теги действительны и одинаковы для всех ключей 
```python
from jsoner import Database
from jsoner.tags import const_tag
from jsoner.errors import ValueIsConstant

db = Database('data.json')

# добавление глобального тега
db.set_global_tag(const_tag: True)

db.add('num', 123)
db.update('num', 0)
>>> raise ValueIsConstant
```

### Работа с with

При входе в `with` вызывается метод `db.discard()`, который стирает несохраненные в файл данные

Если атрибут `autocommit` у `db` равен `True`, то он заменится на `False`, а при выходе из `with` вернется обратно

При выходе из `with` вызывается метод `db.commit()`
```python
from jsoner import Database

db = Database('data.json')

db.add('num', 0)

with db:
    db.add('key', 'value')

print(db.items())
>>> [('key', 'value')]
```


### Другие полезные методы
 - **discard** - стереть несохраненные в файл данные
 - **get_many** - получить несколько значений по ключам
 - **set** - автоматически либо добавляет, либо изменяет данные. Т. к. при добавлении существующего ключа или обновлении несуществующего вызовется исключение

  - **db[`'key'`] = `'value'`** - установить значение
  - **db[`'key'`]** - прочитать значение

## Кластер

Папка с файлами:

    database
     |-- users.json
     `-- data.json

```python
from jsoner import Cluster

class db(Cluster):
    folder_path = 'database'   
```

В классе `db` создадутся атрибуты `users` и `data`, которые будут объектами класса `Database`

```python
from jsoner import Cluster

class db(Cluster):
    folder_path = 'database'   

    autocommit = True
```
В данном случае во всех задействованных базах атрибуту `autocommit` будет присвоено значение `True`

Это работает со всеми атрибутами, которые можно передать при инициализации объета класса `Database`

Если создать файл `cluster_settings.json` в папке с остальными файлами, то все его ключи станут атрибутами класса

#### cluster_settings.json
```json
{
    "key": "value",
    "autocommit": true
}
```
```python
print(db.key) # 'value'
print(db.autocommit) # True
```
После создания подкласса будет доступен атрибут `databases`, в котором хранятся имена всех баз данных
```python
print(db.databases) # ['users', 'data', 'cluster_settings']
```

## License

Этот проект лицензируется по лицензии [MIT](https://choosealicense.com/licenses/mit/).