import os

myToken = os.getenv("MODELSCOPE_KEY")
if not myToken:
    raise RuntimeError("Missing env var MODELSCOPE_KEY. Please set it before running.")
