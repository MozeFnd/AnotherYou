import os

myToken = os.getenv("xxx_KEY")
if not myToken:
    raise RuntimeError("Environment variable xxx_KEY is required")
