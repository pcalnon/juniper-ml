"""What header bytes does Starlette's TestClient hand the ASGI app for a non-ASCII value?"""

from starlette.testclient import TestClient

seen: list = []


async def app(scope, receive, send):
    if scope["type"] == "http":
        seen.append([v for k, v in scope["headers"] if k == b"if-match"])
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})


TestClient(app).get("/", headers={"If-Match": b"\xa0*"})
print("sent b'\\xa0*'; TestClient delivered:", seen[-1])
