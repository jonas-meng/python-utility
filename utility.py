import functools
import inspect
from typing import Callable, List, Any, Dict


def auto_field_assignment(special_items: List[str] = None) -> Callable:
    """Used when fields and passed parameters share same name.

    Potential problem: due to explict declaration of fields in __init__,
    reference of fields in other methods might be confusing to both readers and programs (e.g. type checkers).
    Therefore, this decorator is more recommended for pure data items.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def decorated(*args, **kwargs) -> None:
            self_ = args[0]

            # merge args into kwargs
            signature = inspect.signature(func)
            parameters = (param for param in signature.parameters if param != "self")
            for name, value in zip(parameters, args[1:]):
                kwargs[name] = value

            for name, value in kwargs.items():
                if name in special_items:
                    continue
                setattr(self_, name, value)

            func(self_, **kwargs)
        return decorated
    return decorator


class AbstractFactory(object):
    """Abstract factory following factory pattern managing class registration and creation.
    Concrete factory creates their own namespace preventing name collision.

    """
    registry = {} # type: Dict[str, Callable]

    @staticmethod
    def default_tag(registree: Callable) -> str:
        """ generate the default tag of registree """
        return registree.__name__

    @classmethod
    def namespace(cls) -> str:
        """ generate the namespace of the class """
        return f"{cls.__module__}.{cls.__name__}"

    @classmethod
    def canonicalize(cls, tag: str) -> str:
        """ concatenate class namespace with tag """
        return f"{cls.namespace()}.{tag}"

    @classmethod
    def register(cls, custom_tag: str = None) -> Callable:
        def decorator(registree: Callable) -> Callable:
            # create namespace isolated tag using either custom tag or default tag
            tag = custom_tag if custom_tag else cls.default_tag(registree)
            tag = cls.canonicalize(tag)

            assert tag not in cls.registry, f"Duplicate tag registration found! Tag {tag} has already been registered"

            cls.registry[tag] = registree
            return registree
        return decorator

    @classmethod
    def create(cls, tag: str, *args: Any, **kwargs: Any) -> Any:
        tag = cls.canonicalize(tag)
        if tag in cls.registry:
            return cls.registry[tag](*args, **kwargs)
        else:
            raise NotImplementedError(f"Tag {tag} is not registered in the namespace {cls.namespace()}")