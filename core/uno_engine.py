import random
from collections import Counter

COLORS = [
    ('red', 'Vermelho'),
    ('blue', 'Azul'),
    ('green', 'Verde'),
    ('yellow', 'Amarelo'),
]

ACTION_TYPES = [
    ('skip', '⊘', 'Pular Vez'),
    ('reverse', '⇄', 'Inverter'),
    ('draw2', '+2', 'Comprar +2'),
]


def create_deck():
    """
    Cria o baralho clássico colorido de UNO com 100 cartas:
    - Para cada uma das 4 cores (Vermelho, Azul, Verde, Amarelo):
      - 1 carta de número 0
      - 2 cartas de cada número de 1 a 9
      - 2 cartas de Pular Vez (skip)
      - 2 cartas de Inverter (reverse)
      - 2 cartas de Comprar 2 (draw2)
    """
    deck = []
    card_seq = 1

    for color_code, color_name in COLORS:
        # Uma carta '0' por cor
        deck.append({
            'id': f'{color_code}_0_{card_seq}',
            'color': color_code,
            'color_name': color_name,
            'value': '0',
            'label': '0',
            'action_title': 'Número 0',
            'display_name': f'0 {color_name}',
            'type': 'number',
        })
        card_seq += 1

        # Duas cartas de 1 a 9 por cor
        for num in range(1, 10):
            for _ in range(2):
                deck.append({
                    'id': f'{color_code}_{num}_{card_seq}',
                    'color': color_code,
                    'color_name': color_name,
                    'value': str(num),
                    'label': str(num),
                    'action_title': f'Número {num}',
                    'display_name': f'{num} {color_name}',
                    'type': 'number',
                })
                card_seq += 1

        # Duas cartas de cada ação básica por cor
        for action_code, symbol, action_title in ACTION_TYPES:
            for _ in range(2):
                deck.append({
                    'id': f'{color_code}_{action_code}_{card_seq}',
                    'color': color_code,
                    'color_name': color_name,
                    'value': action_code,
                    'label': symbol,
                    'action_title': action_title,
                    'display_name': f'{action_title} {color_name}',
                    'type': 'action',
                })
                card_seq += 1

    random.shuffle(deck)
    return deck


def is_card_playable(card, top_card):
    """
    Verifica se uma carta pode ser jogada sobre a carta do topo do descarte.
    Regra: deve combinar em COR ou em NÚMERO/SÍMBOLO.
    """
    if not card or not top_card:
        return False
    return card['color'] == top_card['color'] or card['value'] == top_card['value']


def init_game_state():
    """
    Inicializa uma nova partida de UNO 1v1 (Jogador vs Computador).
    Cada jogador começa com 7 cartas e 1 carta numérica inicia o monte de descarte.
    """
    deck = create_deck()
    player_hand = [deck.pop() for _ in range(7)]
    bot_hand = [deck.pop() for _ in range(7)]

    # Garante que a primeira carta da mesa seja numérica para um início limpo
    top_card = deck.pop()
    while top_card['type'] != 'number':
        deck.insert(0, top_card)
        random.shuffle(deck)
        top_card = deck.pop()

    discard_pile = [top_card]

    return {
        'deck': deck,
        'discard_pile': discard_pile,
        'player_hand': player_hand,
        'bot_hand': bot_hand,
        'turn': 'player',
        'turn_count': 1,
        'status': 'playing',
        'winner': None,
        'has_drawn_this_turn': False,
        'saved_to_db': False,
        'message': f"Partida iniciada! Carta na mesa: {top_card['display_name']}. Sua vez!",
        'log': [
            f"Partida iniciada! Cada jogador recebeu 7 cartas.",
            f"Carta inicial na mesa: {top_card['display_name']}.",
        ],
    }


def append_log(state, text):
    """Adiciona uma mensagem ao histórico recente da partida (mantendo as últimas 25 entradas)."""
    state.setdefault('log', []).append(text)
    if len(state['log']) > 25:
        state['log'] = state['log'][-25:]


def draw_cards_from_deck(state, count=1):
    """
    Compra `count` cartas do monte. Se o monte acabar, reembaralha o descarte
    (mantendo apenas a carta do topo na mesa).
    """
    drawn = []
    for _ in range(count):
        if not state['deck']:
            if len(state['discard_pile']) > 1:
                top_card = state['discard_pile'][-1]
                recycled = state['discard_pile'][:-1]
                random.shuffle(recycled)
                state['deck'] = recycled
                state['discard_pile'] = [top_card]
                append_log(state, '🔄 O monte de compra acabou! A pilha de descarte foi reembaralhada.')
            else:
                # Caso extremo onde quase todas as cartas estão nas mãos
                state['deck'] = create_deck()
        drawn.append(state['deck'].pop())
    return drawn


def choose_best_bot_card(playable_cards, bot_hand, player_card_count):
    """
    IA do Bot: escolhe estrategicamente a melhor carta dentre as jogáveis.
    Prioridades:
    1. Se o jogador tiver poucas cartas (<= 3), prioriza +2, Pular e Inverter para impedir a vitória.
    2. Prioriza cartas de ação (+2, Pular, Inverter) pois no 1v1 garantem jogar novamente em seguida.
    3. Prioriza a cor que o Bot possui em maior quantidade na mão.
    4. Descarta números mais altos primeiro como critério de desempate.
    """
    color_counts = Counter(c['color'] for c in bot_hand)

    def card_score(card):
        score = 0
        # Bônus por quantidade da mesma cor na mão do bot
        score += color_counts[card['color']] * 5

        if card['value'] == 'draw2':
            score += 45 if player_card_count <= 3 else 22
        elif card['value'] in ('skip', 'reverse'):
            score += 35 if player_card_count <= 3 else 18
        else:
            score += int(card['value'])
        return score

    return max(playable_cards, key=card_score)


def make_step_snapshot(state, actor, action, description, card=None):
    """
    Cria um snapshot do estado para animação passo a passo no frontend.
    """
    top_card = state['discard_pile'][-1]
    return {
        'actor': actor,
        'action': action,
        'description': description,
        'card': card,
        'top_card': top_card,
        'bot_card_count': len(state['bot_hand']),
        'player_card_count': len(state['player_hand']),
        'player_hand_snapshot': [dict(c) for c in state['player_hand']],
        'deck_count': len(state['deck']),
        'turn_count': state['turn_count'],
        'uno_alert': (
            'BOT' if len(state['bot_hand']) == 1
            else ('JOGADOR' if len(state['player_hand']) == 1 else None)
        ),
    }


def apply_bot_card_play(state, chosen_card, events, drew_before_play=False):
    """
    Executa o descarte de uma carta pelo Bot e aplica seus efeitos.
    Retorna True se o Bot deve jogar novamente (carta de ação em 1v1), ou False se a vez passa ao jogador.
    """
    state['bot_hand'] = [c for c in state['bot_hand'] if c['id'] != chosen_card['id']]
    state['discard_pile'].append(chosen_card)
    state['turn_count'] += 1

    prefix = 'Após comprar, o Bot jogou' if drew_before_play else 'Bot jogou'
    uno_suffix = ' 🔔 O Bot gritou UNO (1 carta restante)!' if len(state['bot_hand']) == 1 else ''

    # Verifica se o Bot venceu a partida
    if len(state['bot_hand']) == 0:
        state['status'] = 'finished'
        state['winner'] = 'BOT'
        state['turn'] = 'none'
        msg = f"🤖 Fim de jogo! {prefix} {chosen_card['display_name']} e ficou sem cartas. O Bot venceu!"
        state['message'] = msg
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'bot', 'win', msg, chosen_card))
        return False

    # Aplica efeitos das cartas de ação no modo 1v1
    if chosen_card['value'] == 'skip':
        msg = f"🤖 {prefix} {chosen_card['display_name']}! Sua vez foi pulada.{uno_suffix}"
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'bot', 'play_action', msg, chosen_card))
        return True  # Bot joga novamente

    if chosen_card['value'] == 'reverse':
        msg = f"🤖 {prefix} {chosen_card['display_name']}! No 1x1 a vez volta para o Bot.{uno_suffix}"
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'bot', 'play_action', msg, chosen_card))
        return True  # Bot joga novamente

    if chosen_card['value'] == 'draw2':
        drawn_for_player = draw_cards_from_deck(state, 2)
        state['player_hand'].extend(drawn_for_player)
        nomes_compradas = ', '.join(c['display_name'] for c in drawn_for_player)
        msg = (
            f"🤖 {prefix} {chosen_card['display_name']}! "
            f"Você comprou +2 cartas ({nomes_compradas}) e perdeu a vez.{uno_suffix}"
        )
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'bot', 'play_draw2', msg, chosen_card))
        return True  # Bot joga novamente

    # Carta numérica normal: passa a vez para o jogador
    msg = f"🤖 {prefix} {chosen_card['display_name']}.{uno_suffix} Sua vez!"
    state['message'] = msg
    append_log(state, msg)
    events.append(make_step_snapshot(state, 'bot', 'play', msg, chosen_card))
    return False


def execute_bot_turns(state, events):
    """
    Executa o(s) turno(s) do Bot de forma inteligente e automática.
    Caso o Bot jogue Pular, Inverter ou +2, ele continua jogando até passar a vez ou vencer.
    """
    safety_counter = 0
    while state['status'] == 'playing' and state['turn'] == 'bot' and safety_counter < 30:
        safety_counter += 1
        top_card = state['discard_pile'][-1]
        playable = [c for c in state['bot_hand'] if is_card_playable(c, top_card)]

        if playable:
            chosen = choose_best_bot_card(playable, state['bot_hand'], len(state['player_hand']))
            keep_turn = apply_bot_card_play(state, chosen, events, drew_before_play=False)
            if not keep_turn and state['status'] == 'playing':
                state['turn'] = 'player'
                state['has_drawn_this_turn'] = False
                break
        else:
            # Bot não tem carta válida: compra 1 carta do monte
            drawn = draw_cards_from_deck(state, 1)[0]
            state['bot_hand'].append(drawn)

            if is_card_playable(drawn, top_card):
                draw_msg = '🤖 Bot não tinha carta compatível e comprou 1 carta do monte...'
                append_log(state, draw_msg)
                events.append(make_step_snapshot(state, 'bot', 'draw', draw_msg))

                keep_turn = apply_bot_card_play(state, drawn, events, drew_before_play=True)
                if not keep_turn and state['status'] == 'playing':
                    state['turn'] = 'player'
                    state['has_drawn_this_turn'] = False
                    break
            else:
                state['turn_count'] += 1
                state['turn'] = 'player'
                state['has_drawn_this_turn'] = False
                msg = '🤖 Bot não tinha jogada válida, comprou 1 carta e passou a vez. Sua vez!'
                state['message'] = msg
                append_log(state, msg)
                events.append(make_step_snapshot(state, 'bot', 'draw_pass', msg))
                break


def play_player_card(state, card_id):
    """
    Processa a jogada de uma carta escolhida pelo jogador humano.
    """
    events = []
    if state['status'] != 'playing':
        return False, 'A partida já foi encerrada. Inicie um novo jogo!', events

    if state['turn'] != 'player':
        return False, 'Aguarde! Não é a sua vez de jogar.', events

    card = next((c for c in state['player_hand'] if c['id'] == card_id), None)
    if not card:
        return False, 'Carta não encontrada na sua mão.', events

    top_card = state['discard_pile'][-1]
    if not is_card_playable(card, top_card):
        return (
            False,
            f"Jogada inválida! {card['display_name']} não combina em cor nem em número/símbolo com {top_card['display_name']}.",
            events,
        )

    # Remove da mão do jogador e coloca no topo do descarte
    state['player_hand'] = [c for c in state['player_hand'] if c['id'] != card_id]
    state['discard_pile'].append(card)
    state['turn_count'] += 1
    state['has_drawn_this_turn'] = False

    uno_suffix = ' 🔥 UNO! Você está com apenas 1 carta!' if len(state['player_hand']) == 1 else ''

    # Condição de vitória do jogador
    if len(state['player_hand']) == 0:
        state['status'] = 'finished'
        state['winner'] = 'JOGADOR'
        state['turn'] = 'none'
        msg = f"🏆 Vitória! Você jogou {card['display_name']}, esvaziou sua mão e venceu a partida!"
        state['message'] = msg
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'player', 'win', msg, card))
        return True, msg, events

    # Aplica efeitos de cartas de ação do jogador (em 1v1, Pular, Inverter e +2 mantêm a vez com o jogador)
    if card['value'] == 'skip':
        state['turn'] = 'player'
        msg = f"⚡ Você jogou {card['display_name']}! A vez do Bot foi pulada — jogue novamente!{uno_suffix}"
        state['message'] = msg
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'player', 'play_action', msg, card))
        return True, msg, events

    if card['value'] == 'reverse':
        state['turn'] = 'player'
        msg = f"🔄 Você jogou {card['display_name']}! No duelo 1x1 a ordem volta para você — jogue novamente!{uno_suffix}"
        state['message'] = msg
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'player', 'play_action', msg, card))
        return True, msg, events

    if card['value'] == 'draw2':
        drawn_for_bot = draw_cards_from_deck(state, 2)
        state['bot_hand'].extend(drawn_for_bot)
        state['turn'] = 'player'
        msg = f"💥 Você jogou {card['display_name']}! O Bot comprou +2 cartas e perdeu a vez — jogue novamente!{uno_suffix}"
        state['message'] = msg
        append_log(state, msg)
        events.append(make_step_snapshot(state, 'player', 'play_draw2', msg, card))
        return True, msg, events

    # Carta numérica: passa a vez para o Bot
    player_msg = f"Você jogou {card['display_name']}.{uno_suffix}"
    append_log(state, player_msg)
    events.append(make_step_snapshot(state, 'player', 'play', player_msg, card))

    state['turn'] = 'bot'
    execute_bot_turns(state, events)
    return True, state['message'], events


def draw_player_card(state):
    """
    Jogador clica no monte para comprar 1 carta.
    - Se a carta comprada for jogável, o jogador pode jogá-la imediatamente ou clicar em 'Passar Vez'.
    - Se a carta comprada não combinar com o topo, a vez passa automaticamente para o Bot.
    """
    events = []
    if state['status'] != 'playing':
        return False, 'A partida já foi encerrada. Inicie um novo jogo!', events

    if state['turn'] != 'player':
        return False, 'Aguarde! Não é a sua vez de jogar.', events

    if state.get('has_drawn_this_turn'):
        return (
            False,
            'Você já comprou 1 carta neste turno! Jogue uma carta válida ou clique em "Passar Vez".',
            events,
        )

    drawn_card = draw_cards_from_deck(state, 1)[0]
    state['player_hand'].append(drawn_card)
    top_card = state['discard_pile'][-1]

    if is_card_playable(drawn_card, top_card):
        state['has_drawn_this_turn'] = True
        msg = (
            f"🃏 Você comprou {drawn_card['display_name']}! "
            f"Ela combina com a mesa — clique nela para jogar ou em 'Passar Vez'."
        )
        state['message'] = msg
        append_log(state, f"Você comprou {drawn_card['display_name']} (jogável).")
        events.append(make_step_snapshot(state, 'player', 'draw_playable', msg, drawn_card))
        return True, msg, events

    # Carta comprada não é jogável -> passa a vez para o Bot automaticamente
    state['has_drawn_this_turn'] = False
    state['turn_count'] += 1
    draw_msg = f"🃏 Você comprou {drawn_card['display_name']} (não combina com {top_card['display_name']}). Vez do Bot!"
    append_log(state, draw_msg)
    events.append(make_step_snapshot(state, 'player', 'draw_pass', draw_msg, drawn_card))

    state['turn'] = 'bot'
    execute_bot_turns(state, events)
    return True, state['message'], events


def pass_player_turn(state):
    """
    Permite ao jogador passar a vez após ter comprado 1 carta jogável e optar por mantê-la.
    """
    events = []
    if state['status'] != 'playing' or state['turn'] != 'player':
        return False, 'Não é possível passar a vez agora.', events

    if not state.get('has_drawn_this_turn'):
        return False, 'Você precisa comprar 1 carta do monte antes de passar a vez!', events

    state['has_drawn_this_turn'] = False
    state['turn_count'] += 1
    pass_msg = '⏭️ Você optou por passar a vez após comprar. Vez do Bot!'
    append_log(state, pass_msg)
    events.append(make_step_snapshot(state, 'player', 'pass', pass_msg))

    state['turn'] = 'bot'
    execute_bot_turns(state, events)
    return True, state['message'], events


def serialize_state_for_client(state, stats=None, events=None, ok=True):
    """
    Prepara o payload JSON seguro para o frontend (sem revelar as cartas da mão do Bot).
    Marca também quais cartas na mão do jogador são válidas para jogar no momento.
    """
    top_card = state['discard_pile'][-1]
    is_player_turn = state['status'] == 'playing' and state['turn'] == 'player'

    player_hand_annotated = []
    for card in state['player_hand']:
        c_copy = dict(card)
        c_copy['playable'] = bool(is_player_turn and is_card_playable(card, top_card))
        player_hand_annotated.append(c_copy)

    has_playable_card = any(c['playable'] for c in player_hand_annotated)

    return {
        'ok': ok,
        'status': state['status'],
        'winner': state['winner'],
        'turn': state['turn'],
        'turn_count': state['turn_count'],
        'has_drawn_this_turn': state.get('has_drawn_this_turn', False),
        'has_playable_card': has_playable_card,
        'message': state['message'],
        'top_card': top_card,
        'deck_count': len(state['deck']),
        'discard_count': len(state['discard_pile']),
        'bot_card_count': len(state['bot_hand']),
        'player_hand': player_hand_annotated,
        'log': state.get('log', []),
        'events': events or [],
        'stats': stats or {},
    }
