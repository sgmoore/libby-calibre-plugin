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

from pathlib import Path
from typing import Dict, Optional

from calibre.ptempfile import PersistentTemporaryDirectory
from calibre.gui2 import open_url

from .compat import _c
from .download import LibbyDownload
from .libby import LibbyClient
from .overdrive import OverDriveClient
from .tools.CustomLogger import CustomLogger
from .tools.WatchForFile import wait_for_file_qt
from os.path import expanduser
from .config import PREFS, PreferenceKeys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    load_translations = lambda x=None: x  # noqa: E731

load_translations()


class CustomEbookDownload(LibbyDownload):
    def __call__(
        self,
        gui,
        libby_client: LibbyClient,
        loan: Dict,
        card: Dict,
        library: Dict,
        format_id: str,
        book_id=None,
        metadata=None,
        filename="",
        tags=None,
        log=None,
        abort=None,
        notifications=None,
    ):
        raise NotImplementedError 
    
        if not tags:
            tags = []
        downloaded_filepath: Optional[Path] = None            
        try:

            library_key = library["preferredKey"]

            folder = expanduser(PREFS[PreferenceKeys.DOWNLOADS_FOLDER])
            file_ext = "." + LibbyClient.get_file_extension(format_id)

            url = OverDriveClient.generate_download_ebook_permalink(library_key, format_id , loan["id"])

            CustomLogger.log_simple_string(f"Opening {url}")
            open_url(url) 
            CustomLogger.log_simple_string(f"watching folder : {folder} for file type {file_ext}")

            downloaded_filepath = wait_for_file_qt(folder , file_ext )
            CustomLogger.log_simple_string(f"filename : {downloaded_filepath}")

                     
            if downloaded_filepath :
                self.add(
                gui,
                loan,
                card,
                library,
                format_id,
                downloaded_filepath,
                book_id,
                tags,
                metadata,
            )

        finally:
            try:
                if downloaded_filepath:
                    downloaded_filepath.unlink(missing_ok=True)
            except:  # noqa
                pass
        return loan

    def _custom_download(
        self,
        libby_client: LibbyClient,
        loan: Dict,
        format_id: str,
        filename: str,
        abort=None,
        notifications=None,
    ) -> Path:
        book_folder_path = Path(PersistentTemporaryDirectory())
        book_file_path = book_folder_path.joinpath(filename)

        notifications.put((0.5, _c("Downloading")))
        res_content = libby_client.fulfill_loan_file(
            loan["id"], loan["cardId"], format_id
        )
        with book_file_path.open("w+b") as tf:
            tf.write(res_content)

        return book_file_path
