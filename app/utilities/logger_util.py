import json
import logging
from datetime import datetime


class JsonLoggingFormatter(logging.Formatter):
    """Formats JSON data that is being logged."""

    def format(self, record):
        log_obj = {
            "timestamp": int(record.created * 1000),
            "message": record.getMessage(),
            "log.level": record.levelname,
            "logger.name": record.name,
            "thread.id": record.thread,
            "thread.name": record.threadName,
            "process.id": record.process,
            "process.name": record.processName,
            "file.name": record.pathname,
            "line.number": record.lineno,
            "entity.type": "SERVICE",
            "extra.message": record.getMessage(),
            "extra.asctime": self.formatTime(record, self.datefmt),
        }

        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        return json.dumps(log_obj)


class MicrosecondFormatter(logging.Formatter):
    """Custom formatter to include microseconds in log timestamps."""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs * 1000):06d}"
