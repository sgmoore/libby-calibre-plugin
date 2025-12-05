# Test Routines relating to the search results especially with regards to sorting by series
#
# Motivation
# The Series Number/Reading Order is not a purely numeric value (as we can have values like 1,2 or
# 1-5), but we also don't want to exclude such books from the sorting (e.g. we would like to be 
# able to sort 1-5 before 6-10 etc). 
# The original solution to this was to use padding of the numerical value to ensure that a pure
# alphabetical sort would produce results in the desirted order. However it was written with the
# assumption that the numeric value would never exceed two characters, but that assumption turned
# out to be incorrect (see the The Boxcar Children series which has more than 150 books in the 
# series and hence was not sorted correctly).
# We now assume that the there will never be more than 999 books in a series, but a test was 
# added to test that assumption.

# The tests are performed on a predefine dictionary which was based on some real results, but
# amended to cover other possible values.
# It also tests some real results which are included in the repo.
# Finally it tests all search results which have been saved in the search results folder.


import os
import json

from typing import Dict , TYPE_CHECKING
from re import sub, IGNORECASE
from os.path import dirname

if TYPE_CHECKING:
    from models import unsafe_get_series, get_waitdays_description
    from dialog.advanced_search import getSearchResultsFolder   
else :    
    from calibre_plugins.overdrive_libby.models import unsafe_get_series , get_waitdays_description                     
    from calibre_plugins.overdrive_libby.dialog.advanced_search import getSearchResultsFolder   

from all import RunnableTests

class Search_results(RunnableTests):
    
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
            book["series"]          = entry["series_name"]
            book["detailedSeries"]  = ds
            ds["seriesName"]        = entry["series_name"]
            ds["readingOrder"]      = entry["index"]

            result = unsafe_get_series(book, False) 
            self.assertEqual(result, entry["description"])

    def test_sorting_of_sample_series(self) :
        list = self.get_sample_series_dict()
        sorted_list = sorted(list , key=lambda d: d['description'])

        self.assertEqual(sorted_list, list)


    # Iterator to go through all json files in the specified folder 
    # and return the filename and the json data
    def get_all_search_results_iterator(self, folder):
        for filename in os.listdir(folder) :
            if filename.lower().endswith('.json') :

                filename = os.path.join(folder ,filename)
                with open(filename, 'r') as file:
                    data = json.load(file)         
                
                yield filename, data
    
    def test_details_in_example_search_results(self) :
        self._check_details_for_results_in_folder(dirname(__file__))

    def test_sorting_by_series_in_example_search_results(self) :
        self._check_sorting_by_series_for_results_in_folder(dirname(__file__))

    def test_sorting_by_waitdays_in_example_search_results(self) :
        self._check_sorting_by_waitdays_for_results_in_folder(dirname(__file__))



    # Now go through and test all the user's saved search results 
    def test_all_saved_search_results(self):
        self._check_details_for_results_in_folder(getSearchResultsFolder())

    def test_sorting_by_series_for_all_saved_search_results(self):
        self._check_sorting_by_series_for_results_in_folder(getSearchResultsFolder())

    def test_sorting_by_waitdays_for_all_saved_search_results(self):
        self._check_sorting_by_waitdays_for_results_in_folder(getSearchResultsFolder())


    def _check_sorting_by_series_for_results_in_folder(self, folder_path) :
        iterator = self.get_all_search_results_iterator(folder_path)

        for filename, data in iterator:
            self.filename = filename 
            self._check_results_are_sorted_by_series_correctly(data)

    def _check_sorting_by_waitdays_for_results_in_folder(self, folder_path) :
        iterator = self.get_all_search_results_iterator(folder_path)

        for filename, data in iterator:
            self.filename = filename 
            self._check_results_are_sorted_by_waitdays_correctly(data)
 

    def _check_details_for_results_in_folder(self, folder_path) :
        iterator = self.get_all_search_results_iterator(folder_path)

        for filename, data in iterator:
            self.filename = filename 
            self.check_details(data)


    def check_details(self, data : Dict) :
        list = data["Results"]
        for book in list:
            self._check_book(book)

    def _check_book(self, book : Dict) :

        seriesName = ""
        seriesNo = ""
        try :
            self.title  = book.get("title")
            self.author = book.get("firstCreatorName")
            seriesName  = book.get("series") 
            ds = book.get("detailedSeries")
            if (ds is not None) :
                seriesNo   = ds.get("readingOrder")
            
            if self.title is None or len(self.title) == 0 :
                self.assertFalse(f"all books should have a title but at least one is missing from {self.filename}")

            if self.author is None or len(self.author) == 0 :
                self.assertFalse(f"all books should have an author but {self.title} in {self.filename} has none")

            currentBookDescription = f"{self.title} by {self.author} in {self.filename}"

            seriesDescription = unsafe_get_series(book, False) 
            if seriesDescription is None :
                self.assertFalse(f"Series description should not be None but is for {currentBookDescription} ")

            if seriesName is not None and len(seriesName) != 0 :
                self.assertTrue(len(seriesDescription) > 0, f"Book has series so should have a series description in {currentBookDescription}" )

      

        except Exception as e2:
            self.fail(f"Error processing {self.title} by {self.author} in {self.filename}: {e2} : {seriesName} : {seriesNo} :")
            # self.dump_book(book)
            
    # def dump_book(self, book : Dict ) :
    #     import json
    #     jsonStr = json.dumps(book, indent=4)
    #     print(jsonStr)
    #     print("")

    def quote(self, s : str, padding : int ) : 
        q = "'"
        return (q + s + q).ljust(padding)

    def getBookDetails(self, book : Dict) :
        if book is None :
            return "(None)"
        
        seriesName = ""
        readingOrder = ""
        ds = book.get("detailedSeries")
        if ds is not None :                       
            seriesName = ds.get("seriesName", "").strip()
            readingOrder = ds.get("readingOrder", "")

        return (self.quote(book.get("title", "")            , 40) + " : " + 
                self.quote(seriesName                       , 20) + " : " + 
                self.quote(readingOrder                     , 10) + " : " + 
                self.quote(book.get('seriesDescription',"") , 40))



    def _check_results_are_sorted_by_series_correctly(self, data : Dict) :
        # Given a list of books, calculate the seriesDescription for each
        # book and then sort the list by this description.
        # Then iterate through each book and check that each series Name
        # and series number is greater than or equal to the previous entry
        
        # If the series number has more than one value we just check the first value

        list = data["Results"]
        for book in list:
            book['seriesDescription'] = unsafe_get_series(book, False) 

        sorted_list = sorted(list , key=lambda d: d['seriesDescription'])
        lastBook = dict()
        lastSeriesName = ""
        lastSeriesNo = 0
        for book in sorted_list :
            seriesName = ""
            seriesNo = 0
            readingOrder = ""
            ds = book.get("detailedSeries")
            if ds is not None :                       
                seriesName = ds.get("seriesName", "").strip()
                readingOrder = ds.get("readingOrder", "")

                if readingOrder != '' and not readingOrder[0].isdigit() :
                    readingOrder = sub(r'Book |Volume ', '', readingOrder, flags=IGNORECASE)
   
                leading_numbers = ''

                for char in readingOrder:
                    if char.isdigit() or char == '.':
                        leading_numbers += char
                    else:
                        break
                if (leading_numbers != '') :
                    seriesNo = float(leading_numbers)

            if (seriesName != lastSeriesName) :
                lastSeriesNo = 0

          #  print(book['title'] + " " + seriesName + " " + str(seriesNo) + " vs " + lastSeriesName + " " + str(lastSeriesNo), flush=True)

            self.assertGreaterEqual(seriesName , lastSeriesName, "Wrong order for Series Name " + 
                                             "\r\nPrevious Book = " + self.getBookDetails(lastBook)  +
                                             "\r\nCurrent Book  = " + self.getBookDetails(book)  +
                                             "\r\nIn file " + self.filename)


            self.assertGreaterEqual(seriesNo , lastSeriesNo, "Wrong order for Series No " + readingOrder +  
                                             "\r\nPrevious Book = " + self.getBookDetails(lastBook)  +
                                             "\r\nCurrent Book  = " + self.getBookDetails(book)  +
                                             "\r\nIn file " + self.filename) 

            lastSeriesName = seriesName
            lastSeriesNo = seriesNo
            lastBook = book

    def _check_results_are_sorted_by_waitdays_correctly(self, data : Dict) :
        # Given a list of books, calculate the waitDays for each book and then sort the list by this value 
        # Then iterate through each book and check that each waitdays is greater than or equal to the previous entry
        
        list = data["Results"]
        for book in list:
            book['waitDaysSortDescription'] = get_waitdays_description(book, True)

        sorted_list = sorted(list , key=lambda d: d['waitDaysSortDescription'])
        lastBook = dict()

        lastWaitDays = 0 
        for book in sorted_list :
            waitDaysSortDescription = book['waitDaysSortDescription']

            waitdays = 0 if waitDaysSortDescription == "" else int(waitDaysSortDescription)
         
            self.assertGreaterEqual(waitdays , lastWaitDays, "Wrong order for waitDays " +  
                                             f"\r\nPrevious Book = {self.getBookDetails(lastBook)} {lastWaitDays}"  + 
                                             f"\r\nCurrent  Book = {self.getBookDetails(book)} {waitdays}"  +
                                             "\r\nIn file " + self.filename) 

            lastWaitDays = waitdays
            lastBook = book

if __name__ == "__main__":
    Search_results.run_tests()   
 