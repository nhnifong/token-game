
import asyncio
from websockets.asyncio.server import serve, broadcast
from collections import defaultdict, deque
import json
from random import randint

DECIDING_PERIOD = 5 # seconds

connected = set()
scores = defaultdict(lambda: 0)
history = deque(['If','only','it','were','all','so','simple!','If','only'])
outfile = open('content_log.txt', 'a')

async def handler(websocket):
    connected.add(websocket)
    print("new connection (%i clients connected)" % len(connected))
    try:
        # send new user recent history and setup data
        event = {
            'u': len(connected), # connected users
            'h': ' '.join(history), # recent text
        }
        await websocket.send(json.dumps(event));
        while True:
            message = await websocket.recv()
            print("received %r" % message)
            data = json.loads(message)
            scores[data['s']] += 1
    finally:
        connected.remove(websocket)
        print("lost connection (%i clients connected)" % len(connected))

async def select_token():
    while True:
        print('select_token')
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
            history.append(token)
            if len(history) > 500:
                history.popleft()
            outfile.write(token+' ')
        await asyncio.sleep(DECIDING_PERIOD)

async def main():
    task = asyncio.create_task(select_token())
    async with serve(handler, "localhost", 8765):
        print("server listening on localhost:8756")
        await asyncio.get_running_loop().create_future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())