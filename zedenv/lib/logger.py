"""
Common functions
"""

import logging
import logging.config
import logging.handlers

class ZELogger:
    def __init__(self):
        logger_config = {
            'version': 1,
            'formatters': {
                'console': {
                    'class': 'logging.Formatter',
                    'format': '%(message)s',
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': logging.DEBUG,
                    'formatter': 'console',
                },
            },
            'root': {
                'level': logging.DEBUG,
                'handlers': ['console']
            },
        }

        logging.config.dictConfig(logger_config)

        self.logger = logging.getLogger("zedenv")

    def callback(self, log, exit_on_error=False):
        """Helper to call the appropriate logging level"""

        if log['level'] == 'CRITICAL':
            self.logger.critical(log['message'])

        elif log['level'] == 'ERROR':
            self.logger.error(log['message'])

        elif log['level'] == 'WARNING':
            self.logger.warning(log['message'])

        elif log['level'] == 'INFO':
            self.logger.info(log['message'])

        elif log['level'] == 'DEBUG':
            self.logger.debug(log['message'])

        elif log['level'] == 'EXCEPTION':
            if not exit_on_error:
                raise RuntimeError(log['message'])
            else:
                self.logger.error(log['message'])
                raise SystemExit(1)

    def log(self, content, exit_on_error=False):
        level = content["level"]
        message = content["message"]

        self.callback({
            "level": level,
            "message": message
        }, exit_on_error)

    def verbose_log(self, content, verbose_logs, exit_on_error=False):
        if verbose_logs:
            self.log(content)