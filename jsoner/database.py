import json
from .check import Check
from .tags import Tags, NewTag
from .decorators import autocommit
from . import errors
from typing import Any, TypeAlias

__version__ = '0.1'

default_settings = {'__version__': __version__, 
                    'default': None,
                    'tags': {}, 
                    'global_tags': {}}

JSONValue: TypeAlias = int | str | list | dict | float | tuple

class Database:
    '''`Объект базы данных`'''

    def __init__(self, 
                 database_file: str, 
                 autocommit: bool = False, 
                 indent: int = 4, 
                 encoding: str = 'utf-8',
                 ensure_ascii: bool = True,
                 settings: str = '__settings__'):
        '''
        
        `Объект базы данных`

        >>> db = Database('data.json')
        >>> db['key'] = 'value'
        >>> print(db['key'])
        >>> 'value'
        
        :param database_file: Путь к файлу базы данных
        :param autocommit: После каждого запроса база данных будет сохраняться в файл, если значение установлено на True
        :param indent: Сколько отступов будет в файле при переносе строки. Влияет только на внешний вид
        :param encoding: Кодировка файла. Рекомендуется 'utf-8'
        :param ensure_ascii: Если установлено значение True , в выводе будут экранированы все входящие символы, отличные от ASCII
        :param settings: Зарезервированное имя для настроек, которое будет записано в файле'''
        self.database_file = database_file
        self.data = self.read_data()
        self.autocommit = autocommit
        self.indent = indent
        self.encoding = encoding
        self.settings = settings
        self.ensure_ascii = ensure_ascii
        self.cache = {}

        try: 
            self.data[self.settings]
            db_version = self.data[self.settings]['__version__']
            if db_version != __version__:
                print(f"Текущая версия Jsoner {__version__} не совпадает с версией {db_version} базы данных {self.database_file}")
        except KeyError:
            self.data[self.settings] = default_settings
            self.commit()

    def commit(self) -> None:
        """`Сохранить изменения в файл`"""

        with open(self.database_file, 'w', encoding=self.encoding) as file: 
            json.dump(self.data, file, indent=self.indent, ensure_ascii=self.ensure_ascii) 
    
    @autocommit
    def drop(self):
        '''
        `Удалить все данные`
        '''
        self.data = {self.settings: default_settings}

    def read_data(self) -> dict[str, Any]:
        try:

            with open(self.database_file, 'r') as file:
                return json.load(file)
            
        except FileNotFoundError:

            with open(self.database_file, 'w') as file:
                file.write('{}')
            
            return self.read_data()

    def discard(self) -> None:
        '''`Отменить все несохраненные изменения`'''
        self.data = self.read_data()
        
    def get(self, key: str) -> Any | None:
        """
        `Получить значение по ключу`
        """
        
        try:
            Check.is_key_string(key)

            match key:

                case '*': 
                    
                    return [self.get(key) for key in self.keys]
                
                case _: 

                    try: 
                        tags = Tags.get(self, key)
                         
                        for tag_name in list(tags.keys()):

                            for cls in NewTag.all:

                                if cls.__name__ == tag_name:
                                    if hasattr(cls, 'read'): return cls.read(self, key, self.data[key], tags[tag_name])

                        return self.data[key]

                    except KeyError:

                        return self.data[key]
                    
        except KeyError:

            return self.data[self.settings]['default']
        
    def get_many(self, *keys: tuple[str]) -> list[Any | None]:
        '''`Получить значения по нескольким ключам`'''
        return [self.get(key) for key in keys]

    @autocommit
    def add(self, key: str, value: JSONValue, tags: dict = {}) -> None:
        """
        `Добавление данных`
        
        :param key: Ключ должен быть объектом класса str
        :param value: Значение должно быть объектом стадартных классов 
        :param tags: Словарь должен состоять из пар Тег: Значение
        """

        Check.is_key_string(key)
        Check.is_value_correct(value)
        Check.can_key_be_added(self.data, key)

        Tags.create(self, key, value, tags)

        self.data[key] = value

    @autocommit
    def update(self, key: str, value: JSONValue) -> None:
        """`Изменение данных`"""

        Check.is_key_string(key)
        Check.is_key_exists(self.data, key)
        Check.is_value_correct(value)
        
        Check.can_key_be_updated(self, key, value)

        # обновление в Check.can_key_be_updated

    @autocommit
    def delete(self, key: str) -> None:
        """
        `Удаление данных`
        """

        Check.is_key_string(key)

        try: 
            del self.data[key]
            Tags.delete(self, key)
        except: ...

    @autocommit
    def set(self, key: str, value: JSONValue, tags: dict = {}) -> None:
        """`Установка значения`"""

        try: 
            self.update(key, value)
        except errors.KeyNotFound: 
            self.add(key, value, tags)

    @autocommit
    def incr(self, key: str, number: int | float) -> None:
        """
        `Увеличить значение`
        
        :param number: Число, на которое увеличится значение
        """
         
        Check.is_key_string(key)
        Check.is_key_exists(self.data, key)
        Check.is_number_float_or_int(number)

        self.data[key] += number

    def decr(self, key: str, number: int | float) -> None:
        """
        `Уменьшить значение`
        
        :param number: Число, на которое уменьшится значение
        """
        self.incr(key, -number)

    def keys(self) -> list[str]:
        '''`Все ключи`'''
        ans = list(self.data.keys())
        ans.remove(self.settings)
        return ans

    def values(self) -> list[Any]:
        '''`Все значения`'''
        return self.get_many(*self.keys())
    
    def items(self) -> list[list[str, Any]]:
        '''`Все пары ключ-значение`'''
        return [(key, self.get(key)) for key in self.keys()]
    
    def __getitem__(self, key: str):
        return self.get( str(key) )
    
    @autocommit
    def __setitem__(self, key: str, value: JSONValue):
        return self.set(key, value)
    
    @autocommit
    def set_global_tag(self, tag: str | NewTag, value: Any) -> None:
        '''
        `Устанавливает глобальный тег`
        '''
        if not isinstance(tag, str): tag = tag.__name__
        self.data[self.settings]['global_tags'][tag] = value

    @autocommit
    def set_default(self, default_value: JSONValue) -> None:
        '''
        `Устанавливает значение по умолчанию`
        '''
        self.data[self.settings]['default'] = default_value

    def __enter__(self):
        self.cache['autocommit'], self.autocommit = self.autocommit, False
        self.discard()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.autocommit = self.cache['autocommit']
        self.commit() if exc_type is None else self.discard()

__all__ = ['Database']