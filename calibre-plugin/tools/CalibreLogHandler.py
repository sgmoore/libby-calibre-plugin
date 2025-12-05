import logging
from calibre.utils.logging import DEBUG, ERROR, INFO, WARN


class CalibreLogHandler(logging.Handler):
    """
    Simple wrapper around the calibre job Log to support standard logging calls
    """

    def __init__(self, logger):
        self.calibre_log = None
        if not logger:
            super().__init__()
            return

        if isinstance(logger, CalibreLogHandler):
            # just in case we accidentally pass in a wrapped log
            self.calibre_log = logger.calibre_log
        else:
            self.calibre_log = logger
        calibre_log_level = self.calibre_log.filter_level
        level = logging.NOTSET
        if calibre_log_level <= DEBUG:
            level = logging.DEBUG
        elif calibre_log_level == INFO:
            level = logging.INFO
        elif calibre_log_level == WARN:
            level = logging.WARNING
        elif calibre_log_level >= ERROR:
            level = logging.ERROR
        super().__init__(level)

    def emit(self, record):
        if not self.calibre_log:
            return
        msg = self.format(record)
        if record.levelno <= logging.DEBUG:
            self.calibre_log.debug(msg)
        elif record.levelno == logging.INFO:
            self.calibre_log.info(msg)
        elif record.levelno == logging.WARNING:
            self.calibre_log.warning(msg)
        elif record.levelno >= logging.ERROR:
            self.calibre_log.error(msg)
        else:
            self.calibre_log.info(msg)

