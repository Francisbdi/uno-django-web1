/**
 * Lógica Frontend do Jogo UNO 1v1 (Jogador vs Computador)
 * Comunica-se com os endpoints JSON do Django e anima as jogadas em tempo real.
 */

let isAnimating = false;
let soundEnabled = true;
let audioCtx = null;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function playSound(type) {
    if (!soundEnabled) return;
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        const now = audioCtx.currentTime;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);

        if (type === 'card') {
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(340, now);
            osc.frequency.exponentialRampToValueAtTime(580, now + 0.09);
            gain.gain.setValueAtTime(0.16, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
            osc.start(now);
            osc.stop(now + 0.1);
        } else if (type === 'action') {
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(280, now);
            osc.frequency.exponentialRampToValueAtTime(720, now + 0.18);
            gain.gain.setValueAtTime(0.14, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.19);
            osc.start(now);
            osc.stop(now + 0.19);
        } else if (type === 'draw') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(240, now);
            osc.frequency.exponentialRampToValueAtTime(360, now + 0.08);
            gain.gain.setValueAtTime(0.14, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.09);
            osc.start(now);
            osc.stop(now + 0.09);
        } else if (type === 'invalid') {
            osc.type = 'square';
            osc.frequency.setValueAtTime(160, now);
            osc.frequency.setValueAtTime(120, now + 0.07);
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            osc.start(now);
            osc.stop(now + 0.15);
        } else if (type === 'win') {
            const notes = [523.25, 659.25, 783.99, 1046.5];
            notes.forEach((freq, idx) => {
                const o = audioCtx.createOscillator();
                const g = audioCtx.createGain();
                o.type = 'triangle';
                o.connect(g);
                g.connect(audioCtx.destination);
                o.frequency.setValueAtTime(freq, now + idx * 0.1);
                g.gain.setValueAtTime(0.18, now + idx * 0.1);
                g.gain.exponentialRampToValueAtTime(0.008, now + idx * 0.1 + 0.25);
                o.start(now + idx * 0.1);
                o.stop(now + idx * 0.1 + 0.25);
            });
        } else if (type === 'lose') {
            const notes = [392.0, 349.23, 311.13, 261.63];
            notes.forEach((freq, idx) => {
                const o = audioCtx.createOscillator();
                const g = audioCtx.createGain();
                o.type = 'sawtooth';
                o.connect(g);
                g.connect(audioCtx.destination);
                o.frequency.setValueAtTime(freq, now + idx * 0.12);
                g.gain.setValueAtTime(0.12, now + idx * 0.12);
                g.gain.exponentialRampToValueAtTime(0.008, now + idx * 0.12 + 0.26);
                o.start(now + idx * 0.12);
                o.stop(now + idx * 0.12 + 0.26);
            });
        }
    } catch (e) {
        // Ignora caso o navegador bloqueie áudio antes de interação
    }
}

function createCardElement(card, options = {}) {
    const { interactive = false, animatePop = false } = options;
    const el = document.createElement('div');
    el.className = `uno-card color-${card.color}`;
    if (animatePop) {
        el.classList.add('discard-pop');
    }

    if (interactive) {
        if (card.playable) {
            el.classList.add('is-playable');
            el.title = `Jogar ${card.display_name}`;
        } else {
            el.classList.add('not-playable');
            el.title = `${card.display_name} — Não combina com a cor ou símbolo do topo`;
        }
        el.addEventListener('click', () => handleCardClick(card, el));
    }

    const subtitleHtml = card.type === 'action'
        ? `<span class="uno-card-subtitle">${card.action_title}</span>`
        : '';

    el.innerHTML = `
        <span class="uno-card-corner top-left">${card.label}</span>
        <div class="uno-card-oval">
            <span class="uno-card-center">${card.label}</span>
        </div>
        <span class="uno-card-corner bottom-right">${card.label}</span>
        ${subtitleHtml}
    `;
    return el;
}

function renderBotHand(count) {
    const botHandEl = document.getElementById('bot-hand');
    const botCountEl = document.getElementById('bot-card-count');
    const botUnoBadge = document.getElementById('bot-uno-badge');

    botCountEl.textContent = `${count} ${count === 1 ? 'carta' : 'cartas'}`;
    botUnoBadge.style.display = count === 1 ? 'inline-block' : 'none';

    botHandEl.innerHTML = '';
    const maxVisible = Math.min(count, 14);
    for (let i = 0; i < maxVisible; i++) {
        const back = document.createElement('div');
        back.className = 'bot-card-back';
        botHandEl.appendChild(back);
    }
}

function renderTopDiscard(topCard, animate = true) {
    const slot = document.getElementById('discard-pile-slot');
    const activeInfo = document.getElementById('active-card-info');
    const tableArea = document.getElementById('table-area');

    slot.innerHTML = '';
    if (topCard) {
        slot.appendChild(createCardElement(topCard, { interactive: false, animatePop: animate }));
        activeInfo.textContent = `${topCard.display_name}`;
        tableArea.setAttribute('data-active-color', topCard.color);
    }
}

function renderPlayerHand(cards, interactive = true) {
    const container = document.getElementById('player-hand');
    const playerCountEl = document.getElementById('player-card-count');
    const playerUnoBadge = document.getElementById('player-uno-badge');

    playerCountEl.textContent = `${cards.length} ${cards.length === 1 ? 'carta' : 'cartas'}`;
    playerUnoBadge.style.display = cards.length === 1 ? 'inline-block' : 'none';

    container.innerHTML = '';
    cards.forEach((card) => {
        const cardCopy = { ...card };
        if (!interactive) {
            cardCopy.playable = false;
        }
        container.appendChild(createCardElement(cardCopy, { interactive }));
    });
}

function renderStatsAndHistory(stats) {
    if (!stats) return;
    document.getElementById('stat-player-wins').textContent = stats.vitorias_jogador ?? 0;
    document.getElementById('stat-bot-wins').textContent = stats.vitorias_bot ?? 0;
    document.getElementById('stat-total-matches').textContent = stats.total_partidas ?? 0;
    document.getElementById('stat-win-rate').textContent = `${stats.taxa_vitoria ?? 0}%`;

    document.getElementById('top-player-wins').textContent = stats.vitorias_jogador ?? 0;
    document.getElementById('top-bot-wins').textContent = stats.vitorias_bot ?? 0;

    const historyContainer = document.getElementById('history-list');
    historyContainer.innerHTML = '';
    const items = stats.historico || [];

    if (items.length === 0) {
        historyContainer.innerHTML = `
            <div class="history-item" style="justify-content:center; color:#94a3b8;">
                Nenhuma partida finalizada ainda.
            </div>
        `;
        return;
    }

    items.forEach((item) => {
        const isPlayer = item.vencedor === 'JOGADOR';
        const row = document.createElement('div');
        row.className = 'history-item';
        row.innerHTML = `
            <div>
                <div class="history-winner ${isPlayer ? 'win-player' : 'win-bot'}">
                    ${isPlayer ? '🏆 Você venceu' : '🤖 Bot venceu'}
                </div>
                <div class="history-meta">${item.data_hora}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-weight:700; color:#e2e8f0;">${item.turnos} turnos</div>
                <div class="history-meta">Restaram ${item.cartas_restantes_perdedor} cartas</div>
            </div>
        `;
        historyContainer.appendChild(row);
    });
}

function renderLog(logEntries) {
    const logEl = document.getElementById('match-log');
    logEl.innerHTML = '';
    const entries = (logEntries || []).slice().reverse();
    entries.forEach((txt) => {
        const li = document.createElement('li');
        li.textContent = txt;
        logEl.appendChild(li);
    });
}

function renderFullState(data, animateDiscard = false) {
    renderBotHand(data.bot_card_count);
    renderTopDiscard(data.top_card, animateDiscard);
    renderPlayerHand(data.player_hand, !isAnimating && data.status === 'playing' && data.turn === 'player');

    document.getElementById('deck-count').textContent = `${data.deck_count} no monte`;
    document.getElementById('turn-counter').textContent = data.turn_count;
    document.getElementById('status-message').textContent = data.message;

    const turnBadge = document.getElementById('turn-badge');
    if (data.status === 'finished') {
        turnBadge.className = 'turn-badge bot-turn';
        turnBadge.textContent = 'FIM DE JOGO';
    } else if (data.turn === 'player') {
        turnBadge.className = 'turn-badge player-turn';
        turnBadge.textContent = 'SUA VEZ';
    } else {
        turnBadge.className = 'turn-badge bot-turn';
        turnBadge.textContent = 'VEZ DO BOT 🤖';
    }

    // Botão de comprar carta e dica de compra
    const drawBtn = document.getElementById('draw-pile-btn');
    const drawHint = document.getElementById('draw-hint');
    const passBtn = document.getElementById('pass-turn-btn');

    const canDraw = !isAnimating && data.status === 'playing' && data.turn === 'player' && !data.has_drawn_this_turn;
    drawBtn.disabled = !canDraw;

    if (canDraw && !data.has_playable_card) {
        drawBtn.classList.add('suggest-draw');
        drawHint.textContent = 'Sem jogada! Comprar +1';
    } else {
        drawBtn.classList.remove('suggest-draw');
        drawHint.textContent = 'Comprar +1';
    }

    // Botão de passar a vez (visível caso o jogador tenha comprado uma carta jogável e prefira não jogar)
    if (!isAnimating && data.status === 'playing' && data.turn === 'player' && data.has_drawn_this_turn) {
        passBtn.style.display = 'inline-flex';
    } else {
        passBtn.style.display = 'none';
    }

    renderLog(data.log);
    renderStatsAndHistory(data.stats);

    if (data.status === 'finished' && !isAnimating) {
        showEndGameModal(data);
    }
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function playEventsSequence(data) {
    const events = data.events || [];
    if (events.length === 0) {
        renderFullState(data, true);
        return;
    }

    isAnimating = true;
    const turnBadge = document.getElementById('turn-badge');
    const statusMsg = document.getElementById('status-message');

    for (let i = 0; i < events.length; i++) {
        const ev = events[i];

        if (ev.actor === 'bot') {
            turnBadge.className = 'turn-badge bot-turn';
            turnBadge.textContent = 'VEZ DO BOT 🤖';
            statusMsg.textContent = '🤖 O Bot está pensando na jogada...';
            await sleep(550);
        }

        if (ev.action === 'play_action' || ev.action === 'play_draw2') {
            playSound('action');
        } else if (ev.action === 'draw' || ev.action === 'draw_pass' || ev.action === 'draw_playable') {
            playSound('draw');
        } else {
            playSound('card');
        }

        renderBotHand(ev.bot_card_count);
        renderTopDiscard(ev.top_card, true);
        if (ev.player_hand_snapshot) {
            renderPlayerHand(ev.player_hand_snapshot, false);
        }
        document.getElementById('deck-count').textContent = `${ev.deck_count} no monte`;
        document.getElementById('turn-counter').textContent = ev.turn_count;
        statusMsg.textContent = ev.description;

        if (i < events.length - 1) {
            await sleep(650);
        }
    }

    isAnimating = false;
    renderFullState(data, false);
}

async function handleCardClick(card, cardElement) {
    if (isAnimating) return;

    if (!card.playable) {
        playSound('invalid');
        cardElement.classList.remove('shake-card');
        void cardElement.offsetWidth;
        cardElement.classList.add('shake-card');
        document.getElementById('status-message').textContent =
            `⚠️ ${card.display_name} não combina com a cor ou símbolo do topo da mesa!`;
        return;
    }

    try {
        isAnimating = true;
        const response = await fetch('/api/play-card/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ card_id: card.id }),
        });
        const data = await response.json();
        isAnimating = false;

        if (!response.ok || !data.ok) {
            playSound('invalid');
            document.getElementById('status-message').textContent = data.error || 'Jogada inválida.';
            return;
        }

        await playEventsSequence(data);
    } catch (err) {
        isAnimating = false;
        console.error('Erro ao jogar carta:', err);
    }
}

async function handleDrawCard() {
    if (isAnimating) return;
    try {
        isAnimating = true;
        const response = await fetch('/api/draw-card/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        const data = await response.json();
        isAnimating = false;

        if (!response.ok || !data.ok) {
            playSound('invalid');
            document.getElementById('status-message').textContent = data.error || 'Não foi possível comprar carta.';
            return;
        }

        await playEventsSequence(data);
    } catch (err) {
        isAnimating = false;
        console.error('Erro ao comprar carta:', err);
    }
}

async function handlePassTurn() {
    if (isAnimating) return;
    try {
        isAnimating = true;
        const response = await fetch('/api/pass-turn/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        const data = await response.json();
        isAnimating = false;

        if (response.ok && data.ok) {
            await playEventsSequence(data);
        }
    } catch (err) {
        isAnimating = false;
        console.error('Erro ao passar a vez:', err);
    }
}

async function startNewGame() {
    if (isAnimating) return;
    closeEndGameModal();
    try {
        const response = await fetch('/api/new-game/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        const data = await response.json();
        playSound('card');
        renderFullState(data, true);
    } catch (err) {
        console.error('Erro ao iniciar nova partida:', err);
    }
}

async function clearMatchHistory() {
    try {
        const response = await fetch('/api/clear-history/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        const data = await response.json();
        renderStatsAndHistory(data.stats);
    } catch (err) {
        console.error('Erro ao limpar histórico:', err);
    }
}

function showEndGameModal(data) {
    const modal = document.getElementById('endgame-modal');
    const title = document.getElementById('endgame-title');
    const desc = document.getElementById('endgame-desc');

    if (data.winner === 'JOGADOR') {
        playSound('win');
        title.textContent = '🏆 Vitória! Você Venceu!';
        title.style.color = '#34d399';
        desc.textContent = `Parabéns! Você zerou sua mão em ${data.turn_count} turnos deixando o Bot com ${data.bot_card_count} carta(s). Partida salva no histórico!`;
    } else {
        playSound('lose');
        title.textContent = '🤖 O Bot Venceu esta Rodada!';
        title.style.color = '#f87171';
        desc.textContent = `O Bot esvaziou a mão em ${data.turn_count} turnos. Que tal uma revanche agora mesmo?`;
    }

    modal.classList.add('active');
}

function closeEndGameModal() {
    document.getElementById('endgame-modal').classList.remove('active');
}

function toggleRulesModal(show) {
    const modal = document.getElementById('rules-modal');
    if (show) {
        modal.classList.add('active');
    } else {
        modal.classList.remove('active');
    }
}

function toggleSound() {
    soundEnabled = !soundEnabled;
    const btn = document.getElementById('sound-toggle-btn');
    btn.textContent = soundEnabled ? '🔊 Som: ON' : '🔇 Som: OFF';
}

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('new-game-btn').addEventListener('click', startNewGame);
    document.getElementById('draw-pile-btn').addEventListener('click', handleDrawCard);
    document.getElementById('pass-turn-btn').addEventListener('click', handlePassTurn);
    document.getElementById('clear-history-btn').addEventListener('click', clearMatchHistory);
    document.getElementById('rules-btn').addEventListener('click', () => toggleRulesModal(true));
    document.getElementById('close-rules-btn').addEventListener('click', () => toggleRulesModal(false));
    document.getElementById('rematch-btn').addEventListener('click', startNewGame);
    document.getElementById('close-endgame-btn').addEventListener('click', closeEndGameModal);
    document.getElementById('sound-toggle-btn').addEventListener('click', toggleSound);

    try {
        const res = await fetch('/api/state/');
        const data = await res.json();
        renderFullState(data, true);
    } catch (err) {
        console.error('Erro ao carregar estado inicial:', err);
    }
});

