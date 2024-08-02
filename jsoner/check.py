from typing import Any
from .errors import *
from .tags import Tags, NewTag

class Check:

    def is_key_string(key: str) -> None:

        if not isinstance(key, str): 
            raise KeyMustBeStr("Ключ должен быть объектом класса str")

    def is_key_exists(data: dict, key: str) -> None | bool:

        try: 
            data[key]
            return True
        except KeyError: 
            raise KeyNotFound(f"Ключ '{key}' не найден")
        
    def is_number_float_or_int(number: int | float) -> None:

        if not any((isinstance(number, int), isinstance(number,float))):
            raise TypeError("Число должно быть объектом класса int или float")
        
    def is_value_correct(value: Any):
        
        if not type(value) in (str, int, float, list, dict, tuple): 
            raise TypeError(f'Объекты типа {value.__class__.__name__} не поддерживаются для перевода в JSON')
        
    def can_key_be_added(data: dict, key: str) -> None | bool:
        try: 
            data[key]
            raise KeyAddError(f"Ключ '{key}' yже существует. Для изменения ключа примените методы update или set")
        except KeyError: return True
        
    @staticmethod
    def can_key_be_updated(self, key: str, value) -> None:

        tags = Tags.get(self, key)
            
        for tag_name in list(tags.keys()):
            for cls in NewTag.all:
                if cls.__name__ == tag_name:
                    if hasattr(cls, 'update'): 
                        result = cls.update(self, key, self.data[key], value, tags[tag_name])
                        self.data[key] = result
                        return

        self.data[key] = value

        # try: 
        #     tags = Tags.get(self, key)
             
        #     for tag_name in list(tags.keys()):
        #         for cls in NewTag.all:
        #             if cls.__name__ == tag_name:
        #                 if hasattr(cls, 'update'): 
        #                     result = cls.update(self, key, self.data[key], value, tags[tag_name])
        #                     self.data[key] = result
        #                     return

        # except KeyError:
        #     ...
        # finally:
        #     self.data[key] = value

__all__ = ['Check']