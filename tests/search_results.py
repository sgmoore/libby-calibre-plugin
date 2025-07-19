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


import logging
import sys
import os
import json
import unittest

from typing import Dict
from re import sub, split, IGNORECASE

from calibre_plugins.overdrive_libby.models import unsafe_get_series



class search_results():
    def __init__(self, testcase : unittest.TestCase):
        self.testcase = testcase 

    # Iterator to go through all json files in the specified folder 
    # and return the filename and the json data
    def get_all_search_results_iterator(self, folder):
        for filename in os.listdir(folder) :
            if filename.lower().endswith('.json') :

                filename = os.path.join(folder ,filename)
                with open(filename, 'r') as file:
                    data = json.load(file)         
                
                yield filename, data
    

    def test_sorting_for_results_in_folder(self, folder_path) :
        iterator = self.get_all_search_results_iterator(folder_path)

        for filename, data in iterator:
            self.filename = filename 
            self.test_results_are_sorted_correctly(data)
 
    def test_details_for_results_in_folder(self, folder_path) :
        iterator = self.get_all_search_results_iterator(folder_path)

        for filename, data in iterator:
            self.filename = filename 
            self.check_details(data)


    def check_details(self, data : Dict) :
        list = data["Results"]
        for book in list:
            self.test_book(book)

    def test_book(self, book : Dict) :

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
                self.testcase.assertFalse(f"all books should have a title but at least one is missing from {self.filename}")

            if self.author is None or len(self.author) == 0 :
                self.testcase.assertFalse(f"all books should have an author but {self.title} in {self.filename} has none")

            currentBookDescription = f"{self.title} by {self.author} in {self.filename}"

            seriesDescription = unsafe_get_series(book, False) 
            if seriesDescription is None :
                self.testcase.assertFalse(f"Series description should not be None but is for {currentBookDescription} ")

            if seriesName is not None and len(seriesName) != 0 :
                self.testcase.assertTrue(len(seriesDescription) > 0, f"Book has series so should have a series description in {currentBookDescription}" )

      

        except Exception as e2:
            print(f"Error processing {self.title} by {self.author} in {self.filename}: {e2} : {seriesName} : {seriesNo} :")
            # self.dump_book(book)
            
    def dump_book(self, book : Dict ) :
        import json
        jsonStr = json.dumps(book, indent=4)
        print(jsonStr)
        print("")

    def quote(self, s : str, padding : int ) : 
        q = "'"
        return (q + s + q).ljust(padding)

    def getBookDetails(self, book : Dict) :
        if book == None :
            return "(None)"
        
        seriesName = ""
        readingOrder = ""
        ds = book.get("detailedSeries")
        if not ds is None :                       
            seriesName = ds.get("seriesName", "").strip()
            readingOrder = ds.get("readingOrder", "")

        return (self.quote(book.get("title", "")            , 40) + " : " + 
                self.quote(seriesName                       , 20) + " : " + 
                self.quote(readingOrder                     , 10) + " : " + 
                self.quote(book.get('seriesDescription',"") , 40))
        

    def test_results_are_sorted_correctly(self, data : Dict) :
        # Given a list of books, calculate the seriesDescription for each
        # book and then sort the list by this description.
        # Then iterate through each book and check that each series Name
        # and series number is greater than or equal to the previous entry
        
        # If the series number has more than one value we just check the first value

        list = data["Results"]
        for book in list:
            book['seriesDescription'] = unsafe_get_series(book, False) 

        sorted_list = sorted(list , key=lambda d: d['seriesDescription'])
        lastBook = None
        lastSeriesName = ""
        lastSeriesNo = 0
        for book in sorted_list :
            seriesName = ""
            seriesNo = 0
            readingOrder = ""
            ds = book.get("detailedSeries")
            if not ds is None :                       
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

            self.testcase.assertGreaterEqual(seriesName , lastSeriesName, "Wrong order for Series Name " + 
                                             "\r\nPrevious Book = " + self.getBookDetails(lastBook)  +
                                             "\r\nCurrent Book  = " + self.getBookDetails(book)  +
                                             "\r\nIn file " + self.filename)


            self.testcase.assertGreaterEqual(seriesNo , lastSeriesNo, "Wrong order for Series No " + readingOrder +  
                                             "\r\nPrevious Book = " + self.getBookDetails(lastBook)  +
                                             "\r\nCurrent Book  = " + self.getBookDetails(book)  +
                                             "\r\nIn file " + self.filename) 

            lastSeriesName = seriesName
            lastSeriesNo = seriesNo
            lastBook = book



 