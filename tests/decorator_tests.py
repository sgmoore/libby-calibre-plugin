# This file does not contain any tests, but serves as a template for future test files.

from typing import Dict , TYPE_CHECKING
from all import RunnableTests
from urllib.request import Request

if TYPE_CHECKING :
    from tools.decorators   import enforce_types   
    from tools.CustomLogger  import CustomLogger   
    from libby.client        import LibbyClient  
else :    
    from calibre_plugins.overdrive_libby.tools.decorators   import enforce_types   
    from calibre_plugins.overdrive_libby.tools.CustomLogger import CustomLogger   
    from calibre_plugins.overdrive_libby.libby.client       import LibbyClient  


@enforce_types
def method(data: Dict, s : str , b : bool ) -> str : # type hints guide the decorator
    return s

@enforce_types
def method2(data: Dict, s : str , b : bool ) -> str :
    return True # pyright: ignore[reportReturnType]

def method3(data: Dict, s : str , b : bool ) -> str :
    return True # pyright: ignore[reportReturnType]

@enforce_types
def method4(data: Dict, s : str , b : bool ) -> None :
    return True # pyright: ignore[reportReturnType]

def method5(data: Dict, s : str , b : bool ) -> None :
    return True # pyright: ignore[reportReturnType]

class DecoratorTests(RunnableTests):

    def test_enforce_types(self):
        method({}, "Test", False)   # This should not fail as all the parameters are correct.

        with self.assertRaises(TypeError) as cm:
            method("Test", "Test", False)    # pyright: ignore[reportArgumentType]
        self.assertEqual(str(cm.exception), "Argument 'data' must be typing.Dict, got <class 'str'> (Test)")

        with self.assertRaises(TypeError) as cm:
            method({},  False, "Test")       # pyright: ignore[reportArgumentType]
        self.assertEqual(str(cm.exception), "Argument 's' must be <class 'str'>, got <class 'bool'> (False)")

        with self.assertRaises(TypeError) as cm:
            method({},  "Test" , "Test")       # pyright: ignore[reportArgumentType]
        self.assertEqual(str(cm.exception), "Argument 'b' must be <class 'bool'>, got <class 'str'> (Test)")
         
        with self.assertRaises(TypeError) as cm:
            method2({}, "Test", False)   
        self.assertEqual(str(cm.exception), "Return value must be <class 'str'>, got <class 'bool'> (True)")

        method3({}, "Test", False)   # This should not fail because the type hints are not enforced
        
        with self.assertRaises(TypeError) as cm:
            method4({}, "Test", False)   
        self.assertEqual(str(cm.exception),  "Expected no return value, but got <class 'bool'> (True)")
        
        method5({}, "Test", False)   # This should not fail because the type hints are not enforced

    def test_decorators_for_logging(self) :

        # Some of the logging methods work, but we are not interested in the output,  merely that they don't 
        # throw an error, so disable logging temporarily by setting the level to critical.
        storeLevel = CustomLogger.logger.level
        try :    
            import logging
            CustomLogger.logger.level = logging.CRITICAL    

            CustomLogger.log_and_format({})

            with self.assertRaises(TypeError) as cm:
                method("Test", "Test", False)          # pyright: ignore[reportArgumentType]
            self.assertEqual(str(cm.exception), "Argument 'data' must be typing.Dict, got <class 'str'> (Test)")
        
            client = LibbyClient()
            headers = client.default_headers()
            endpoint_url = "http://www.example.com"

            req = Request(endpoint_url, None, headers=headers)

            CustomLogger.log_request(req, endpoint_url , None  )
            with self.assertRaises(TypeError) as cm:
                CustomLogger.log_request("headers" , req , None)        # pyright: ignore[reportArgumentType]
            self.assertEqual(str(cm.exception), "Argument 'req' must be <class 'urllib.request.Request'>, got <class 'str'> (headers)")

            with self.assertRaises(TypeError) as cm:
                CustomLogger.log_request(None , endpoint_url, None)     # pyright: ignore[reportArgumentType]
            self.assertEqual(str(cm.exception), "Argument 'req' must be <class 'urllib.request.Request'>, got <class 'NoneType'> (None)")

            CustomLogger.log_and_format("{'name': 'Joe Bloggs'}")

        finally :
            CustomLogger.logger.level = storeLevel
        


# Run with:
# All tests    : calibre-customize -b calibre-plugin && calibre-debug -e tests/decorator_tests.py
# Specific test: calibre-customize -b calibre-plugin && calibre-debug -e tests/decorator_tests.py -- --method test_one_plus_one

if __name__ == "__main__":
    DecoratorTests.run_tests()
 