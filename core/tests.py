import json
from django.test import Client, TestCase
from django.urls import reverse

from .models import Partida
from .uno_engine import (
    create_deck,
    init_game_state,
    is_card_playable,
    play_player_card,
)
from .views import SESSION_KEY


class UnoEngineAndApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_deck_composition(self):
        """O baralho deve conter 100 cartas com 4 cores, números 0-9 e cartas de ação."""
        deck = create_deck()
        self.assertEqual(len(deck), 100)
        colors = {c['color'] for c in deck}
        self.assertEqual(colors, {'red', 'blue', 'green', 'yellow'})
        values = {c['value'] for c in deck}
        self.assertTrue({'0', '9', 'skip', 'reverse', 'draw2'}.issubset(values))

    def test_initial_game_state(self):
        """A partida deve iniciar com 7 cartas para cada jogador e 1 carta numérica na mesa."""
        state = init_game_state()
        self.assertEqual(len(state['player_hand']), 7)
        self.assertEqual(len(state['bot_hand']), 7)
        self.assertEqual(len(state['discard_pile']), 1)
        self.assertEqual(len(state['deck']), 85)
        self.assertEqual(state['discard_pile'][-1]['type'], 'number')

    def test_card_matching_rules(self):
        """Uma carta só pode ser jogada se combinar em cor ou em número/símbolo."""
        top = {'color': 'red', 'value': '5'}
        self.assertTrue(is_card_playable({'color': 'red', 'value': '9'}, top))
        self.assertTrue(is_card_playable({'color': 'blue', 'value': '5'}, top))
        self.assertFalse(is_card_playable({'color': 'green', 'value': '2'}, top))

    def test_draw2_card_effect_in_1v1(self):
        """Jogar +2 deve fazer o Bot comprar 2 cartas e manter a vez com o jogador."""
        state = init_game_state()
        state['discard_pile'] = [{
            'id': 'red_5_1', 'color': 'red', 'color_name': 'Vermelho',
            'value': '5', 'label': '5', 'action_title': 'Número 5',
            'display_name': '5 Vermelho', 'type': 'number',
        }]
        state['player_hand'] = [
            {
                'id': 'red_draw2_99', 'color': 'red', 'color_name': 'Vermelho',
                'value': 'draw2', 'label': '+2', 'action_title': 'Comprar +2',
                'display_name': 'Comprar +2 Vermelho', 'type': 'action',
            },
            {
                'id': 'blue_1_98', 'color': 'blue', 'color_name': 'Azul',
                'value': '1', 'label': '1', 'action_title': 'Número 1',
                'display_name': '1 Azul', 'type': 'number',
            },
        ]
        initial_bot_cards = len(state['bot_hand'])
        ok, _, _ = play_player_card(state, 'red_draw2_99')
        self.assertTrue(ok)
        self.assertEqual(len(state['bot_hand']), initial_bot_cards + 2)
        self.assertEqual(state['turn'], 'player')

    def test_player_victory_persists_in_sqlite(self):
        """Quando o jogador joga sua última carta, vence a partida e salva no banco SQLite."""
        self.client.get(reverse('api_state'))
        session = self.client.session
        state = session[SESSION_KEY]
        state['discard_pile'] = [{
            'id': 'green_4_1', 'color': 'green', 'color_name': 'Verde',
            'value': '4', 'label': '4', 'action_title': 'Número 4',
            'display_name': '4 Verde', 'type': 'number',
        }]
        state['player_hand'] = [{
            'id': 'green_9_99', 'color': 'green', 'color_name': 'Verde',
            'value': '9', 'label': '9', 'action_title': 'Número 9',
            'display_name': '9 Verde', 'type': 'number',
        }]
        session[SESSION_KEY] = state
        session.save()

        response = self.client.post(
            reverse('api_play_card'),
            data=json.dumps({'card_id': 'green_9_99'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'finished')
        self.assertEqual(payload['winner'], 'JOGADOR')
        self.assertEqual(Partida.objects.count(), 1)
        partida = Partida.objects.first()
        self.assertEqual(partida.vencedor, Partida.VencedorChoices.JOGADOR)
