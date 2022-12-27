import asyncio

import websockets
import json
from connect4 import PLAYER1, PLAYER2
from connect4 import Connect4
import itertools
import secrets

JOIN = {}
WATCH = {}


async def error(websocket, message):

    event = {
        "type": "error",
        "message": message
    }
    await websocket.send(json.dumps(event))


async def start(websocket):
    """
    function to start the game. First player initialises game with this function
    :param websocket:
    :return:
    """
    game = Connect4()
    connected = {websocket}

    join_key = secrets.token_urlsafe(12)
    watch_key = secrets.token_urlsafe(15)
    JOIN[join_key] = game, connected
    WATCH[watch_key] = game, connected

    try:
        event = {
            "type": "init",
            "join": join_key,
            "watch": watch_key
        }
        await websocket.send(json.dumps(event))

        await play(websocket, game, PLAYER1, connected)

    finally:
        del JOIN[join_key]


async def join(websocket, join_key):
    """
    function to allow a second player join the game and play their moves
    :param websocket:
    :param join_key:
    :return:
    """
    try:
        # find the connect 4 game using the join key provided.
        game, connected = JOIN[join_key]
    except KeyError:
        await error(websocket, "Game not found")
        return

    connected.add(websocket)

    try:
        await replay(websocket, game)
        await play(websocket, game, PLAYER2, connected)

    finally:
        connected.remove(websocket)


async def watch(websocket, watch_key):
    """
    function to allow spectators to connect and watch the game being played
    :param websocket:
    :param watch_key:
    :return:
    """
    try:
        game, connected = WATCH[watch_key]
    except KeyError:
        await error(websocket, "Game not found")
        return

    connected.add(websocket)

    try:
        await websocket.wait_closed()
    finally:
        connected.remove(websocket)


async def play(websocket, game, player, connected):
    """
    function to allow each player send their moves
    :param websocket:
    :param game:
    :param player:
    :param connected:
    :return:
    """
    async for message in websocket:
        event = json.loads(message)
        assert(event['type'] == 'play')
        column = event['column']

        try:
            row = game.play(player=player, column=column)

        except RuntimeError as exc:
            event = {
                "type": "error",
                "message": str(exc)
            }
            await websocket.send(json.dumps(event))
            continue

        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row
        }

        websockets.broadcast(connected, json.dumps(event))

        if game.winner is not None:
            event = {
                "type": "win",
                "player": game.winner
            }
            websockets.broadcast(connected, json.dumps(event))


async def replay(websocket, game):
    """
    Send previous moves.

    """
    # Make a copy to avoid an exception if game.moves changes while iteration
    # is in progress. If a move is played while replay is running, moves will
    # be sent out of order but each move will be sent once and eventually the
    # UI will be consistent.
    for player, column, row in game.moves.copy():
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row,
        }
        await websocket.send(json.dumps(event))


async def handler(websocket):
    message = await websocket.recv()
    event = json.loads(message)
    assert event['type'] == "init"

    if "join" in event:
        await join(websocket, event["join"])
    elif "watch" in event:
        await watch(websocket, event["watch"])
    else:
        await start(websocket)


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
