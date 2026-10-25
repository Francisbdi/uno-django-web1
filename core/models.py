from django.db import models
from django.utils import timezone


class Partida(models.Model):
    """
    Armazena o histórico de partidas finalizadas do jogo UNO (Jogador vs Bot).
    """

    class VencedorChoices(models.TextChoices):
        JOGADOR = 'JOGADOR', 'Jogador'
        BOT = 'BOT', 'Computador (Bot)'

    vencedor = models.CharField(
        max_length=15,
        choices=VencedorChoices.choices,
        verbose_name='Vencedor',
    )
    turnos = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantidade de Turnos',
    )
    cartas_restantes_perdedor = models.PositiveIntegerField(
        default=0,
        verbose_name='Cartas Restantes do Adversário',
    )
    data_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data e Hora',
    )

    class Meta:
        verbose_name = 'Partida de UNO'
        verbose_name_plural = 'Partidas de UNO'
        ordering = ['-data_hora']

    def __str__(self):
        data_local = timezone.localtime(self.data_hora).strftime('%d/%m/%Y %H:%M')
        return f"{self.get_vencedor_display()} venceu em {self.turnos} turnos ({data_local})"

    @classmethod
    def obter_estatisticas(cls, limite_historico=10):
        """
        Retorna o placar geral acumulado e as últimas partidas registradas no banco SQLite.
        """
        total = cls.objects.count()
        vitorias_jogador = cls.objects.filter(vencedor=cls.VencedorChoices.JOGADOR).count()
        vitorias_bot = cls.objects.filter(vencedor=cls.VencedorChoices.BOT).count()
        taxa_vitoria = round((vitorias_jogador / total) * 100, 1) if total > 0 else 0.0

        ultimas_partidas = cls.objects.all()[:limite_historico]
        historico = []
        for p in ultimas_partidas:
            data_local = timezone.localtime(p.data_hora)
            historico.append({
                'id': p.id,
                'vencedor': p.vencedor,
                'vencedor_nome': p.get_vencedor_display(),
                'turnos': p.turnos,
                'cartas_restantes_perdedor': p.cartas_restantes_perdedor,
                'data_hora': data_local.strftime('%d/%m/%Y às %H:%M'),
            })

        return {
            'total_partidas': total,
            'vitorias_jogador': vitorias_jogador,
            'vitorias_bot': vitorias_bot,
            'taxa_vitoria': taxa_vitoria,
            'historico': historico,
        }
