# This file is used for logging and tries to redact (remove or mask) sensitive data
#
# Note library names are not redacted.


import ast
import json
import logging
import re
import copy
import sys
from http.client import HTTPMessage
from urllib.request import Request
from typing import List, Dict, Any, Optional



from calibre.constants import DEBUG as CALIBRE_DEBUG
from calibre.utils.logging import Log, DEBUG as LOGGING_DEBUG

from .. import PLUGIN_NAME, __version__
from .CalibreLogHandler import CalibreLogHandler

from .decorators import enforce_types
from .pretty_print import pp 
from ..compat import RedactableTypes , RedactableHeaders


class classproperty(property):
    def __get__(self, instance, cls):
        return self.fget(cls)

    def __set__(self, instance, value):
        raise AttributeError("Cannot set classproperty")

    def __delete__(self, instance):
        raise AttributeError("Cannot delete classproperty")


def static_init(cls):
    # print(f"{cls.__name__} static init")
    name = f"CL-calibre_plugins.{PLUGIN_NAME}"

    cls.logger = logging.getLogger(name)
            
    cls.ch = CalibreLogHandler(Log(LOGGING_DEBUG))


    cls.ch.setLevel(logging.DEBUG)
    cls.ch.setFormatter(
        logging.Formatter(
            f'[{PLUGIN_NAME}/{".".join([str(d) for d in __version__])}] %(message)s'
        )
    )
    cls.logger.addHandler(cls.ch)
    cls.logger.setLevel(logging.INFO if not CALIBRE_DEBUG else logging.DEBUG)
    
    # cls.logger.debug(f"Created CreateCustomLogger by calling logging.getLogger({name})")  
    
    return cls

@static_init
class CustomLogger:
    logger : logging.Logger 
    ch : CalibreLogHandler 
 
  
    @staticmethod
    def log_simple_string(input : str):
        if CustomLogger.logger.level <= logging.DEBUG: 
            CustomLogger.logger.debug(Redactor._redact_simple_string(input))

    @staticmethod
    def log_response(decoded_res , prefix = None) -> None :
        # decoded_res is the response (after decoding if it has been gziped).
        # This should be json so if we are logging this to file then we look for and redact any sensitive data.

        if CustomLogger.logger.level > logging.DEBUG: 
            return

        if prefix is None: 
            prefix = Redactor._get_original_caller()

        # try:
        #     data = json.loads(decoded_res)
        # except Exception as e:
        #     CustomLogger.logger.error(f"{prefix} log_response : Error loading json response : Type of decoded_res = {type(decoded_res)}  {e}")
        #     return 

        Redactor._redact_and_log(decoded_res, prefix)
 
    @staticmethod
    @enforce_types
    def log_and_format(input : Any , prefix : Optional[str] = None) -> None :
        if CustomLogger.logger.level > logging.DEBUG: 
            return

        if prefix is None: 
            prefix = Redactor._get_original_caller()

        Redactor._redact_and_log (input, prefix)

 

    @staticmethod
    @enforce_types
    def log_request(req : Request , endpoint_url : str , data : Optional[bytes]) -> None :
        if CustomLogger.logger.level > logging.DEBUG: 
            return

        CustomLogger.log_simple_string(f"REQUEST: {req.get_method()} {endpoint_url}\n")
        Redactor._redact_and_log_headers(req.headers, "REQ HEADERS")    

        if data:
            Redactor._redact_and_log(data , "REQ BODY:")

    @staticmethod
    def log_response_headers(response) -> None :
        if CustomLogger.logger.level > logging.DEBUG: 
            return

        CustomLogger.log_simple_string(f"RESPONSE: {response.code} {response.url}")

        Redactor._redact_and_log_headers(response.info() , "RES HEADERS")    




# this doesn't guarantee that sensitive data will be redacted fully # it's just a best effort attempt

_scrub_sensitive_data = True

class Redactor:
    # Not entirely sure how sensitive the card ids are, but persumably they are related to library card 
    # numbers and hence we try to redact them. The difficultly is they appear as values against card_id
    # which is easily handled, but also the card_id's are uses as keys in the summary which means we 
    # need to keep a record of these ids and masked as keys that used them.
    card_ids : List[str] = []
 
    # Most of the functions are only called from CustomLogger or from Redactor itself.
    # Exception are redact_sensitive_data_as_json which is called when we save the search
    # results to json file and redact_simple_string


    @staticmethod
    def redact_sensitive_data_as_json(data , prefix=None , isTest = False) :
        if prefix is None: 
            prefix = Redactor._get_original_caller()

        redacted = Redactor._redact_sensitive_data(data, prefix, isTest)
        return pp(redacted)
    
    @staticmethod
    @enforce_types
    def _redact_simple_string(input : str) -> str :
        def replace_keyword(match):
            word = match.group(0)
            return Redactor._mask_every_second_character(word)

        pattern = re.compile( r"\b(?:{})\b".format("|".join(map(re.escape, Redactor.card_ids))))

        transformed = pattern.sub(replace_keyword, input)
        return transformed
    

    @staticmethod
    @enforce_types
    def parse_bytes(input : bytes) -> Any :    
        return Redactor.parse_string(input.decode())
    
    @staticmethod
    @enforce_types
    def parse_string(input : str) -> Any :    
        # If the string input happens to be the string representation of a list or dict 
        # in either json format or 'python style' ast literal format, then we want to
        # convert it back to the original format.

        try : 
            obj = json.loads(input)
        except json.JSONDecodeError :
            try :
                obj = ast.literal_eval(input)
            except Exception : 
                return input    # Not either json or python style 

        if isinstance(obj, (dict, list)) :
            return obj
        return input


    @staticmethod
    def _mask_every_second_character(s):
        return ''.join(c if i % 2 == 0 else '*' for i, c in enumerate(s))


    @staticmethod
    def _rename_nested_keys(data, key_map):
        if isinstance(data, dict):
            # for k, v in data.items() :
            #     print (f"rename_nested_keys testing dict {k} ")
            return {
                key_map.get(k, k): Redactor._rename_nested_keys(v, key_map)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            # for item in data :
            #     print (f"rename_nested_keys testing list {item} ")
            return [Redactor._rename_nested_keys(item, key_map) for item in data]
        else:
            # print (f"rename_nested_keys return data of type {type(data)}")
            return data
    
    @staticmethod
    def _redact_key(obj, target_key):
        if isinstance(obj, dict):

            for key in obj:
                if key.lower() == target_key.lower():
                    old_value = obj[key] 
                    # print(f"found {key}  {old_value} {len(old_value)}")
                    new_value = "*" * len(old_value)
                    obj[key] = new_value
                else:
                    Redactor._redact_key(obj[key], target_key)
        elif isinstance(obj, list):
            for item in obj:
                Redactor._redact_key(item, target_key)

    @staticmethod
    def _redact_token(obj, target_key):
        if isinstance(obj, dict):

            for key in obj:
                if key.lower() == target_key.lower():
                    bearer_token = obj[key] 
                    #print(f"found {key}  {bearer_token} {len(bearer_token)}")
                    prefixLen = len("Bearer ")
                    bearer_token = bearer_token[:prefixLen] + "*" * int(len(bearer_token[prefixLen :]) / 10)
                    obj[key] = bearer_token
                else:
                    Redactor._redact_token(obj[key], target_key)
        elif isinstance(obj, list):
            for item in obj:
                Redactor._redact_token(item, target_key)

    @staticmethod
    def _mask_key(obj, target_key):
        if isinstance(obj, dict):

            for key in obj:
                if key.lower() == target_key.lower():
                    old_value = obj[key] 
                    #print(f"found {key}  {old_value} {len(old_value)}")
                    new_value = Redactor._mask_every_second_character(old_value) 
                    obj[key] = new_value
                else:
                    Redactor._mask_key(obj[key], target_key)
        elif isinstance(obj, list):
            for item in obj:
                Redactor._mask_key(item, target_key)                

    @staticmethod
    def _replace_preserve_length(text, prefix):
        def _replacer(match):
            original_line = match.group()
            new_prefix = prefix
            num_x = len(original_line) - len(new_prefix)
            return new_prefix + ("x" * num_x)

        pattern = rf"^{prefix}.*" 
        return re.sub(pattern, _replacer, text, flags=re.MULTILINE)

   

    @staticmethod
    def _get_original_caller() :
        return sys._getframe(2).f_code.co_name    # frame(0) is this function; 
                                                  # frame(1) is the caller (eg redact_dict)
                                                  # frame(2) is the original caller (eg the test)




  
 
    @staticmethod
    @enforce_types
    def _redact_sensitive_data(data : RedactableTypes , prefix : str, isTest : bool = False) -> RedactableTypes :
        # Data should be redacted of sensitive data.
        # if data is the string representation of a list or dict, then we should convert it back to allow
        # us to parse and then redact information.
        # Note, this is not just used for logging, so ignore logger.level
        
        if _scrub_sensitive_data :
            if isinstance(data, str):
                data = Redactor.parse_string(data)
            elif isinstance(data, bytes) :
                data = Redactor.parse_bytes(data)
            else :
                data = copy.deepcopy(data)  # we need to make sure we do not change the original dict, list, etc

            if isinstance(data, str):
                return Redactor._redact_simple_string(data)

            if not isinstance(data, (dict, list, HTTPMessage)):
                CustomLogger.logger.warning(f"{prefix} : Starting redact_sensitive_data on data of Type  = {type(data).__name__}")
                if isTest :
                    raise TypeError(f"{prefix} :  redact_sensitive_data is not support with data of type = {type(data).__name__}") 
            
            try:
                if isinstance(data, Dict) and ("summary" in data) :
                    print(f"summary found in data of type {type(data)}")
                    summary = data["summary"]
                    # CustomLogger.logger.debug(f"summary is {type(summary)}")
                    for card_id in summary :
                        Redactor.card_ids.append(card_id)
                else :
                    # print("summary not found in data")
                    pass


                # The values for these keys are removed and replaced by asteriks with the same length

                Redactor._redact_key(data, "identity"     )
                Redactor._redact_key(data, "emailAddress" )
                Redactor._redact_key(data, "email"        )
                Redactor._redact_key(data, "bearer"       )

                # The Authorization is also removed and replace by asteriks, but with only one-tenth the original length

                Redactor._redact_token(data, "Authorization")
                

                # The value for the following keys are masked, ie every second character is replaced by an asterisk.
                # For people who have more than one library card, sometimes we need to be able to distingush between cards.
                # Similar to credit cards showing the last four digits.

                Redactor._mask_key(data, "username"       )
                Redactor._mask_key(data, "cardName"       )
                Redactor._mask_key(data, "cardId"         )     

                # we also need to mask some card_ids which are used as keys rather than values.
                key_map =  {}
                for card_id in Redactor.card_ids :
                   key_map[card_id] = Redactor._mask_every_second_character(card_id)                  

                data = Redactor._rename_nested_keys(data, key_map)
                           
            except Exception as e:
                CustomLogger.logger.error("%s: Error redacting data : %s" , prefix, str(e))                
                pass
        else:
            CustomLogger.logger.warning("%s: WARNING : data is not redacted of Sensitive Data ",prefix )
            
        return data


    @staticmethod
    @enforce_types
    def _redact_and_log(data : Any , prefix : str) -> None :
        if CustomLogger.logger.level > logging.DEBUG: 
            return 
        
        if _scrub_sensitive_data :
            try:
                redacted = Redactor.redact_sensitive_data_as_json(data, prefix)
               
                CustomLogger.logger.debug("%s\n%s\n", prefix , redacted )            
            except Exception as e:
                CustomLogger.logger.error("%s: Error redacting data : %s" , prefix, str(e))                
                pass
        else:
            CustomLogger.logger.debug("%s: WARNING : May contain Sensitive Data\n%s\n",prefix,  data)            

    @staticmethod
    @enforce_types
    def _redact_and_log_headers(headers : RedactableHeaders , prefix : str) -> None :
        clone = Redactor._redact_sensitive_data(headers, prefix)        
        details = "\n".join(f"{k}: {v}" for k, v in clone.items())
        CustomLogger.logger.debug(f"{prefix}: \n{details}\n")

                
