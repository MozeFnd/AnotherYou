# import os

# myToken = os.getenv("xxx_KEY")127.0.0.1 - - [01/Feb/2026 11:33:07] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [01/Feb/2026 11:33:08] "GET /style.css HTTP/1.1" 404 -
127.0.0.1 - - [01/Feb/2026 11:33:08] "GET /script.js HTTP/1.1" 404 -
127.0.0.1 - - [01/Feb/2026 11:33:08] "GET /favicon.ico HTTP/1.1" 404 -
127.0.0.1 - - [01/Feb/2026 11:33:41] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [01/Feb/2026 11:33:41] "GET /style.css HTTP/1.1" 404 -
127.0.0.1 - - [01/Feb/2026 11:33:41] "GET /script.js HTTP/1.1" 404 -
127.0.0.1 - - [01/Feb/2026 11:33:51] "GET / HTTP/1.1" 304 -
127.0.0.1 - - [01/Feb/2026 11:33:51] "GET /style.css HTTP/1.1" 404 -
127.0.0.1 - - [01/Feb/2026 11:33:52] "GET /script.js HTTP/1.1" 404 -
# if not myToken:
#     raise RuntimeError("Environment variable xxx_KEY is required")
myToken = "ms-fa149b85-bc91-4fd4-bcd4-40d467c3b48b"