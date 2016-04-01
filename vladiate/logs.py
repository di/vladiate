import logging

logger = logging.getLogger("vlad_logger")
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(sh)
logger.propagate = False
