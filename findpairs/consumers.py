"""
findpairs/consumers.py
"""
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from . import handle_ws_messages

MESSAGE_TYPES = handle_ws_messages.MESSAGE_TYPES

class FindpairsConsumer(WebsocketConsumer):
    """
    Application's websocket API
    """
    myGroups = list()
    user_name = None

    def connect(self):
        self.accept()

    def disconnect(self, code):
        print("FindpairsConsumer.disconnect")
        response = handle_ws_messages.handler(handle_ws_messages.MESSAGE_TYPE_DISCONNECT,
                                              None, self)                
        if response["channelMessage"] is not None:
            print("disconnect: sending channelMessage, groupName=" + response["groupName"])
            async_to_sync(self.channel_layer.group_send)(response["groupName"], {
                'type':self.receive_channel_message.__name__,
                'message': response["channelMessage"]})
            response = response["wsMessage"]

        if response is not None:
            self.send(json.dumps(response))

    def receive(self, text_data=None, bytes_data=None):
        try:
            ws_message = json.loads(text_data)
        except json.JSONDecodeError:
            response = {
                "type":"error",
                "message":json.JSONDecodeError.__name__
            }
        else:
            message_type = ws_message["type"]
            message = ws_message["message"]
            if message_type is None:
                response = {
                    "type":"error",
                    "message":"no messageType"
                }
            elif message is None:
                response = {
                    "type":"error",
                    "message":"no message"
                }
            else:
                response = handle_ws_messages.handler(message_type, message, self)
                if "channelMessages" in response:
                    for i, channel_message in enumerate(response["channelMessages"]):
                        print("receive: sending channelMessages, groupName=" +
                              response["groupNames"][i])
                        async_to_sync(self.channel_layer.group_send)(response["groupNames"][i], {
                            'type': self.receive_channel_message.__name__,
                            'message': channel_message})
                elif response["channelMessage"] is not None:
                    if "receiving_method" in response:
                        receiving_method = response["receiving_method"]
                    else:
                        receiving_method = self.receive_channel_message.__name__
                    print("receive: sending channelMessage, groupName=" + response["groupName"])
                    async_to_sync(self.channel_layer.group_send)(response["groupName"], {
                        'type':receiving_method,
                        'message': response["channelMessage"]})
                response = response["wsMessage"]

        if response is not None:
            self.send(json.dumps(response))

    def receive_channel_message(self, event):
        """
        Relay a group-message to the browser via the websocket
        """
        message = event["message"]
        print("FindpairsConsumer.receiveChannelMessage, message=" + json.dumps(message))
        self.send(json.dumps(message))

    def receive_channel_message_play_game(self, event):
        """
        Receive play-game message
        """
        try:
            message = json.dumps(event["message"])
        except TypeError:
            print("receive_channel_message_play_game: json.dumps TypeError, user_name=" +
                  self.user_name)
        print("receive_channel_message_play_game: " + self.user_name)
        print("message=" + message)
        self.send(message)

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        print("GameConsumer.disconnect")

    def receive(self, text_data=None, bytes_data=None):
        try:
            ws_message = json.loads(text_data)
        except json.JSONDecodeError:
            response = {
                "type":"error",
                "message":json.JSONDecodeError.__name__
            }
            self.send(json.dumps(response))
            return

        print("GameConsumer.receive: " + text_data)
