from django.contrib import admin
from .models import Partida


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'vencedor', 'turnos', 'cartas_restantes_perdedor', 'data_hora')
    list_filter = ('vencedor', 'data_hora')
    ordering = ('-data_hora',)
    readonly_fields = ('data_hora',)
