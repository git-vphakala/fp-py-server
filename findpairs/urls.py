from django.urls import path

from . import views

app_name = 'findpairs'

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:game_id>/', views.game, name='game'),
    path('logon', views.logon, name='logon'),
    path('<userName>/', views.user, name='user')
]
