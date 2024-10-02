
import os
import signal
import asyncio
from websockets.asyncio.server import serve, broadcast
from collections import defaultdict
import json
from random import randint
from math import sqrt
import re
import redis
from datetime import datetime
from urllib.parse import urlparse

# redis key changes every few days, clearing the history
def current_key():
    return (datetime.now() - datetime(year=1999, month=1, day=1)).days//5

def sanitize(s):
    if disallowed.search(s):
        return ''
    else:
        return s[:20] # max token length

connected = set()
scores = defaultdict(lambda: 0)
# no urls, no underscores, no whitespace
disallowed = re.compile(r'(http)|(://)|(\w\.\w)|(\s)|(_)')


# r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'), decode_responses=True)
url = urlparse(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
r = redis.Redis(host=url.hostname, port=url.port, password=url.password, ssl=(url.scheme == "rediss"), ssl_cert_reqs=None)
if not r.exists(current_key()):
    r.set(current_key(), 'If only')

async def handler(websocket):
    connected.add(websocket)
    print('new connection (%i clients connected)' % len(connected))
    try:
        # send new user recent history and setup data
        event = {
            'u': len(connected), # connected users
            'h': r.get(current_key()), # recent text
        }
        await websocket.send(json.dumps(event));
        while True:
            # this loopruns every time a user sends a word
            message = await websocket.recv()
            print('received %r' % message)
            data = json.loads(message)
            token = sanitize(data['s'])
            if token:
                scores[token] += 1
    finally:
        connected.remove(websocket)
        print('lost connection (%i clients connected)' % len(connected))

async def select_token():
    while True:
        if len(scores) > 0:
            items = list(scores.items())
            print(repr(items))
            point = randint(0, sum(scores.values()) - 1)
            # select a token with a probability proportional to its score
            index = 0
            while point > items[index][1]:
                point -= items[index][1]
                index += 1
            token = items[index][0]
            # reset scores and broadcast selection to connected users
            scores.clear()
            event = {
                's': token,
                'u': len(connected), # connected users
            }
            print('broadcast token "%s"' % token)
            broadcast(connected, json.dumps(event))
            r.append(current_key(), ' '+token)
        sleep_seconds = sqrt(len(connected))*3
        await asyncio.sleep(sleep_seconds)

async def main():
    task = asyncio.create_task(select_token())

    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    port = int(os.environ.get("PORT", "8765"))
    print("listening on port ", port)
    async with serve(handler, "", port):
        await stop

if __name__ == "__main__":
    asyncio.run(main())