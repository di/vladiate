import logging

logger = logging.getLogger("vlad_logger")
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(sh)
logger.propagate = False
