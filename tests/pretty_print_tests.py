# This file does not contain any tests, but serves as a template for future test files.

from all import RunnableTests
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING :
    from tools.pretty_print import pp           
else :
    from calibre_plugins.overdrive_libby.tools.pretty_print import pp                   


class PrettyPrintTests(RunnableTests):

    fakeEmail = "test@example.com"      #gitleaks:allow

    def _get_sample_dict(self) -> Dict :
        data  = dict()
        data["series"] = "Series"
        data["title"] = "Title"
        data["email"] =  self.fakeEmail
        data["Bearer"] = "12345678"

        return data
    
    def _get_sample_result(self) -> str :
        return f'''{{
    "series":"Series",
    "title":"Title",
    "email":"{self.fakeEmail}",
    "Bearer":"12345678"
}}'''

    def test_pretty_print_string(self): 
        
        plainText = "Hello World"
        self.assertEqual(pp(plainText) , plainText ) 
        self.assertEqual(pp(plainText, "::" , "\n") , f'::{plainText}\n')


        data  = self._get_sample_dict()

        shouldbe =  self._get_sample_result()
        self.assertEqual(pp(data) , shouldbe )

        import re
        removeIndents = re.sub("[\r\n ]", "", shouldbe)
    
        self.assertEqual(pp(removeIndents) , shouldbe )

        self.assertEqual(pp(str(data)) , shouldbe )
 
    def test_pretty_print_ascii_bytes(self): 

        data  = self._get_sample_dict()
        shouldbe =  self._get_sample_result()
        bytes = pp(data).encode("ascii")
        self.assertEqual(pp(bytes) , shouldbe )
        bytes = pp(shouldbe).encode("ascii")
        self.assertEqual(pp(bytes) , shouldbe )

    def test_pretty_print_unicode_bytes(self): 
        data  = self._get_sample_dict()
        shouldbe =  self._get_sample_result()
        bytes = pp(data).encode()
        self.assertEqual(pp(bytes) , shouldbe )
        unicode = "café"
        bytes = pp(unicode).encode()
        self.assertEqual(pp(bytes) , unicode )


# Run with:
# All tests    : calibre-customize -b calibre-plugin && calibre-debug -e tests/pretty_print_tests.py
# Specific test: calibre-customize -b calibre-plugin && calibre-debug -e tests/pretty_print_tests.py -- --method test_pretty_print_string

if __name__ == "__main__":
    PrettyPrintTests.run_tests()
 