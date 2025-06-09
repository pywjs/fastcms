# Logging Utilities

How to use the logging utilities in any project?


To log to console: 
```python
from fastcms.utils.logging import setup_logging, get_logger

setup_logging(level="DEBUG")

logger = get_logger("YourLoggerName")
logger.info("Logging system ready 🚀")
```

# To log to file:
```python
from fastcms.utils.logging import setup_logging, get_logger
setup_logging(level="DEBUG", file="app.log")
logger = get_logger("YourLoggerName")
logger.info("Logging system ready 🚀")
```
