import argparse
import sys
import unittest

from calibre.gui2 import ensure_app, destroy_app
  

class RunnableTests(unittest.TestCase):
    
    @classmethod
    def run_tests(cls):  
        suite = unittest.makeSuite(cls)
        _run_tests_for_suite(suite)



def filter_suite(suite, predicate):
    """
    Yield every TestCase in `suite` for which predicate(test) is True.
    Recurses into nested TestSuites automatically.
    """
   
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from filter_suite(item, predicate)
        else:
            if predicate(item):
                yield item

    
def _run_tests_for_suite(suite : unittest.TestSuite) :

    parser = argparse.ArgumentParser()
    parser.add_argument("--methods", nargs="*")
    args = parser.parse_args()

    try:
        ensure_app()
        if args.methods : 
            tests = filter_suite(suite, lambda t: t.id().split(".")[-1] in args.methods)            
            suite = unittest.TestSuite(tests)

        result = unittest.TextTestRunner(verbosity=2).run(suite)

        if not result.wasSuccessful():
            sys.exit(1)
    finally:
        destroy_app()

# Run with:
# All tests    : calibre-customize -b calibre-plugin && calibre-debug -e tests/all.py
# Specific test: calibre-customize -b calibre-plugin && calibre-debug -e tests/all.py -- --method test_rating_to_stars

if __name__ == "__main__":

    # Load all the tests in any files in the current folder ending with _tests.py
    # Note - This deliberately excludes the tests in libby.py and overdrive.py

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover("tests", pattern="*_tests.py"))  
    _run_tests_for_suite(suite)        