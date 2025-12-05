import traceback
import sys
from functools import wraps
from inspect import signature
from typing import Any
from .guiMode import GuiMode

def enforce_types(func):
   
    if sys.version_info >= (3, 10):
        sig = signature(func)
        return_type = func.__annotations__.get('return')
    
        @wraps(func)
        def wrapper(*args, **kwargs):
      
            bound_args = sig.bind(*args, **kwargs)
            for name, value in bound_args.arguments.items():
                expected_type = func.__annotations__.get(name)
                if expected_type and not expected_type == Any and not isinstance(value, expected_type):
                    display_error(f"Argument '{name}' must be {expected_type}, got {type(value)} ({value})")
            result = func(*args, **kwargs)

            if return_type and not return_type == Any and return_type is not None and not isinstance(result, return_type):
                display_error(f"Return value must be {return_type}, got {type(result)} ({result})")
            elif return_type is None and result is not None :
                display_error(f"Expected no return value, but got {type(result)} ({result})")
            return result        
       
        return wrapper
    else :
        return func 



def display_error(message : str) :
    if GuiMode.IsAvailable :
        stack_trace = ''.join(traceback.format_stack())

        print(f"RunTime Validation failure {message}\r\n at {stack_trace}" )
    else :
       raise TypeError(message)


    

    
