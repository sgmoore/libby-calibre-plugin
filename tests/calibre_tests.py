import logging
import sys
from typing import TYPE_CHECKING

from calibre_plugins.overdrive_libby import PLUGIN_NAME , __version__   # pyright: ignore[reportMissingImports]   
if TYPE_CHECKING :
    from tools.CustomLogger import CustomLogger 
    from tools.pretty_print import pp           
    from utils import rating_to_stars ,  generate_od_identifier , SimpleCache

else :
    from calibre_plugins.overdrive_libby.tools.CustomLogger import CustomLogger         
    from calibre_plugins.overdrive_libby.tools.pretty_print import pp                   
    from calibre_plugins.overdrive_libby.utils import rating_to_stars ,  generate_od_identifier , SimpleCache 

from all import RunnableTests

class _CalibreTests(RunnableTests):

    def test_rating_to_stars(self):

        self.assertEqual("★★★", rating_to_stars(3))
        self.assertEqual("★★★", rating_to_stars(3.2))
        self.assertEqual("★★★⯨", rating_to_stars(3.4))
        self.assertEqual("★★★⯨", rating_to_stars(3.6))

    def test_generate_od_identifier(self):

        self.assertEqual(
            "1234@abc.overdrive.com",
            generate_od_identifier({"id": "1234"}, {"preferredKey": "abc"}),
        )

    def test_simplecache(self):

        cache = SimpleCache(capacity=2)
        a = {"a": 1}
        b = {"b": 1}
        c = {"c": 1}
        cache.put("a", a)
        self.assertEqual(cache.count(), 1)
        self.assertEqual(cache.get("a"), a)
        cache.put("b", b)
        self.assertEqual(cache.count(), 2)
        self.assertEqual(cache.get("b"), b)
        cache.put("c", c)
        self.assertEqual(cache.count(), 2)
        self.assertIsNone(cache.get("a"))
        self.assertIsNotNone(cache.get("b"))
        self.assertIsNotNone(cache.get("c"))
        cache.clear()
        self.assertEqual(cache.count(), 0)


    def test__log_handler(self):    # FileName with two underscores means this may be run before other tests

        print("")   # This test outputs some details to stdout, so we add a few carriage returns 
        print("")   # to seperate the output of the test from the tests results
        logger = CustomLogger.logger

        logger.log(0, "\n\n******* ERROR **** You Should NOT see this message ******\n\n")

        logger.info("Format of standard logger output")
        CustomLogger.ch.setFormatter(
            logging.Formatter(f'[{PLUGIN_NAME}/{".".join([str(d) for d in __version__])}] %(levelname)-8s %(message)s')
        )
        logger.info("Format of custom logger output")
        print("")   
        msg = "Level %s"
        logger.debug(msg, logging.DEBUG)
        logger.info(msg, logging.INFO)
        logger.warning(msg, logging.WARNING)
        logger.error(msg, logging.ERROR)
        logger.critical(msg, logging.CRITICAL)
        try:
            1 / 0                                  # pyright: ignore[reportUnusedExpression]
        except:  # noqa
            logger.exception("Test divide by zero exception")
        print("")

        # Output the name of the test again so the status is more clearly associated with it.  

        method_name = sys._getframe(0).f_code.co_name
        print(f"{method_name} ({__name__}.{__class__.__name__}.{method_name})" , end = " ... ", flush=True)

        level_name = logging.getLevelName(logger.level) 

        self.assertGreater(logger.level, 0 , f"Logger level {level_name} should be greater than 0")

   

# Run with:
# All tests: calibre-customize -b calibre-plugin && calibre-debug -e tests/calibre_tests.py
# Specific test: calibre-customize -b calibre-plugin && calibre-debug -e tests/calibre_tests.py -- --method test__log_handler
if __name__ == "__main__":
    _CalibreTests.run_tests()

