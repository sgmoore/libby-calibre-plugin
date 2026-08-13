from .decorators import enforce_types

from typing import Any


class Error(Exception):
    """Generic error ."""
    def __init__(self, msg: str) -> None:
        super().__init__(msg)

    @staticmethod
    @enforce_types
    def RaiseIf(condition: Any, msg: str) -> None:
        if condition:
            raise Error(msg)
        
    @staticmethod
    @enforce_types
    def RaiseIfNot(condition: Any, msg: str) -> None:
       if not condition:
            raise Error(msg)
              
    @staticmethod
    @enforce_types
    def Raise(msg: str) -> None:
        raise Error(msg)
