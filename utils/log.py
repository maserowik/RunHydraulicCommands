import logging


# logging.basicConfig(filename="myapp.log", level=logging.INFO)


# strFormat = format = "%(levelname)s | %(asctime)s | %(filename)s |  %(message)s"
# strFileName = "log.txt"
# levelVal = logging.INFO
# logging.addHandler("log.txt")
# logging.addHandler(logging.StreamHandler)


# logging.basicConfig(format=strFormat, filename=strFileName, level=levelVal)


# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler("log.txt")
file_handler.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handlers
file_formatter = logging.Formatter(
    "%(levelname)s | %(asctime)s | %(filename)s | line: %(lineno)d | %(funcName)s | %(message)s"
)

console_formatter = logging.Formatter(
    "%(levelname)s | %(message)s | %(filename)s | %(module)s | line: %(lineno)d"
)

file_handler.setFormatter(file_formatter)
console_handler.setFormatter(console_formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
