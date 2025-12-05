# This file does not contain any tests, but serves as a template for future test files.

from all import RunnableTests

class MoreTests(RunnableTests):

    # def test_one_plus_one(self):
    #     ans = 1 + 1
    #     self.assertEqual(ans, 2)

    pass

# Run with:
# All tests    : calibre-customize -b calibre-plugin && calibre-debug -e tests/template_for_tests.py
# Specific test: calibre-customize -b calibre-plugin && calibre-debug -e tests/template_for_tests.py -- --method test_one_plus_one

if __name__ == "__main__":
    MoreTests.run_tests()

# Notes.
# 1. The file name is important and should end in _tests.py (because all.py only looks for tests in files of that name)
# 2. We need to import RunnableTests from all.py
# 3. There should only be one class of tests per file.
# 4. The name of the class for the tests is not important, but it should be based on RunnableTest
# 5. The names of the actual tests methods needs to start with test_ and just take self as a parameter.
# 6. The assertions should be called via self, eg, self.assertEqual
# 7. If we want to be able to call the tests directly, then we add the following, where MoreTests is the name of the class above.

# Note : These are guidelines or recommendations. It is not essential to follow them all exactly.
# For example, If 7 is not needed, then you can base your test on unittest.TestCase rather than RunnableTest. Also you could
# ignore rule 3.
