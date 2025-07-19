import logging
import sys
import unittest

from calibre.gui2 import ensure_app, destroy_app
from calibre_plugins.overdrive_libby.models import unsafe_get_series
from calibre_plugins.overdrive_libby.dialog.advanced_search import getSearchResultsFolder
from search_results import search_results
from os.path import dirname


class CalibreTests(unittest.TestCase):

    def test_rating_to_stars(self):
        from calibre_plugins.overdrive_libby.utils import rating_to_stars

        self.assertEqual("★★★", rating_to_stars(3))
        self.assertEqual("★★★", rating_to_stars(3.2))
        self.assertEqual("★★★⯨", rating_to_stars(3.4))
        self.assertEqual("★★★⯨", rating_to_stars(3.6))

    def test_generate_od_identifier(self):
        from calibre_plugins.overdrive_libby.utils import generate_od_identifier

        self.assertEqual(
            "1234@abc.overdrive.com",
            generate_od_identifier({"id": "1234"}, {"preferredKey": "abc"}),
        )

    def test_simplecache(self):
        from calibre_plugins.overdrive_libby.utils import SimpleCache

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

    # def test_truncate_for_display1(self):
    #     from calibre_plugins.overdrive_libby.models import truncate_for_display

    #     from calibre.utils.logging import Log, DEBUG
    #     from calibre_plugins.overdrive_libby.utils import create_job_logger

    #     logger: logging.Logger = create_job_logger(Log(DEBUG))

    #     logger.debug("")
    #     source = "Ipsum debitis dignissimos aspernatur."
    #     for i in range(1 , 30) :
    #         xxx = truncate_for_display(source, i)
    #         yyy = source[:i-2] + "…"

    #         if (xxx != yyy) :
    #             logger.error(f"Length = {i} Lengths= Got {len(xxx)} vs Expected {len(yyy)} got {xxx} vs {yyy}")
    #         # else :
    #         #     logger.debug(f"Length = {i} Lengths= Got {len(xxx)} vs Expected {len(yyy)} got {xxx} vs {yyy}")
    #         # self.assertEqual( yyy , xxx , i)

    # def test_truncate_for_display(self):
    #     from calibre_plugins.overdrive_libby.models import truncate_for_display

    #     # original = "Ipsum debitis dignissimos aspernatur." 
    #     # xxx = truncate_for_display(original)

    #     # ellipsis = '…'

    #     # # self.assertEqual( xxx, original[0 : len(xxx)-1] + ellipsis)
    #     # # self.assertEqual( "xxx", xxx)

    #     # xxx = truncate_for_display("Ipsum debitis dignissimos aspernatur.", 30, 210)
    #     # yyy = truncate_for_display(xxx+xxx , 30)
    #     # self.assertEqual( yyy, xxx)
    #     # self.assertEqual( "xxx", xxx)

    #     self.assertEqual(
    #         "Ipsum debitis dignissimo…",
    #         truncate_for_display("Ipsum debitis dignissimos aspernatur.", 24),
    #     )
    #     self.assertEqual(
    #         "Ipsum debitis dignissimo…",
    #         truncate_for_display("Ipsum debitis dignissimos aspernatur.", width=-100),
    #     )
    #     self.assertEqual(
    #         "Ipsum debitis dignissimo…",
    #         truncate_for_display(
    #             "Ipsum debitis dignissimos aspernatur.", text_length=-1
    #         ),
    #     )
    #     self.assertEqual(
    #         "Ipsum debitis d…",
    #         truncate_for_display(
    #             "Ipsum debitis dignissimos aspernatur.", text_length=20
    #         ),
    #     )

    def test_log_handler(self):
        from calibre.utils.logging import Log, DEBUG
        from calibre_plugins.overdrive_libby.utils import create_job_logger

        logger: logging.Logger = create_job_logger(Log(DEBUG))
        msg = "Level %s"
        logger.debug(msg, logging.DEBUG)
        logger.info(msg, logging.INFO)
        logger.warning(msg, logging.WARNING)
        logger.error(msg, logging.ERROR)
        logger.critical(msg, logging.CRITICAL)
        try:
            1 / 0
        except:  # noqa
            logger.exception("Test divide by zero exception")

    # test the sample series  

    def get_sample_series_dict(self) :

        # Data started from real series, but then modified 

        # series_name and index are the source data
        # description is the expected output from unsafe_get_series

        # Extra entries should be added to the list in the correct order

        list = []
        seriesName = "The Boxcar Children"
        list.append(  dict(series_name = seriesName , index=''              , description = "The Boxcar Children"        ))
        list.append(  dict(series_name = seriesName , index='.4'            , description = "The Boxcar Children   0.4 " ))
        list.append(  dict(series_name = seriesName , index='0.5'           , description = "The Boxcar Children   0.5 " ))
        list.append(  dict(series_name = seriesName , index='1'             , description = "The Boxcar Children   1   " ))
        list.append(  dict(series_name = seriesName , index='1,2'           , description = "The Boxcar Children   1,2 " ))
        list.append(  dict(series_name = seriesName , index='1-5'           , description = "The Boxcar Children   1-5 " ))
        list.append(  dict(series_name = seriesName , index='1.5'           , description = "The Boxcar Children   1.5 " ))
        list.append(  dict(series_name = seriesName , index='2'             , description = "The Boxcar Children   2   " ))
        list.append(  dict(series_name = seriesName , index='10'            , description = "The Boxcar Children  10   " ))
        list.append(  dict(series_name = seriesName , index='11'            , description = "The Boxcar Children  11   " ))
        list.append(  dict(series_name = seriesName , index='100'           , description = "The Boxcar Children 100   " ))
        list.append(  dict(series_name = seriesName , index='Book 101'      , description = "The Boxcar Children 101   " ))
        list.append(  dict(series_name = seriesName , index='Volume 102'    , description = "The Boxcar Children 102   " ))
        list.append(  dict(series_name = seriesName , index='103'           , description = "The Boxcar Children 103   " ))

        return list

    def test_details_in_sample_series(self):

        list = self.get_sample_series_dict()

        for entry in list :
            # Construct a dummy book entry
            book = dict()
            ds = dict()
            book["series"] = entry["series_name"]
            book["detailedSeries"] = ds
            ds["seriesName"]   = entry["series_name"]
            ds["readingOrder"] = entry["index"]

            result = unsafe_get_series(book, False) 
            self.assertEqual(result, entry["description"])

    def test_sorting_of_sample_series(self) :
        list = self.get_sample_series_dict()
        sorted_list = sorted(list , key=lambda d: d['description'])

        self.assertEqual(sorted_list, list)

    # Several example search results files are included, so go through and test all these.

    def test_details_in_example_search_results(self) :
        sr = search_results(self)
        sr.test_details_for_results_in_folder(dirname(__file__))

    def test_sorting_by_series_in_example_search_results(self) :
        sr = search_results(self)
        sr.test_sorting_for_results_in_folder(dirname(__file__))


    # Now go through and test all the user's saved search results 
    def test_all_saved_search_results(self):
        sr = search_results(self)
        sr.test_details_for_results_in_folder(getSearchResultsFolder())

    def test_sorting_by_series_for_all_saved_search_results(self):
        sr = search_results(self)
        sr.test_sorting_for_results_in_folder(getSearchResultsFolder())


# Run with:
# All tests: calibre-customize -b calibre-plugin && calibre-debug -e tests/calibre.py
# Specific test: calibre-customize -b calibre-plugin && calibre-debug -e tests/calibre.py -- --method test_log_handler
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--methods", nargs="*")
    args = parser.parse_args()

    try:
        ensure_app()
        tests = [
            test
            for test in unittest.makeSuite(CalibreTests)
            if not args.methods or test.id().split(".")[-1] in args.methods
        ]
        suite = unittest.TestSuite(tests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)

        if not result.wasSuccessful():
            sys.exit(1)
    finally:
        destroy_app()
