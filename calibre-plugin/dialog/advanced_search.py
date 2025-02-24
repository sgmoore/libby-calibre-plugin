#
# Copyright (C) 2023 github.com/ping
#
# This file is part of the OverDrive Libby Plugin by ping
# OverDrive Libby Plugin for calibre / libby-calibre-plugin
#
# See https://github.com/ping/libby-calibre-plugin for more
# information
#
# Now being maintained at https://github.com/sgmoore/libby-calibre-plugin
#
from threading import Lock
from typing import Dict, List, Optional
from datetime import datetime

from calibre.constants import DEBUG, config_dir 

from qt.core import (
    QAbstractItemView,
    QButtonGroup,
    # QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel, 
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QThread,
    QWidget,
    Qt,
 
)

from .base_search import SearchBaseDialog
from .widgets import DefaultQPushButton, DefaultQTableView
from ..compat import (
    QHeaderView_ResizeMode_ResizeToContents,
    QHeaderView_ResizeMode_Stretch,
    _c,
)
from ..config import (
    BorrowActions,
    PREFS,
    PreferenceKeys,
    SearchMode,
)
from ..libby import LibbyFormats
from ..models import (
    LibbySearchModel,
    LibbySearchSortFilterModel,
)
from ..overdrive import LibraryMediaSearchParams
from ..utils import PluginImages
from ..workers import OverDriveLibraryMediaSearchWorker

from .. import PLUGIN_NAME, PLUGINS_FOLDER_NAME

# noinspection PyUnreachableCode
if False:
    load_translations = _ = ngettext = lambda x=None, y=None, z=None: x

load_translations()


class AdvancedSearchDialogMixin(SearchBaseDialog):
    def __init__(self, *args):
        super().__init__(*args)

        self.maximum_number_of_pages = 0 
        self.current_page_no = 1

        self._lib_search_threads: List[QThread] = []
        self._lib_search_result_sets: Dict[str, List[Dict]] = {}
        self.lock = Lock()

        adv_search_widget = QWidget()
        adv_search_widget.layout = QGridLayout()
        adv_search_widget.setLayout(adv_search_widget.layout)
        widget_row_pos = 0

        form_fields_layout = QFormLayout()
        form_fields_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_fields_layout.setHorizontalSpacing(20)
        adv_search_widget.layout.addLayout(
            form_fields_layout, widget_row_pos, 0, 1, self.view_hspan - 1
        )

        # Title Query textbox
        self.adv_query_txt = QLineEdit(self)
        self.adv_query_txt.setClearButtonEnabled(True)
        self.adv_query_txt.textChanged.connect(self.re_enable_search)
        form_fields_layout.addRow(_("Query"), self.adv_query_txt)

        # Title Query textbox
        self.title_txt = QLineEdit(self)
        self.title_txt.setClearButtonEnabled(True)
        self.title_txt.textChanged.connect(self.re_enable_search)
        form_fields_layout.addRow(_c("Title"), self.title_txt)

        # Creator Query textbox
        self.creator_txt = QLineEdit(self)
        self.creator_txt.setClearButtonEnabled(True)
        self.creator_txt.textChanged.connect(self.re_enable_search)
        form_fields_layout.addRow(_c("Author"), self.creator_txt)

        # Identifier Query textbox
        self.identifier_txt = QLineEdit(self)
        self.identifier_txt.setClearButtonEnabled(True)
        self.identifier_txt.textChanged.connect(self.re_enable_search)
        form_fields_layout.addRow(_("ISBN"), self.identifier_txt)

        rb_layout_spacing = 10
        self.availability_btn_group = QButtonGroup(self)
        self.availability_all_rb = QRadioButton(_("All"), self)
        self.availability_only_available_rb = QRadioButton(_("Available now"), self)
        self.availability_only_prelease_rb = QRadioButton(_("Coming soon"), self)
        availability_rb = (
            self.availability_all_rb,
            self.availability_only_available_rb,
            self.availability_only_prelease_rb,
        )
        self.availability_rb_layout = QHBoxLayout()
        self.availability_rb_layout.setSpacing(rb_layout_spacing)
        for rb in availability_rb:
            self.availability_btn_group.addButton(rb)
            self.availability_rb_layout.addWidget(rb)
        form_fields_layout.addRow(_("Availability"), self.availability_rb_layout)

        if PREFS[PreferenceKeys.INCL_NONDOWNLOADABLE_TITLES]:
            self.media_type_btn_group = QButtonGroup(self)
            self.media_all_rb = QRadioButton(_("Any"), self)
            self.media_ebook_rb = QRadioButton(_("Book"), self)
            self.media_audiobook_rb = QRadioButton(_("Audiobook"), self)
            self.media_magazine_rb = QRadioButton(_("Magazine"), self)
            media_type_rb = (
                self.media_all_rb,
                self.media_ebook_rb,
                self.media_audiobook_rb,
                self.media_magazine_rb,
            )
            self.media_rb_layout = QHBoxLayout()
            self.media_rb_layout.setSpacing(rb_layout_spacing)
            for rb in media_type_rb:
                self.media_type_btn_group.addButton(rb)
                self.media_rb_layout.addWidget(rb)
            form_fields_layout.addRow(_("Media"), self.media_rb_layout)

        self.subject_btn_group = QButtonGroup(self)
        self.subject_all_rb = QRadioButton(_("All"), self)
        self.subject_fiction_rb = QRadioButton(_("Fiction"), self)
        self.subject_nonfiction_rb = QRadioButton(_("Nonfiction"), self)
        subject_rb = (
            self.subject_all_rb,
            self.subject_fiction_rb,
            self.subject_nonfiction_rb,
        )
        self.subject_rb_layout = QHBoxLayout()
        self.subject_rb_layout.setSpacing(rb_layout_spacing)
        for rb in subject_rb:
            self.subject_btn_group.addButton(rb)
            self.subject_rb_layout.addWidget(rb)
        form_fields_layout.addRow(_("Subject"), self.subject_rb_layout)

   
        buttons_layout = QFormLayout()
        buttons_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        buttons_layout.setHorizontalSpacing(20)
        adv_search_widget.layout.addLayout(
            buttons_layout, widget_row_pos,   self.view_hspan - 1, 1, 1
        )

        # Search button
        self.adv_search_btn = DefaultQPushButton(_c("Search"), self.resources[PluginImages.Search], self )
        self.adv_search_btn.clicked.connect(self.adv_search_btn_clicked)
        buttons_layout.addRow(self.adv_search_btn)

        # Clear button
        self.adv_clear_btn = DefaultQPushButton(_c("Clear"), self.resources[PluginImages.Refresh], self )
        self.adv_clear_btn.clicked.connect(self.adv_clear_btn_clicked)
        buttons_layout.addRow(self.adv_clear_btn)

        self.load_results_btn = DefaultQPushButton(_c("Load"), self.resources[PluginImages.ExternalLink], self )
        buttons_layout.addRow(self.load_results_btn)

        self.save_results_btn = DefaultQPushButton(_c("Save"), self.resources[PluginImages.ExternalLink], self )
        buttons_layout.addRow(self.save_results_btn)
       
        widget_row_pos += 1

        self.adv_search_model = LibbySearchModel(None, [], self.db)
        self.adv_search_proxy_model = LibbySearchSortFilterModel(
            self, model=self.adv_search_model
        )
        self.adv_search_proxy_model.setSourceModel(self.adv_search_model)
        self.load_results_btn.clicked.connect(self.loadRows)
        self.save_results_btn.clicked.connect(self.saveRows)

        # The main search results list
        self.adv_search_results_view = DefaultQTableView(
            self, model=self.adv_search_proxy_model, min_width=self.min_view_width
        )
        self.adv_search_results_view.setSelectionMode(QAbstractItemView.SingleSelection)
        # context menu
        self.adv_search_results_view.customContextMenuRequested.connect(
            self.adv_search_results_view_context_menu_requested
        )
        # selection change
        self.adv_search_results_view.selectionModel().selectionChanged.connect(
            self.adv_search_results_view_selection_model_selectionchanged
        )
        # debug display
        self.adv_search_results_view.doubleClicked.connect(
            lambda mi: self.display_debug("Search Result", mi.data(Qt.UserRole))
            if DEBUG and mi.column() == self.adv_search_model.columnCount() - 1
            else self.show_book_details(mi.data(Qt.UserRole))
        )
        horizontal_header = self.adv_search_results_view.horizontalHeader()
        for col_index in range(self.adv_search_model.columnCount()):
            horizontal_header.setSectionResizeMode(
                col_index,
                QHeaderView_ResizeMode_Stretch
                if col_index == 0
                else QHeaderView_ResizeMode_ResizeToContents,
            )
        adv_search_widget.layout.addWidget(
            self.adv_search_results_view,
            widget_row_pos,
            0,
            self.view_vspan,
            self.view_hspan,
        )
        widget_row_pos += 1

        if hasattr(self, "search_tab_index"):
            self.toggle_advsearch_mode_btn = DefaultQPushButton(
                "", self.resources[PluginImages.Switch], self
            )
            self.toggle_advsearch_mode_btn.setToolTip(_("Basic Search"))
            self.toggle_advsearch_mode_btn.setMaximumWidth(
                self.toggle_advsearch_mode_btn.height()
            )
            self.toggle_advsearch_mode_btn.clicked.connect(
                self.toggle_advsearch_mode_btn_clicked
            )
            adv_search_widget.layout.addWidget(
                self.toggle_advsearch_mode_btn, widget_row_pos, 0
            )

        borrow_action_default_is_borrow = PREFS[
            PreferenceKeys.LAST_BORROW_ACTION
        ] == BorrowActions.BORROW or not hasattr(self, "download_loan")

        self.adv_search_borrow_btn = DefaultQPushButton(
            _("Borrow")
            if borrow_action_default_is_borrow
            else _("Borrow and Download"),
            self.resources[PluginImages.Add],
            self,
        )
        adv_search_widget.layout.addWidget(
            self.adv_search_borrow_btn, widget_row_pos, self.view_hspan - 1
        )
        self.adv_hold_btn = DefaultQPushButton(_("Place Hold"), None, self)
        adv_search_widget.layout.addWidget(
            self.adv_hold_btn, widget_row_pos, self.view_hspan - 2
        )

        # Create empty calibre book 
        self.empty_book_btn = DefaultQPushButton(("Create empty entry in calibre"), None, self)
        self.empty_book_btn.setToolTip(_("Creates an empty entry in Calibre with the details of the book"))
        self.empty_book_btn.clicked.connect(self.adv_search_empty_book_btn_clicked)
        adv_search_widget.layout.addWidget(self.empty_book_btn, widget_row_pos, self.view_hspan - 3)

        # set last 3 col's min width (buttons)
        for i in (1 ,2, 3) :
            adv_search_widget.layout.setColumnMinimumWidth(
                adv_search_widget.layout.columnCount() - i, self.min_button_width
            )
        for col_num in range(0, adv_search_widget.layout.columnCount() - 3):
            adv_search_widget.layout.setColumnStretch(col_num, 1)


        self.adv_search_tab_index = self.add_tab(
            adv_search_widget, _("Advanced Search")
        )
        self.last_borrow_action_changed.connect(self.rebind_advsearch_borrow_btn)
        self.sync_starting.connect(self.base_sync_starting_advsearch)
        self.sync_ended.connect(self.base_sync_ended_advsearch)
        self.loan_added.connect(self.loan_added_advsearch)
        self.loan_removed.connect(self.loan_removed_advsearch)
        self.hold_added.connect(self.hold_added_advsearch)
        self.hold_removed.connect(self.hold_removed_advsearch)

    def toggle_advsearch_mode_btn_clicked(self):
        if hasattr(self, "search_tab_index"):
            PREFS[PreferenceKeys.SEARCH_MODE] = SearchMode.BASIC
            self.search_mode_changed.emit(SearchMode.BASIC)
            self.tabs.setCurrentIndex(self.search_tab_index)

    def base_sync_starting_advsearch(self):
        self.adv_search_borrow_btn.setEnabled(False)
        self.adv_search_model.sync({})

    def base_sync_ended_advsearch(self, value):
        self.adv_search_borrow_btn.setEnabled(True)
        self.adv_search_model.sync(value)

    def rebind_advsearch_borrow_btn(self, last_borrow_action: str):
        borrow_action_default_is_borrow = (
            last_borrow_action == BorrowActions.BORROW
            or not hasattr(self, "download_loan")
        )
        self.adv_search_borrow_btn.setText(
            _("Borrow") if borrow_action_default_is_borrow else _("Borrow and Download")
        )
        self.adv_search_borrow_btn.borrow_menu = None
        self.adv_search_borrow_btn.setMenu(None)
        self.adv_search_results_view.selectionModel().clearSelection()

    def loan_added_advsearch(self, loan: Dict):
        self.adv_search_model.add_loan(loan)
        self.adv_search_results_view.selectionModel().clearSelection()

    def loan_removed_advsearch(self, loan: Dict):
        self.adv_search_model.remove_loan(loan)
        self.adv_search_results_view.selectionModel().clearSelection()

    def hold_added_advsearch(self, hold: Dict):
        self.adv_search_model.add_hold(hold)
        self.adv_search_results_view.selectionModel().clearSelection()

    def hold_removed_advsearch(self, hold: Dict):
        self.adv_search_model.remove_hold(hold)
        self.adv_search_results_view.selectionModel().clearSelection()

    def adv_search_results_view_selection_model_selectionchanged(self):
        self.view_selection_model_selectionchanged(
            self.adv_search_borrow_btn,
            self.adv_hold_btn,
            self.adv_search_results_view,
            self.adv_search_model,
        )

    def adv_search_results_view_context_menu_requested(self, pos):
        self.view_context_menu_requested(
            pos, self.adv_search_results_view, self.adv_search_model
        )

    def _adv_reset_borrow_hold_buttons(self):
        self.adv_search_borrow_btn.borrow_menu = None
        self.adv_search_borrow_btn.setMenu(None)
        self.adv_search_borrow_btn.setEnabled(True)
        self.adv_hold_btn.hold_menu = None
        self.adv_hold_btn.setMenu(None)
        self.adv_hold_btn.setEnabled(True)

    def _has_running_search(self, asked_by=None) -> bool:
        for t in self._lib_search_threads:
            if asked_by and asked_by == t.library_key:
                continue
            if t.isRunning():
                return True
        return False
    
    def re_enable_search(self) :
        self.adv_search_btn.setText(_c("Search"))
        self.adv_search_btn.setEnabled(True)
        self.current_page_no = 1
    
    def adv_clear_btn_clicked(self) :
        self.adv_query_txt.clear()
        self.title_txt.clear()
        self.creator_txt.clear()
        self.identifier_txt.clear()
        self.adv_search_model.sync({"search_results": []})
        self.availability_all_rb.setChecked(True)
        self.media_all_rb.setChecked(True)
        self.subject_all_rb.setChecked(True)
        self.re_enable_search()


    def adv_search_btn_clicked(self):
        if self.current_page_no <= 1 :
            self.adv_search_model.sync({"search_results": []}, True)

        self.maximum_number_of_pages = 0
        
        self.adv_search_results_view.sortByColumn(-1, Qt.AscendingOrder)
        self._reset_borrow_hold_buttons()
        if self._has_running_search():
            return

        if not PREFS[PreferenceKeys.INCL_NONDOWNLOADABLE_TITLES]:
            formats = [
                LibbyFormats.EBookEPubAdobe,
                LibbyFormats.EBookPDFAdobe,
                LibbyFormats.EBookEPubOpen,
                LibbyFormats.EBookPDFOpen,
                LibbyFormats.MagazineOverDrive,
            ]
        else:
            formats = [
                LibbyFormats.EBookEPubAdobe,
                LibbyFormats.EBookPDFAdobe,
                LibbyFormats.EBookEPubOpen,
                LibbyFormats.EBookPDFOpen,
                LibbyFormats.MagazineOverDrive,
                LibbyFormats.EBookKindle,
                LibbyFormats.AudioBookMP3,
                LibbyFormats.AudioBookOverDrive,
            ]

        media_type = ""
        if PREFS[PreferenceKeys.INCL_NONDOWNLOADABLE_TITLES]:
            if self.media_ebook_rb.isChecked():
                media_type = "ebook"
            elif self.media_audiobook_rb.isChecked():
                media_type = "audiobook"
            elif self.media_magazine_rb.isChecked():
                media_type = "magazine"

        subject_id = ""
        if self.subject_nonfiction_rb.isChecked():
            subject_id = "111"
        elif self.subject_fiction_rb.isChecked():
            subject_id = "26"

        query = LibraryMediaSearchParams(
            query=self.adv_query_txt.text(),
            title=self.title_txt.text(),
            creator=self.creator_txt.text(),
            identifier=self.identifier_txt.text(),
            show_only_available=self.availability_only_available_rb.isChecked(),
            show_only_prelease=self.availability_only_prelease_rb.isChecked(),
            formats=formats,
            media_type=media_type,
            subject_id=subject_id,
            per_page=PREFS[PreferenceKeys.SEARCH_RESULTS_MAX],
            page=self.current_page_no

        )
        if query.is_empty():
            return

        self.adv_search_btn.setText(_c("Searching..."))
        self.adv_search_btn.setEnabled(False)
        self.setCursor(Qt.WaitCursor)
        library_keys = self.adv_search_model.limited_library_keys()
        self.status_bar.showMessage(
            ngettext(
                "Searching across {n} library...",
                "Searching across {n} libraries...",
                len(library_keys),
            ).format(n=len(library_keys))
        )
        self._lib_search_threads = []
        self._lib_search_result_sets = {}

      

        for library_key in library_keys:
            search_thread = self._get_adv_search_thread(
                self.overdrive_client, library_key, query
            )
            self._lib_search_threads.append(search_thread)
            search_thread.start()

    def adv_search_for(self, title: str, author: str):
        self.tabs.setCurrentIndex(self.adv_search_tab_index)
        self.title_txt.setText(title)
        self.creator_txt.setText(author)
        self.availability_all_rb.setChecked(True)
        self.identifier_txt.setText("")
        self.adv_search_btn.setFocus(Qt.OtherFocusReason)
        self.adv_search_btn.animateClick()

    def _process_search_results(self, library_key, results : Optional[Dict] ):
        with self.lock:
            print(f"Type of results = {type(results)}")
            if results == None :
                search_items = []
                totalItems = 0
                totalItems2 = 0
                lastPageNo = 0
            else :
                search_items = results.get("items", [])

                noPerPage = PREFS[PreferenceKeys.SEARCH_RESULTS_MAX]
                print(f'Items {len(search_items)} vs {noPerPage}')
               

                try :
                    totalItems = results["facets"]["availability"]["items"][0]["totalItems"]
                except Exception as e1:
                    try :
                        totalItems = results["facets"]["availability"]["items"][1]["totalItems"]
                    except Exception as e2:
                        print("")
                        print(e2)
                        try :
                            print(f'item[0] = {results["facets"]["availability"]["items"]}')
                        except Exception as e3:
                            print(e3)
                        totalItems = 0
                                 
                try :
                    totalItems2 = results["totalItems"]
                    print(f'item[3] = {totalItems2}')
                    lastPageNo = results["links"]["last"]["page"]
                    print(f'lastPageNo = {lastPageNo}')

                    if (lastPageNo > self.maximum_number_of_pages) :
                        self.maximum_number_of_pages = lastPageNo
                except Exception as e3:
                    print(e3)
                    


            self._lib_search_result_sets[library_key] = search_items
            found_library_keys = self._lib_search_result_sets.keys()
            if len(found_library_keys) != len(self._lib_search_threads):
                pending_libraries = [
                    t.library_key
                    for t in self._lib_search_threads
                    if t.library_key not in found_library_keys
                ]
                self.status_bar.showMessage(
                    _("Waiting for {libraries}...").format(
                        libraries=", ".join(pending_libraries)
                    )
                )
                return

        
            self.status_bar.clearMessage()
            combined_search_results: Dict[str, Dict] = {}
            
            for lib_key, result_items in self._lib_search_result_sets.items():
                print (lib_key + " " + str(len(result_items)))

                for item_rank, item in enumerate(result_items, start=1):
                    site_availability = {}
                    for k in (
                        "advantageKey",
                        "availabilityType",
                        "availableCopies",
                        "estimatedWaitDays",
                        "formats",
                        "holdsCount",
                        "holdsRatio",
                        "isAdvantageFiltered",
                        "isAvailable",
                        "isOwned",
                        "isRecommendableToLibrary",
                        "isFastlane",
                        "isHoldable",
                        "juvenileEligible",
                        "luckyDayAvailableCopies",
                        "luckyDayOwnedCopies",
                        "ownedCopies",
                        "visitorEligible",
                        "youngAdultEligible",
                    ):
                        if k in item:
                            site_availability[k] = item.pop(k)
                    site_availability["advantageKey"] = library_key
                    item.setdefault("siteAvailabilities", {})
                    item.setdefault("__item_ranks", [])
                    item.setdefault("formats", [])
                    title_id = item["id"]
                    print (str(item_rank) + " " + title_id)
                    combined_search_results.setdefault(title_id, item)
                    # merge site availabilities
                    combined_search_results[title_id]["siteAvailabilities"][
                        lib_key
                    ] = site_availability
                    # merge item ranks
                    combined_search_results[title_id]["__item_ranks"].append(item_rank)
                    # merge formats
                    existing_format_ids = [
                        f["id"]
                        for f in combined_search_results[title_id].get("formats", [])
                    ]
                    for f in site_availability.get("formats", []):
                        if f["id"] not in existing_format_ids:
                            combined_search_results[title_id]["formats"].append(f)

            ordered_search_result_items = sorted(
                combined_search_results.values(),
                key=lambda r: (
                    sum(r["__item_ranks"]) / len(r["__item_ranks"]),  # average rank
                    1 / len(r["__item_ranks"]),
                ),
            )

            noOfResults = len(ordered_search_result_items)
            per_page=PREFS[PreferenceKeys.SEARCH_RESULTS_MAX]

            if (self.maximum_number_of_pages > 1 ) : 
                if (self.current_page_no < self.maximum_number_of_pages) :
                    self.current_page_no = self.current_page_no+1
                    self.adv_search_btn.setText(_c("More")) 
                    self.adv_search_btn.setEnabled(True)
                    self.adv_search_btn.setToolTip(_c("Get Page") + f" {self.current_page_no} " + _c("of") + f" {self.maximum_number_of_pages}")
                else :
                    self.adv_search_btn.setText(_c("No more"))
                    self.adv_search_btn.setToolTip("")
                    self.adv_search_btn.setEnabled(True)
                
            else :
                self.adv_search_btn.setText(_c("Search"))
                self.adv_search_btn.setToolTip("")                
                self.adv_search_btn.setEnabled(True)

            self.adv_search_model.sync({"search_results": ordered_search_result_items}, False)
            print(f"Synced : {self.adv_search_model.rowCount()} of {totalItems}")

            noOfResults = self.adv_search_model.rowCount()

            self.unsetCursor()

            if totalItems == 1 and noOfResults == 1 :
                message = _c("1 result found")
            else :
                message =  _c("{n} of {totalItems} results found {totalItems2} {lastPageNo}").format(n=noOfResults, totalItems=totalItems , totalItems2=totalItems2, lastPageNo = lastPageNo )

            message = ngettext("{n} result found", "{n} results found", noOfResults, ).format(n=noOfResults)
          

            self.status_bar.showMessage(message)
               
            


    def _get_adv_search_thread(
        self, overdrive_client, library_key: str, query: LibraryMediaSearchParams
    ):
        thread = QThread()
        worker = OverDriveLibraryMediaSearchWorker()
        worker.setup(overdrive_client, library_key, query)
        worker.moveToThread(thread)
        thread.library_key = library_key
        thread.worker = worker
        thread.started.connect(worker.run)

        def done(lib_key: str, results: Dict):
            thread.quit()
            self._process_search_results(lib_key, results) # results.get("items", []))

        def errored_out(lib_key: str, err: Exception):
            thread.quit()
            self.logger.warning(
                "Error encountered during search (%s): %s", lib_key, err
            )
            errorMessage = _("Error encountered during search ({library}): {error}").format(
                    library=lib_key, error=str(err)
                )
            self._process_search_results(lib_key, None)
            self.status_bar.showMessage(errorMessage)
            self.gui.status_bar.show_message(errorMessage ,5000)

        worker.finished.connect(lambda lib_key, results: done(lib_key, results))
        worker.errored.connect(lambda lib_key, err: errored_out(lib_key, err))

        return thread

    def empty_hold_callback (self, job):
        if job.failed:
            self.unhandled_exception(job.exception, msg=_c("Failed to create empty e-book"))
        self.gui.status_bar.show_message(job.description + " " + _c("finished"), 5000)

    def adv_search_empty_book_btn_clicked(self):
        self.empty_book_btn_clicked(self.empty_hold_callback, self.adv_search_results_view.selectionModel() , self.adv_search_model) 

    def getSearchResultsFolder(self) :
        from pathlib import Path
        PLUGIN_DIR = Path(config_dir, PLUGINS_FOLDER_NAME)
        documents_folder= PLUGIN_DIR.joinpath(f"{PLUGIN_NAME} Search Results")
        if not documents_folder.exists():
            documents_folder.mkdir(parents=True, exist_ok=True)
        return str(documents_folder)

    
    def saveRows(self) :
        import json
     
        fileName,_ = QFileDialog.getSaveFileName(
            None,
            "Save ", 
            self.getSearchResultsFolder(), 
            "Json Files (*.json)"
        )        

        if fileName:
            data =  { }
            data["Type"]    = f"{PLUGIN_NAME} Search Results"
            data["Date"]    = datetime.now().isoformat()
            data["Results"] = self.adv_search_model._rows

            print(f"Type of data = {type(data)}")
            jsonStr = json.dumps(data, indent=4)
            print(f"Type of jsonStr = {type(jsonStr)}")

            with open(fileName, "w") as text_file:
                print("Saving")
                text_file.write(jsonStr)
                print("Saved")
    
    def loadRows(self) :
        import json

        fileName,_ = QFileDialog.getOpenFileName(
            None,
            "Select a File", 
            self.getSearchResultsFolder(), 
            "Json Files (*.json);"
        )

        if not fileName :
            return

        from calibre.gui2.widgets import BusyCursor
        from calibre.gui2 import question_dialog, error_dialog

        self.adv_search_model.beginResetModel()
        self.adv_search_model._rows = []
        self.adv_search_model.endResetModel()

        data = [] 
        with open(fileName, "r") as file: 
            with BusyCursor():
                data = json.load(file) 
            
            print(f"Type of data = {type(data)}")
            if (not isinstance(data, Dict)) or (data.get("Type") != f"{PLUGIN_NAME} Search Results" ) or not data.get("Results") :
                error_dialog(None, _c("Invalid format"), _c("This file does not appear to be in the correct format ."), show=True, show_copy_button=False)
                return
            
            if data.get("Date") :
                age_of_results = datetime.now() -  datetime.fromisoformat(data["Date"])
                if (age_of_results.days > 14) :

                    if not question_dialog(self,  _c("Stale results") ,
                        '<p>' + _c('These results are {0} days old and hence availabilty and wait times will be incorrect.').format(age_of_results.days) + 
                        '<p>' + _c('Are you sure you want to continue?')   
                        ) :
                        return                        

            with BusyCursor():
                self.adv_search_model.beginResetModel()
                self.adv_search_model._rows = data["Results"]
                self.adv_search_model.endResetModel()
            
