import logging
import colorlog
from datetime import datetime

class LogEvent():
    """
    LogEvent is put in the log_queue to be processed by the Logger  

    :param log_level: A string that specifies the log level 
    :type uuids: string
    :param name: A string that specifies the origin module of the log request
    :type name: string
    :param message: The log message itself
    :type message: string
    """

    def __init__(self, log_level, name, message):
        """ Constructor method
        """
        self.log_level = log_level
        self.name = name
        self.message = message
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def __repr__(self):
        """ Representation method
        """
        return f"{self.timestamp} [{self.name}] {self.message}"


class Logger():
    """
    Logger takes Log Events from log_queue and outputs them on stdout and in the log file.
    If the log_queue outputs a dead_pill, the logger shuts down.

    :param log_queue: A queue used by multiple processes to put log event in
    :type log_queue: multiprocess.Manager().Queue()
    :param log_file: The file in which the log is stored
    :type log_file: string
    :param dead_pill: The dead pill to shutdown the queue
    type dead_pill: string
    """

    def __init__(self, log_queue, log_level, log_file, dead_pill):
        """ Constructor method
        """
        self.log_queue = log_queue
        self.log_level = log_level
        self.log_file = log_file
        self.dead_pill = dead_pill

    def run(self):
        """ The function 'run' is started in a new process. 
            It handles log events from the log queue.
        """
        # logging config in run, because run starts as new process
        colored_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(message)s",
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red'
            })

        log = logging.getLogger(__name__)

        # handler for stdout
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(colored_formatter)

        # handler for the log file
        fileHandler = logging.FileHandler(self.log_file)
        clean_formatter = logging.Formatter("%(levelname)s %(message)s")
        fileHandler.setFormatter(clean_formatter)

        log.addHandler(fileHandler)
        log.addHandler(stream_handler)
        log.setLevel(self.log_level)

        while 1:
            log_event = self.log_queue.get()
            if log_event == self.dead_pill:
                break

            if log_event.log_level == "DEBUG": 
                log.debug(log_event)
            if log_event.log_level == "INFO": 
                log.info(log_event)
            if log_event.log_level == "WARNING": 
                log.warning(log_event)
            if log_event.log_level == "ERROR": 
                log.error(log_event)
            if log_event.log_level == "CRITICAL": 
                log.critical(log_event)

