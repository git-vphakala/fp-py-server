"""
Findpairs tables
"""
import uuid
from django.db import models
from django.db import transaction

# Create your models here.

class User(models.Model):
    """
    Registered Findpairs user
    """
    userName = models.TextField(default='', primary_key=True)
    def __str__(self):
        return self.userName

class Online(models.Model):
    """
    Logged on users
    """
    user = models.OneToOneField(User, default='', primary_key=True, on_delete=models.CASCADE)
    def __str__(self):
        return self.user.userName

class Game(models.Model):
    """
    Created games by a user
    """
    gameId = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    numPlayers = models.IntegerField(default=0)
    numPairs = models.IntegerField(default=0)
    creator = models.TextField(default='')
    state = models.TextField(default='')
    def __str__(self):
        return str(self.gameId) + ':' + str(self.numPlayers) + ':' + str(self.numPairs)

MATCH_COL_USER = 2
MATCH_COL_NUMPLAYER = 3
class Match(models.Model):
    """
    User which has joined to a game
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default='', on_delete=models.SET_DEFAULT)
    numPlayer = models.IntegerField(default=0)
    def __str__(self):
        return str(self.game)

def add_user(game, user):
    """
    Check if there is still a free place in the game and if so add user to the game attendants
    by inserting user to the Match table.
    """
    with transaction.atomic():
        match_list = list(Match.objects.filter(game_id=game.gameId).values_list())
        match_list_len = len(match_list)
        if match_list_len < game.numPlayers:
            match = Match(game=game, user=user, numPlayer=(game.numPlayers-len(match_list)))
            match.save()
            match_list_len += 1
        else:
            match_list_len = -1

    return match_list_len
