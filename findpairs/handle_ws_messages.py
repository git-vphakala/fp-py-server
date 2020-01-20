""" handle_ws_messages.py """
import uuid
from asgiref.sync import async_to_sync
from . import models
from . import game_logic

MESSGE_TYPE_ERROR = "error"
MESSGE_TYPE_MYNAME = "my-name"
MESSGE_TYPE_MYNAMEACK = "my-name-ack"
MESSGE_TYPE_USERLIST = "online-list"
MESSAGE_TYPE_DISCONNECT = "disconnect"
MESSAGE_TYPE_CREATE_GAME = "create-game"
MESSAGE_TYPE_CREATE_GAME_ACK = "create-game-ack"
MESSAGE_TYPE_GAMELIST = "game-list"
MESSAGE_TYPE_JOIN_GAME = "join-game"
MESSAGE_TYPE_JOIN_GAME_ACK = "join-game-ack"
MESSGE_TYPE_START_GAME = "start-game"
MESSAGE_TYPE_CARD_CLICK = "card-click"
MESSAGE_TYPE_CARD_CLICK_ACK = "card-click-ack"
MESSAGE_TYPE_GAME_STATE = "game-state"
MESSAGE_TYPES = {MESSGE_TYPE_ERROR, MESSGE_TYPE_MYNAME, MESSGE_TYPE_USERLIST,
                 MESSAGE_TYPE_DISCONNECT, MESSAGE_TYPE_CREATE_GAME,
                 MESSAGE_TYPE_JOIN_GAME,
                 MESSAGE_TYPE_CARD_CLICK}

MESSAGE_RC_OK = 0
MESSAGE_RC_USER_DOES_NOT_EXIST = 1
MESSAGE_RC_GAME_IS_FULL = 2
MESSAGE_RC_GAME_NOT_FOUND = 3

CHANNEL_GROUP_NAME_ONLINELIST = "onlineList"


def create_game_list_message():
    """
    Create a list of games which have not started yet
    """
    game_list = list(models.Game.objects.filter(state='').values_list())
    for game_tuple in game_list:
        i = game_list.index(game_tuple)
        game_mutable = list(game_tuple)
        game_mutable[0] = str(game_mutable[0]) # stringify gameId
        game_tuple = tuple(game_mutable)
        game_list[i] = game_tuple

    return {"type":MESSAGE_TYPE_GAMELIST, "message":game_list}

def handle_my_name(message, consumer):
    """
    handler for my-name message
    """
    group_name = ''
    group_names = []
    user_name = message
    ws_message = None
    channel_messages = []

    try:
        user = models.User.objects.get(pk=user_name)
    except models.User.DoesNotExist:
        print(handle_my_name.__name__ + ": user does not exist, userName=" + user_name)
        ws_message = {"type": MESSGE_TYPE_MYNAMEACK,
                      "rc": MESSAGE_RC_USER_DOES_NOT_EXIST, "message": user_name}
    else:
        online_user = models.Online(user=user)
        online_user.save()
        consumer.user_name = user.userName

        # websocketconsumer can be reached via the associated userName
        group_name = consumer.user_name
        consumer.myGroups.append(group_name)
        async_to_sync(consumer.channel_layer.group_add)(group_name, consumer.channel_name)

        group_names.append(CHANNEL_GROUP_NAME_ONLINELIST)
        consumer.myGroups.append(group_names[-1])
        print(handle_my_name.__name__ +
              ": groupName=" + group_names[-1] +
              ", user_name=" + user_name +
              ", user.userName=" + user.userName)
        async_to_sync(consumer.channel_layer.group_add)(group_names[-1], consumer.channel_name)
        online_list = list(models.Online.objects.all().values_list('user', flat=True))

        channel_messages = []
        channel_messages.append({"type":MESSGE_TYPE_USERLIST, "message":online_list})
        group_names.append(CHANNEL_GROUP_NAME_ONLINELIST)
        channel_messages.append(create_game_list_message())

        ws_message = {"type":MESSGE_TYPE_MYNAMEACK, "rc": MESSAGE_RC_OK, "message": user.userName}

    return {"channelMessages": channel_messages, "groupNames":group_names, "wsMessage":ws_message}

def handle_disconnect(consumer):
    """
    handler for disconnect of the websocket
    """
    group_name = CHANNEL_GROUP_NAME_ONLINELIST
    ws_message = None
    channel_message = None

    for group_name in consumer.myGroups:
        async_to_sync(consumer.channel_layer.group_discard)(group_name, consumer.channel_name)

    try:
        user = models.User.objects.get(pk=consumer.user_name)
    except models.User.DoesNotExist:
        print("warning: User has not user_name=" + consumer.user_name)
        # no message is sent
        return {"channelMessage": channel_message, "groupName":group_name, "wsMessage":ws_message}

    try:
        online_user = models.Online.objects.get(pk=user)
    except models.Online.DoesNotExist:
        print("warning: Online has not User for user_name=" + consumer.user_name)
    else:
        online_user.delete()
        online_list = list(models.Online.objects.all().values_list('user', flat=True))
        if online_list:
            channel_message = {"type":MESSGE_TYPE_USERLIST, "message":online_list}

    return {"channelMessage": channel_message, "groupName":group_name, "wsMessage":ws_message}

def handle_create_game(create_game_message):
    """
    handler for create-game message
    create_game message = { user:<str>, playerId:<int>, numPairs:<int>, numPlayers:<int> },
        where playerId:turn = [ 0, 1, ... numPlayers-1 ]
    """
    channel_message = None
    group_name = CHANNEL_GROUP_NAME_ONLINELIST
    ws_message = None

    user_name = create_game_message["user"]
    try:
        models.User.objects.get(pk=user_name)
    except models.User.DoesNotExist:
        print("warning: handle_create_game: User has not user_name=" + user_name)
        ws_message = {
            "type":"error",
            "message":MESSAGE_TYPE_CREATE_GAME + ':User has not user_name=' + user_name
        }
        return {"channelMessage": channel_message, "groupName":group_name, "wsMessage":ws_message}

    num_pairs = create_game_message["numPairs"]
    num_players = create_game_message["numPlayers"]
    game = models.Game(numPlayers=num_players, numPairs=num_pairs, creator=user_name)
    game.save()

    channel_message = create_game_list_message()
    ws_message = {"type": MESSAGE_TYPE_CREATE_GAME_ACK, "rc": MESSAGE_RC_OK, "message": user_name}

    return {"channelMessage": channel_message, "groupName":group_name, "wsMessage":ws_message}

def handle_join_game(message, consumer):
    """
    handler for join-game message
    message = [gameId, numPlayers, numPairs]
    """
    channel_messages = []
    group_names = []
    ws_message = None

    try:
        user = models.User.objects.get(pk=consumer.user_name)
    except models.User.DoesNotExist:
        print("warning: handle_join_game: User has not user_name=" + consumer.user_name)
        ws_message = {
            "type":"error",
            "message":MESSAGE_TYPE_JOIN_GAME + ':User has not user_name=' + consumer.user_name
        }
        return {"channelMessage": None, "groupName":'', "wsMessage":ws_message}
    # read game
    try:
        game = models.Game.objects.get(pk=uuid.UUID(message[0]))
    except models.Game.DoesNotExist:
        print("warning: handle_join_game: user_name=" + user.userName +
              ", Game has not gameId=" + message[0])
        ws_message = {
            "type":"error",
            "message":MESSAGE_TYPE_JOIN_GAME + ':Game has not gameId=' + message[0]
        }
        return {"channelMessage": None, "groupName":'', "wsMessage":ws_message}
    ret_val = models.add_user(game, user)
    if ret_val < 0:
        print("handle_join_game: user_name=" + user.userName +
              ", Game is full, gameId=" + str(game.gameId))
        ws_message = {
            "type": MESSAGE_TYPE_JOIN_GAME_ACK, "rc": MESSAGE_RC_GAME_IS_FULL,
            "message": message
        }
        return {"channelMessage": None, "groupName":'', "wsMessage":ws_message}

    async_to_sync(consumer.channel_layer.group_add)(str(game.gameId), consumer.channel_name)
    ws_message = {
        "type": MESSAGE_TYPE_JOIN_GAME_ACK, "rc": MESSAGE_RC_OK,
        "message": message
    }
    if ret_val == game.numPlayers:
        group_names.append(str(game.gameId))
        # receiving_method = consumer.receive_channel_message_play_game.__name__
        game_logic.init(game)
        game.save()
        channel_messages.append({
            "type": MESSGE_TYPE_START_GAME,
            "message": game.state
        })
        group_names.append(CHANNEL_GROUP_NAME_ONLINELIST)
        channel_messages.append(create_game_list_message())

    return {"channelMessages": channel_messages, # "receiving_method":receiving_method,
            "groupNames":group_names, "wsMessage":ws_message}

def handle_card_click(message, consumer):
    """
    Handler for card-click message
    message = {gameId:<str>, userName:<str>, cardI:<int>}
    """
    channel_message = None
    group_name = ''
    ws_message = None

    try:
        game = models.Game.objects.get(pk=uuid.UUID(message["gameId"]))
    except models.Game.DoesNotExist:
        print("error: handle_card_click: user_name=" + consumer.userName +
              ", Game has not gameId=" + message["gameId"])
        ws_message = {
            "type":"error",
            "message":MESSAGE_TYPE_CARD_CLICK + ':Game has not gameId=' + message["gameId"]
        }
        return {"channelMessage": channel_message, "groupName":group_name, "wsMessage":ws_message}

    prev_state = game.state
    game_logic.play(game, message)
    if game.state != prev_state:
        game.save()
        group_name = str(game.gameId)
        channel_message = {
            "type": MESSAGE_TYPE_GAME_STATE,
            "message": game.state
        }

    return {"channelMessage": channel_message, # "receiving_method":receiving_method,
            "groupName":group_name, "wsMessage":ws_message}


def handler(message_type, message, consumer):
    """
    ws-message handler
    """
    response = None

    if message_type not in MESSAGE_TYPES:
        return {
            "wsMessage":{
                "type":"error",
                "message": "Unknown messageType=" + message_type
            },
            "channelMessage": None
        }

    if message_type == MESSGE_TYPE_MYNAME:
        response = handle_my_name(message, consumer)
    if message_type == MESSAGE_TYPE_DISCONNECT:
        response = handle_disconnect(consumer)
    if message_type == MESSAGE_TYPE_CREATE_GAME:
        response = handle_create_game(message)
    if message_type == MESSAGE_TYPE_JOIN_GAME:
        response = handle_join_game(message, consumer)
    if message_type == MESSAGE_TYPE_CARD_CLICK:
        response = handle_card_click(message, consumer)

    if response is None:
        return {
            "wsMessage": {
                "type":"error",
                "message": "Unhandled messageType=" + message_type
            },
            "channelMessage": None
        }
    return response
