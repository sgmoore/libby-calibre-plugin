
from typing import TYPE_CHECKING
from urllib.parse import urlencode

if TYPE_CHECKING :
    from tools.CustomLogger import Redactor  
    from libby.client import LibbyClient  
else :
    from calibre_plugins.overdrive_libby.tools.CustomLogger import Redactor  
    from calibre_plugins.overdrive_libby.libby.client import LibbyClient  

from all import RunnableTests

fake_token = '''Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjbGFpbTEiOjAsImNsYWltMiI6IkxvcmVtIGlwc3VtIGRvbG9yIHNpdCBhbWV0LCBjb25zZWN0ZXR1ciBhZGlwaXNjaW5nIGVsaXQsIHNlZCBkbyBlaXVzbW9kIHRlbXBvciBpbmNpZGlkdW50IHV0IGxhYm9yZSBldCBkb2xvcmUgbWFnbmEgYWxpcXVhLiBVdCBlbmltIGFkIG1pbmltIHZlbmlhbSwgcXVpcyBub3N0cnVkIGV4ZXJjaXRhdGlvbiB1bGxhbWNvIGxhYm9yaXMgbmlzaSB1dCBhbGlxdWlwIGV4IGVhIGNvbW1vZG8gY29uc2VxdWF0LiBEdWlzIGF1dGUgaXJ1cmUgZG9sb3IgaW4gcmVwcmVoZW5kZXJpdCBpbiB2b2x1cHRhdGUgdmVsaXQgZXNzZSBjaWxsdW0gZG9sb3JlIGV1IGZ1Z2lhdCBudWxsYSBwYXJpYXR1ci4gRXhjZXB0ZXVyIHNpbnQgb2NjYWVjYXQgY3VwaWRhdGF0IG5vbiBwcm9pZGVudCwgc3VudCBpbiBjdWxwYSBxdWkgb2ZmaWNpYSBkZXNlcnVudCBtb2xsaXQgYW5pbSBpZCBlc3QgbGFib3J1bS4gU2VkIHV0IHBlcnNwaWNpYXRpcyB1bmRlIG9tbmlzIGlzdGUgbmF0dXMgZXJyb3Igc2l0IHZvbHVwdGF0ZW0gYWNjdXNhbnRpdW0gZG9sb3JlbXF1ZSBsYXVkYW50aXVtLCB0b3RhbSByZW0gYXBlcmlhbS4gRWFxdWUgaXBzYSBxdWFlIGFiIGlsbG8gaW52ZW50b3JlIHZlcml0YXRpcyBldCBxdWFzaSBhcmNoaXRlY3RvIGJlYXRhZSB2aXRhZSBkaWN0YSBzdW50IGV4cGxpY2Fiby4ifQ.wqJ2Vs_zrehRnSUvRztmjXQzSGtvWTaG72AjesQ6gdc''' #gitleaks:allow

# Tests relating to Redacting

class RedactorTests(RunnableTests):

    
    # def test_redact_string(self) :
    #     redacted = Redactor.redact_str("test"                ) 
    #     self.assertEqual(redacted, "test")
    #     redacted = Redactor.redact_str("Bearer=1234567890"   ) 
    #     self.assertEqual(redacted, "Bearer=*********")

    def test_redact_dict(self) :
      
        data  = dict()
        data["series"] = "Series"
        data["title"] = "Title"
        data["email"] = "test@example.com"   #gitleaks:allow
        data["Bearer"] = "12345678"
        data["Authorization"] = f"{fake_token}"

        redacted = Redactor.redact_sensitive_data_as_json(data) 
        shouldbe = '''{
    "series":"Series",
    "title":"Title",
    "email":"****************",
    "Bearer":"********",
    "Authorization":"Bearer ***************************************************************************************************"
}'''
        self.assertEqual(redacted, shouldbe)

        # Just confirm that the original data dictionary has not been changed
        self.assertEqual(data["Authorization"] , f"{fake_token}" , "Original headers should NOT be changed")

    def test_redact_list(self) :

        list = []

        list.append(  dict(title = "Title"))
        list.append(  dict(email = "test@example.com"))  #gitleaks:allow
        list.append(  dict(Authorization = f"{fake_token}"))

        redacted = Redactor.redact_sensitive_data_as_json(list) 
        shouldbe = '''[
    {
        "title":"Title"
    },
    {
        "email":"****************"
    },
    {
        "Authorization":"Bearer ***************************************************************************************************"
    }
]'''    
       
        self.assertEqual(redacted, shouldbe)
        self.assertEqual(list[2]["Authorization"] , f"{fake_token}" , "Original headers should NOT be changed" )

    def test_redact_headers(self) :

        
        token = ""
        try:
            # token = os.environ["LIBBY_TEST_TOKEN"]
            pass
        except KeyError:
            pass
        client = LibbyClient(
            identity_token=token,
            max_retries=0,
            timeout=15,
        )

        headers = client.default_headers()
        headers["Authorization"] = f"{fake_token}"

        redacted = Redactor.redact_sensitive_data_as_json(headers ) 

        shouldbe = '''{
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15",
    "Accept":"application/json",
    "Accept-Encoding":"gzip",
    "Referer":"https://libbyapp.com/",
    "Cache-Control":"no-cache",
    "Pragma":"no-cache",
    "Authorization":"Bearer ***************************************************************************************************"
}'''
        self.assertEqual(redacted, shouldbe)
        self.assertEqual(headers["Authorization"] , f"{fake_token}" , "Original headers should NOT be changed")

    def test_redact_form(self) :
        params={"days_to_suspend": 0, "email_address": ""}
        shouldbe = urlencode(params)
        data = shouldbe.encode("ascii")
        redacted = Redactor.redact_sensitive_data_as_json(data)

        self.assertEqual(redacted, shouldbe)

    def test_parse_bytes(self) :
        params={"days_to_suspend": 0, "email_address": ""}
        data = urlencode(params).encode("ascii")
        parsed = Redactor.parse_bytes(data)

        self.assertEqual(parsed, "days_to_suspend=0&email_address=")
        

if __name__ == "__main__":
    RedactorTests.run_tests()
