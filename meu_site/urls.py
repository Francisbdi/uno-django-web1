from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('api/state/', views.api_state, name='api_state'),
    path('api/new-game/', views.api_new_game, name='api_new_game'),
    path('api/play-card/', views.api_play_card, name='api_play_card'),
    path('api/draw-card/', views.api_draw_card, name='api_draw_card'),
    path('api/pass-turn/', views.api_pass_turn, name='api_pass_turn'),
    path('api/clear-history/', views.api_clear_history, name='api_clear_history'),
]
