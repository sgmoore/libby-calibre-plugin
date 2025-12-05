from json import dumps, loads, JSONDecodeError
from typing import Any
import ast
from ..compat import StrOrAny

def pp(data : Any, prefix:str = "" , postfix:str = "" ) -> StrOrAny :
        
    data = _reformat(data)
    result = f"{prefix}{data}{postfix}"

    return result


def _reformat(input : Any ) -> StrOrAny :
    # if input is a string, then it may contain json but we still want to re-format it.
    # So try to load it as json and if it turns out to be a dict or list then reformat it by calling json.dumps.
    # If it is not json, it might be Python-style (not quite json) so trying load it via ast.literal_eval

    if isinstance(input, bytes) :
        input = input.decode()

    if isinstance(input , str) :
        try : 
            obj = loads(input)
        except JSONDecodeError :
            try :
                obj = ast.literal_eval(input)
            except Exception : 
                return input    # Not either json or python style 

        if isinstance(obj, (dict, list)) :
            input = obj
        else :
            print(f"calling pp on {type(obj)} from {input}")
            return input
       
    try : 
        data = dumps(input , separators=(",", ":") , indent=4) 
        return data
    except Exception as err :
        print (f"Calling pretty_print.pp on type {input} throws {err}" )        
        return input
  