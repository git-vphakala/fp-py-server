"""
Views
"""
from django.shortcuts import render
from django.utils.safestring import mark_safe
import json

# Create your views here.
from django.http import HttpResponse


def index(request):
    return HttpResponse(render(request, 'findpairs/index.html'))

def game(request, game_id):
    """
    View to play the game
    """
    return HttpResponse(render(request, 'findpairs/game.html'), {
        'game_id_json': mark_safe(json.dumps(game_id))
    })

def logon(request):
    return HttpResponse('Logon view for userName=%s' % request.POST['username'])

def user(request, userName):
    return HttpResponse("You are user %s." % userName)