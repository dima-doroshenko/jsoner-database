from typing import Any
from .errors import UnkownTag
from .errors import ForeignKeyError, KeyNotFound, UniqueValueError, ValueIsConstant
import time

class NewTag:
    """
    >>> # Структура класса
    name = 'tag_name'
    def create(db: Database, value, tag_arg):
        return tag_arg
    def update(db: Database, key: str, old_value, new_value, tag_arg):
        return new_value
    def read(db: Database, key: str, value, tag_arg):
        return value

    `. . .`

    `name` - Имя тега. Можно использовать при указании тега

    Если имя класса заканчивается на `tag`, `Tag`, `_tag` или `_Tag`, то они уберутся из имени

    `. . .`

    `create` - Вызывается при создание тега в файле. Метод должен вернуть преобразованный тег. Если преобразование
    не надо, вернуть `tag_arg`

    `update` - Вызывается при обновлении значения ключа. Не влияет на методы `INCR` и `DECR` в классе `Database`. Чтобы запретить обновление, следует вызвать любую ошибку

    `read` - Вызывается при чтении значения ключа. Если у ключа несколько тегов, то вызывается у первого тега, в котором он есть
 
    `. . .`

    Теги можно устанавливать двумя способами:

    Передав класс тега:
    >>> db.add('key', 'value', {MyTag: True})

    Передав имя тега:
    >>> db.add('key', 'value', {'My': True})
    В данном случае передается 'My', так как 'Tag' и подобные окончания автоматически убираются


    """
    all = []

    def create(db, value, tag_arg) -> Any:
        return tag_arg
    
    def __init_subclass__(cls) -> None:

        if cls.__name__[-3:].lower() == 'tag': cls.__name__ = cls.__name__[:-3].lower()
        if cls.__name__[-1:] == '_': cls.__name__ = cls.__name__[:-1]
    
        try: cls.__name__ = cls.name
        except AttributeError: pass

        cls.all.append(cls)

class Tags:

    @staticmethod
    def create(self, key: str, value, tags: dict) -> None:
        global_tags = Tags.get(self, key)

        tags_list = (
            *list(map(lambda x: (x,True)  , list(global_tags.keys()) )),
            *list(map(lambda x: (x,False) , list(tags.keys())        ))
        )
        
        for tag_name, is_global in tags_list:
                
                try:
                    if is_cls := issubclass(tag_name, NewTag): 
                        tag_cls = tag_name
                        tag_name = tag_name.__name__
                except TypeError:
                    is_cls = False
                
                try: self.data[self.settings]['tags'][key]
                except KeyError: 
                    if not is_global: self.data[self.settings]['tags'][key] = {}

                if not is_cls:

                    tag_dict = {cls.__name__: cls for cls in NewTag.all}
                    tag_cls = tag_dict.get(tag_name)

                    if tag_cls is None: raise UnkownTag(f"Тег '{tag_name}' не найден")

                if is_global: tag_data = global_tags[tag_name]
                else: tag_data = tags[tag_cls] if is_cls else tags[tag_name]

                tag_create_result = tag_cls.create(self, value, tag_data)
                if not is_global: self.data[self.settings]['tags'][key][tag_name] = tag_create_result                    

    @staticmethod
    def delete(self, key: str) -> None:
        try:
            del self.data[self.settings]['tags'][key]
        except:
            ...

    @staticmethod
    def get(self, key: str) -> dict[str, Any]:
        stngs = self.data[self.settings]
        try:
            return {**stngs['tags'][key], **stngs['global_tags']}
        except KeyError:
            return {**stngs['global_tags']}
    
class const_tag(NewTag):
    '''
    `Константа`

    Ключ нельзя будет изменить

    `. . .`

    >>> db.set('pi', 3.141592654, {const_tag: True})
    >>> db.set('pi', 4) 
    >>> raise ValueIsConstant
    '''

    def create(db, value, tag):

        if tag != True:
            raise ValueError('Ожидалось True в значении тега const')
        
        return tag

    def update(db, key, old_value, new_value, tag_arg):
        if tag_arg: raise ValueIsConstant(f"Значением с ключем '{key}' - константа")
        return old_value
    
    def read(db, key: str, value, tag_arg):
        return value
    
class foreign_key_tag(NewTag):
    '''
    `Внешний ключ`

    Проверка, есть новое значение в списке возможных значений

    В аргументе тега следует указать ключ, где значение - спискок возможных значений

    `. . .`
    >>> db.set('user_roles', ['admin', 'moderator', 'member'], {const_tag: True})  
    >>> db.set('user1', 'admin', {foreign_key_tag: 'user_roles'})
    >>> db.set('user1', 0) 
    >>> raise ForeignKeyError
    '''

    def create(db, value, tag):

        try: 
            db.data[tag]
        except KeyError: 
            raise KeyNotFound(f"Ключ '{tag}' не найден")
        
        assert isinstance(db.data[tag], list), 'Внешний ключ должен состоять из списка возможных значений'

        return tag

    def update(db, key, old_value, new_value, tag_arg):

        if not new_value in db.data[tag_arg]:
            raise ForeignKeyError(f"Значения '{new_value}' нет в {db.data[tag_arg]}")
        
        return new_value
        
class ttl_tag(NewTag):
    '''
    `TTL`

    Установка время жизни ключа

    `. . .`

    >>> db.set('key', 'value', {ttl_tag: 10}) 
    >>> print(db.get('key')) 
    >>> 'value'
    >>> time.sleep(10.1)
    >>> print(db.get('key')) 
    >>> None
    '''

    def create(db, value, tag) -> str:
        return tag + time.time()

    def read(db, key, value, tag_arg):
        if time.time() <= tag_arg:
            return value
        else:
            db.delete(key)
            return db.data[db.settings]['default']
        
class typing_tag(NewTag):
    '''
    `Улучшенное изменение значений`

    Поддерживается работа со словарями ( `dict` ) и списками ( `list` )

    При изменении значения следует передать кортеж или список (для словарей), или кортеж (для списков) из двух обьектов, 
    в котором второй объект - значение, которое нужно добавить или изменить

    `. . .`

    `Работа со словарями:`

    Первое значение - путь для ключа

    >>> db.set('key', {}, {typing_tag: True} ) 
    # Добавление ключа id в словарь
    >>> db.set('key', ('id', 11111111) ) 
    # Добавление словаря data, в котором есть ключ text
    >>> db.set('key', ('data.text', 'Hello world') ) 
    >>> print( db.get('key') )
    >>> {
        "id": 11111111,
        "data": {
            "text": "Hello world"
            }
        }

    `. . .`

    `Работа со списками:`

    Первое значение - индекс из списка, либо метод, применимый к спискам
    
    >>> db.set('key', [1, 2, 3, 4, 5], {typing_tag: True} ) 
    # Замена первого элемента
    >>> db.set('key', (0, 'Первый  элемент списка') ) 
    # Замена последнего элемента
    >>> db.set('key', (-1, 'Последний элемент списка') )
    >>> print( db.get('key') ) 
    >>> [
            "Первый  элемент списка", 
            2, 
            3, 
            4, 
            "Последний элемент списка"
        ]
    # Добавление элемента в конец списка
    >>> db.set('key', ('append', 'Теперь это последний элемент списка') ) 
    # Удаление элемента
    >>> db.set('key', ('remove', 'Последний элемент списка') ) 
    >>> print( db.get('key') ) 
    >>> [
            'Первый  элемент списка', 
            2, 
            3, 
            4, 
            'Теперь это последний элемент списка'
        ]
    '''

    def create(db, value, tag):

        if tag != True:
            raise ValueError('Ожидалось True в значении тега typing')

        match type(value)():

            case dict(): return 'dict'
            case list(): return 'list'
            case _ as cls: raise TypeError(f'Тег typing поддерживает классы dict и list, не {type(cls).__name__}')
    
    def update(db, key: str, old_value, new_value, tag_arg):

        match tag_arg:
        
            case 'dict':
                
                if not((isinstance(new_value, list) or isinstance(new_value, tuple)) and len(new_value) == 2 and isinstance(new_value[0], str)):
                    return new_value

                path = new_value[0]
                new_value = new_value[1]

                def deep_merge(source, destination):
                    for key, value in source.items():
                        if isinstance(value, dict):
                            n = destination.setdefault(key, {})
                            deep_merge(value, n)
                        else:
                            destination[key] = value
                    return destination

                res = old_value
                keys = path.split('.')[::-1]
                node = {}
                is_value_set = True
                for key in keys:
                    if is_value_set:
                        node.update({key: new_value})
                        is_value_set = False
                    else:
                        node = {key: node}

                deep_merge(node, res)

                return res
            
            case 'list':

                if not(isinstance(new_value, tuple) and len(new_value) == 2 and (isinstance(new_value[0], int) or isinstance(new_value[0], str))):
                    return new_value
                
                if isinstance(new_value[0], int):
                    index = new_value[0]
                    new_value = new_value[1]

                    res = old_value
                    res[index] = new_value

                    return res
                
                else:
                    method = new_value[0]
                    new_value = new_value[1]

                    if hasattr(list, method):
                        
                        res = old_value

                        getattr(res, method)(new_value)

                        return res
                    
                    else:
                        raise AttributeError(f'У класса list нет метода {method}')
                    
class unique_tag(NewTag):
    '''
    `Уникальность значения`

    >>> db.set('1', 1)
    >>> db.set('2', 2, {unique_tag: True})
    >>> db.set('2', 1)
    >>> raise UniqueValueError
    
    `. . .`
    
    >>> db.set('1', 1)
    >>> db.set('2', 1, {unique_tag: True})
    >>> raise UniqueValueError'''

    def create(db, value, tag):

        if tag != True:
            raise ValueError('Ожидалось True в значении тега unique')
        
        if list(db.data.values()).count(value) > 0:
            raise UniqueValueError(f'Значение {value} не уникально')
        
        return tag
    
    def update(db, key: str, old_value, new_value, tag_arg):

        if list(db.data.values()).count(new_value) > 0:
            raise UniqueValueError(f'Значение {new_value} ключа {key} не уникально')
        
        return new_value
    
    def read(db, key: str, value, tag_arg):

        if list(db.data.values()).count(value) > 1:
            raise UniqueValueError(f'Значение {value} ключа {key} не уникально')
        
        return value
        
__all__ = [
    'const_tag',
    'foreign_key_tag',
    'ttl_tag',
    'typing_tag',
    'unique_tag',
    'NewTag'
]