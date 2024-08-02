from .database import __version__, Database
import os

class Cluster:
    '''
    В подклассе обязателен атрибут `folder_path`, в котором должен хранится путь к папке с файлами баз данных

    `. . .`

    Также возможно расписать общие значения для инициализации объектов баз данных

    Например:

    `class db(Cluster):`

        `folder_path = 'database'`

        `autocommit = True`

    В таком случае во всех задействованных базах атрибуту `autocommit` будет присвоено значение `True`
    
    Это работает с атрибутами `autocommit, settings, encoding, indent, ensure_ascii`

    `. . .`

    После создания подкласса будет доступен атрибут `databases`, в котором хранятся имена всех баз данных

    Например:
    
    database
    \n      | -- users.json
    \n      ` -- data.json
    
    `class db(Cluster):`

        `folder_path = 'database'`

    print(db.databases) >>> ['users', 'data']

    Также станут доступны атрибуты `users` и `data` (Конкретно в этом случае): Они станут объектами класса `Database`, 
    и с ними можно будет взаимодействовать как с обычными объеками класса
    
    `. . .`

    Рекомендуется добавить аннотации к атрибутам для упрощения работы с кластером

    `class db(Cluster):`

        `folder_path = 'database'`

        `users: Database` 
        `data: Database` 

   ` . . .`

    Если создать файл `cluster_settings.json`, то все ключи, хранящиеся в нем, превратятся в атрибуты класса со значениями, 
    взятые из файла

    `cluster_settings.json: `
        `{`
            `"key": "value",`
            `"number": 123`
        `}`

    print(db.key) >>> 'value'
    print(db.number) >>> 123

    Если создать ключи `autocommit, settings, encoding, indent, ensure_ascii`, то их значения будут использованы так-же, как если
    бы они были переданы в атрибутах класса `db`
    '''

    autocommit: bool = False
    settings: str = '__settings__'
    encoding: str = 'utf-8'
    indent: int = 4
    ensure_ascii: bool = False
    databases: list

    def __init_subclass__(cls) -> None:
        
        if not hasattr(cls, 'folder_path'): raise AttributeError(f"В классе {cls.__name__} должен быть атрибут 'folder_path'")

        try:

            clstr_db = Database(f'{cls.folder_path}\\cluster_settings.json')

            for key in clstr_db.keys():
                if key == clstr_db.settings: continue
                setattr(cls, key, clstr_db.get(key))

        except FileNotFoundError:
            ...

        autocommit = cls.autocommit
        settings = cls.settings       
        encoding = cls.encoding       
        indent = cls.indent
        ensure_ascii = cls.ensure_ascii

        cls.databases = []

        for file in os.listdir(cls.folder_path):

            if file.split('.')[-1] != 'json': continue

            setattr(cls, file.split('.')[0], 
                Database(f'{cls.folder_path}\\{file}', autocommit=autocommit,
                            indent=indent, encoding=encoding, settings=settings, ensure_ascii=ensure_ascii))
            
            cls.databases.append(file.split('.')[0])

__all__ = ['Cluster']