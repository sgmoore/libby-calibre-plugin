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

from typing import Dict

from .libby import LibbyClient
from .models import get_media_title
from .tools.CustomLogger import CustomLogger

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tools.lint_helper import load_translations

    from calibre.utils.localization import _


load_translations()


class LibbyBorrowMedia:
    def __call__(
        self,
        gui,
        libby_client: LibbyClient,
        media: Dict,
        card: Dict,
        is_lucky_day_loan: bool,
        log=None,
        abort=None,
        notifications=None,
    ):
        notifications.put((0.5, _("Borrowing")))
        loan = libby_client.borrow_media(media, card, is_lucky_day_loan)
        CustomLogger.logger.info(
            "Borrowed %s successfully from %s.",
            get_media_title(loan),
            card["advantageKey"],
        )
        if "cardId" not in loan:
            CustomLogger.logger.warning("Loan info returned does not have cardId")
            if media.get("cardId"):  # from a hold
                loan["cardId"] = media["cardId"]
        return loan
