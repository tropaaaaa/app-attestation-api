import os
import logging
import sys

from utilities.logger_util import JsonLoggingFormatter, MicrosecondFormatter

ENABLED = "true"
IS_DEBUG_MODE = os.getenv("DEBUG_MODE") == ENABLED
ENABLE_JSON_LOG = os.getenv("ENABLE_JSON_LOG_MODE") == ENABLED
ENABLE_STR_LOG = os.getenv("ENABLE_STR_LOG_MODE", ENABLED) == ENABLED

# Console Logging Formatter
console_log_format = "%(asctime)s|%(threadName)s-%(thread)d|%(levelname)s|%(pathname)s-%(lineno)d->%(funcName)s: %(message)s"
console_log_formatter = MicrosecondFormatter(console_log_format, datefmt="%Y-%m-%d %H:%M:%S")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_log_formatter)

# Json Logging Formatter
json_handler = logging.StreamHandler(sys.stdout)
json_handler.setFormatter(JsonLoggingFormatter())

# Main Logger
app_logger = logging.getLogger("app_logger")
app_logger.setLevel(logging.DEBUG if IS_DEBUG_MODE else logging.INFO)

if ENABLE_STR_LOG:
    app_logger.addHandler(console_handler)

if ENABLE_JSON_LOG:
    app_logger.addHandler(json_handler)

app_logger.info(
    f"App Logger Configuration. Debug Mode: {IS_DEBUG_MODE} | String Format: {ENABLE_STR_LOG} | JSON Format: {ENABLE_JSON_LOG}"
)

# Prevent double logging by stopping propagation to root logger
app_logger.propagate = False


def get_logger():
    return app_logger
