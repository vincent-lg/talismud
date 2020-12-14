from logbook import FileHandler, Logger

logger = Logger()
file_handler = FileHandler("logs/commands.log",
        encoding="utf-8", level="DEBUG", delay=True)
file_handler.format_string = (
        "{record.time:%Y-%m-%d %H:%M:%S.%f%z} [{record.level_name}] "
        "{record.message}"
)
logger.handlers.append(file_handler)
