import asyncio

import websockets
import json
from connect4 import PLAYER1, PLAYER2
from connect4 import Connect4
import itertools
async def handler(websocket):

    game = Connect4()
    messages = await websocket.recv()
    turns = itertools.cycle([PLAYER1, PLAYER2])
    player = next(turns)

    async for message in websocket:
        event = json.loads(message)
        assert(event['type'] == 'play')
        column = event['column']

        try:
            row = game.play(player=player, column=column)

        except RuntimeError as exc:
            event = {
                "type" : "error",
                "message": str(exc)
            }
            await websocket.send(json.dumps(event))
            continue

        event = {
            "type" : "play",
            "player": player,
            "column": column,
            "row": row
        }

        await websocket.send(json.dumps(event))


        if game.winner is not None:
            event = {
                "type": "win", 
                "player": game.winner
            }

            await websocket.send(json.dumps(event))

        
        player = next(turns)
    

# async def handler(websocket):
#     while True:
#         try:
#             message = await websocket.recv()
#         except websockets.ConnectionClosedOK:
#             break
#         print(message)
        

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
