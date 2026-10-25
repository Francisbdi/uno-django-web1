import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import Partida
from .uno_engine import (
    draw_player_card,
    init_game_state,
    pass_player_turn,
    play_player_card,
    serialize_state_for_client,
)

SESSION_KEY = 'uno_game_state'


def _get_game_state(request):
    """Recupera o estado atual da partida na sessão ou inicializa uma nova."""
    state = request.session.get(SESSION_KEY)
    if not state or 'discard_pile' not in state or 'player_hand' not in state:
        state = init_game_state()
        request.session[SESSION_KEY] = state
        request.session.modified = True
    return state


def _persist_finished_match(state):
    """
    Se a partida terminou e ainda não foi salva no banco SQLite,
    registra o resultado no model Partida.
    """
    if state.get('status') == 'finished' and not state.get('saved_to_db'):
        winner = state.get('winner')
        if winner in (Partida.VencedorChoices.JOGADOR, Partida.VencedorChoices.BOT):
            loser_cards = (
                len(state.get('bot_hand', []))
                if winner == Partida.VencedorChoices.JOGADOR
                else len(state.get('player_hand', []))
            )
            Partida.objects.create(
                vencedor=winner,
                turnos=state.get('turn_count', 1),
                cartas_restantes_perdedor=loser_cards,
            )
            state['saved_to_db'] = True


@ensure_csrf_cookie
def home(request):
    """Renderiza a interface principal do jogo UNO."""
    stats = Partida.obter_estatisticas()
    return render(request, 'core/index.html', {'initial_stats': stats})


@require_GET
def api_state(request):
    """Retorna o estado atual da partida da sessão e o placar geral do banco."""
    state = _get_game_state(request)
    stats = Partida.obter_estatisticas()
    return JsonResponse(serialize_state_for_client(state, stats=stats, ok=True))


@require_POST
def api_new_game(request):
    """Inicia uma nova partida de UNO limpando o estado anterior na sessão."""
    state = init_game_state()
    request.session[SESSION_KEY] = state
    request.session.modified = True
    stats = Partida.obter_estatisticas()
    return JsonResponse(serialize_state_for_client(state, stats=stats, ok=True))


@require_POST
def api_play_card(request):
    """Recebe o ID de uma carta da mão do jogador e processa a jogada."""
    state = _get_game_state(request)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        body = {}

    card_id = body.get('card_id') or request.POST.get('card_id')
    if not card_id:
        stats = Partida.obter_estatisticas()
        payload = serialize_state_for_client(state, stats=stats, ok=False)
        payload['error'] = 'ID da carta não informado.'
        return JsonResponse(payload, status=400)

    ok, msg, events = play_player_card(state, card_id)
    _persist_finished_match(state)
    request.session[SESSION_KEY] = state
    request.session.modified = True

    stats = Partida.obter_estatisticas()
    payload = serialize_state_for_client(state, stats=stats, events=events, ok=ok)
    if not ok:
        payload['error'] = msg
        return JsonResponse(payload, status=400)
    return JsonResponse(payload)


@require_POST
def api_draw_card(request):
    """Compra 1 carta do monte para o jogador."""
    state = _get_game_state(request)
    ok, msg, events = draw_player_card(state)
    _persist_finished_match(state)
    request.session[SESSION_KEY] = state
    request.session.modified = True

    stats = Partida.obter_estatisticas()
    payload = serialize_state_for_client(state, stats=stats, events=events, ok=ok)
    if not ok:
        payload['error'] = msg
        return JsonResponse(payload, status=400)
    return JsonResponse(payload)


@require_POST
def api_pass_turn(request):
    """Passa a vez após o jogador ter comprado 1 carta jogável e decidir não jogá-la."""
    state = _get_game_state(request)
    ok, msg, events = pass_player_turn(state)
    _persist_finished_match(state)
    request.session[SESSION_KEY] = state
    request.session.modified = True

    stats = Partida.obter_estatisticas()
    payload = serialize_state_for_client(state, stats=stats, events=events, ok=ok)
    if not ok:
        payload['error'] = msg
        return JsonResponse(payload, status=400)
    return JsonResponse(payload)


@require_POST
def api_clear_history(request):
    """Zera o histórico de partidas no banco SQLite."""
    Partida.objects.all().delete()
    state = _get_game_state(request)
    stats = Partida.obter_estatisticas()
    return JsonResponse(serialize_state_for_client(state, stats=stats, ok=True))
