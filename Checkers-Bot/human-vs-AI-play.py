"""
Checkers — Human vs AI
Sleek, minimal, professional UI.
"""

import math
import random
import time
from copy import deepcopy

import pygame

# ─────────────────────────────────────────────────────────────
#  LAYOUT  (computed after pygame.init so we know screen size)
# ─────────────────────────────────────────────────────────────
pygame.init()

# Detect native resolution for crisp, non-blurry rendering
_info       = pygame.display.Info()
SCR_W       = _info.current_w
SCR_H       = _info.current_h

ROWS = COLS  = 8
BOARD_PX     = (SCR_H // 8) * 8          # largest multiple-of-8 that fits height
PANEL_W      = max(200, SCR_W - BOARD_PX) # remaining width for panel
WIDTH        = SCR_W
HEIGHT       = SCR_H
SQ           = BOARD_PX // COLS           # cell size in px

# Scale factor vs the original 720-px design
_S           = BOARD_PX / 720.0

RED   = 'R'
WHITE = 'W'

# ─────────────────────────────────────────────────────────────
#  FONTS  — sized to native resolution, never blurry
# ─────────────────────────────────────────────────────────────
def _fnt(base_size, bold=False):
    size = max(10, int(base_size * _S))
    for name in ['Segoe UI', 'Inter', 'Helvetica Neue', 'Arial']:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f: return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

F_HUGE  = _fnt(72, bold=True)
F_BIG   = _fnt(34, bold=True)
F_HEAD  = _fnt(14, bold=True)
F_BODY  = _fnt(16)
F_SMALL = _fnt(13)

# ─────────────────────────────────────────────────────────────
#  PALETTE  — must be defined BEFORE marble textures are baked
# ─────────────────────────────────────────────────────────────
BG          = ( 14,  13,  16)

# Board — marble
DARK_SQ     = ( 42,  42,  48)   # deep charcoal marble
LIGHT_SQ    = (218, 216, 212)   # pale white-grey marble
BORDER_CLR  = ( 18,  17,  20)
BORDER_HI   = ( 80,  78,  88)

# Pieces
R_BASE      = (196,  48,  48)
R_SHINE     = (230,  90,  90)
R_SHADOW    = ( 90,  15,  15)
W_BASE      = (228, 222, 212)
W_SHINE     = (255, 255, 255)
W_SHADOW    = (130, 122, 112)
GOLD        = (220, 175,  40)
GOLD2       = (160, 118,  10)
SEL_RING    = (255, 220,  80)
MOVE_DOT    = (140, 230, 255)

# Panel
PANEL_BG    = ( 16,  14,  18)
DIVIDER     = ( 35,  30,  40)
TAG_RED_BG  = ( 60,  20,  20)
TAG_WHT_BG  = ( 35,  35,  45)
ACCENT_RED  = (210,  60,  60)
ACCENT_WHT  = (200, 195, 188)
TEXT_HI     = (240, 232, 218)
TEXT_MID    = (160, 148, 130)
TEXT_LOW    = ( 90,  82,  72)
GOLD_TXT    = (210, 168,  50)

# Game-over
OVERLAY     = (  8,   6,  10, 210)
BTN_NRM     = ( 38,  30,  50)
BTN_HOV     = ( 70,  55,  90)
BTN_BRD     = (110,  85, 150)

# ─────────────────────────────────────────────────────────────
#  MARBLE TEXTURE (baked once at startup, deterministic)
# ─────────────────────────────────────────────────────────────
def _bake_marble(w, h, base, vein_color, vein_count=6, seed=42):
    """Render a marble tile using sinusoidal veining."""
    surf = pygame.Surface((w, h))
    surf.fill(base)
    rng  = random.Random(seed)
    # pixel-level vein pass (sampled, not every px for speed)
    pixels = pygame.PixelArray(surf)
    for _ in range(vein_count):
        freq   = rng.uniform(0.04, 0.10)
        phase  = rng.uniform(0, math.tau)
        amp    = rng.uniform(6, 18)
        angle  = rng.uniform(0, math.tau)
        ca, sa = math.cos(angle), math.sin(angle)
        alpha  = rng.randint(60, 130)          # vein opacity 0-255
        for px in range(0, w, 2):              # stride-2 for speed
            for py in range(0, h, 2):
                t   = ca*px + sa*py
                val = abs(math.sin(freq*t + phase + amp*math.sin(freq*0.5*t)))
                if val > 0.88:                 # only render bright peaks
                    blend = int(alpha * (val - 0.88) / 0.12)
                    r2 = min(255, base[0] + int((vein_color[0]-base[0]) * blend / 255))
                    g2 = min(255, base[1] + int((vein_color[1]-base[1]) * blend / 255))
                    b2 = min(255, base[2] + int((vein_color[2]-base[2]) * blend / 255))
                    pixels[px][py] = surf.map_rgb(r2, g2, b2)
    del pixels
    return surf

# Dark marble: charcoal base, lighter grey veins
_TEX_DARK  = _bake_marble(SQ, SQ, DARK_SQ,  (90, 90, 105), vein_count=5, seed=11)
# Light marble: off-white base, subtle warm-grey veins
_TEX_LIGHT = _bake_marble(SQ, SQ, LIGHT_SQ, (155, 148, 140), vein_count=6, seed=23)

# ─────────────────────────────────────────────────────────────
#  DRAW HELPERS
# ─────────────────────────────────────────────────────────────
def draw_board_bg(win):
    win.fill(BORDER_CLR)
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c * SQ, r * SQ
            win.blit(_TEX_LIGHT if (r+c) % 2 == 0 else _TEX_DARK, (x, y))
            # thin grid lines for extra clarity
            pygame.draw.rect(win, BORDER_CLR, (x, y, SQ, SQ), 1)
    # outer border
    pygame.draw.rect(win, BORDER_HI, (0, 0, BOARD_PX, HEIGHT), 3)


def draw_valid_dots(win, moves):
    for (r, c) in moves:
        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        # outer glow ring
        pygame.draw.circle(s, (*MOVE_DOT, 40),  (SQ//2, SQ//2), 22)
        # solid dot
        pygame.draw.circle(s, (*MOVE_DOT, 200), (SQ//2, SQ//2), 11)
        # bright centre
        pygame.draw.circle(s, (255,255,255,230), (SQ//2, SQ//2), 4)
        win.blit(s, (c*SQ, r*SQ))


def draw_piece(win, cx, cy, color, king=False, selected=False, pulse=0.0):
    r = SQ // 2 - 12
    main, shine, shadow = (R_BASE, R_SHINE, R_SHADOW) if color == RED else (W_BASE, W_SHINE, W_SHADOW)

    # selection ring (animated pulse)
    if selected:
        ring_r = int(r + 8 + 3 * math.sin(pulse))
        s = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
        alpha = int(160 + 80 * math.sin(pulse))
        pygame.draw.circle(s, (*SEL_RING, alpha), (ring_r+2, ring_r+2), ring_r, 3)
        win.blit(s, (cx - ring_r - 2, cy - ring_r - 2))

    # shadow
    pygame.draw.ellipse(win, (0,0,0,60),
                        pygame.Rect(cx - r + 5, cy + r - 6, r*2 - 6, 10))
    # body
    pygame.draw.circle(win, shadow, (cx+2, cy+2), r)
    pygame.draw.circle(win, main,   (cx,   cy),   r)
    # specular
    pygame.draw.circle(win, shine,  (cx - r//3, cy - r//3), r//3)
    # rim
    pygame.draw.circle(win, shadow, (cx, cy), r, 2)

    if king:
        pygame.draw.circle(win, GOLD,  (cx, cy), r//3 + 2)
        pygame.draw.circle(win, GOLD2, (cx, cy), r//3 + 2, 2)
        # crown points
        for ang in range(0, 360, 72):
            rad_a = math.radians(ang)
            px = int(cx + (r//3 + 8) * math.cos(rad_a))
            py = int(cy + (r//3 + 8) * math.sin(rad_a))
            pygame.draw.circle(win, GOLD, (px, py), 3)


# ─────────────────────────────────────────────────────────────
#  PANEL
# ─────────────────────────────────────────────────────────────
def _pill(win, x, y, w, h, color, radius=8):
    pygame.draw.rect(win, color, (x, y, w, h), border_radius=radius)

def _hline(win, y, margin=20):
    pygame.draw.line(win, DIVIDER, (BOARD_PX + margin, y),
                     (WIDTH - margin, y), 1)

def draw_panel(win, board, turn, ai_thinking, pulse):
    px = BOARD_PX
    pw = PANEL_W

    # bg
    pygame.draw.rect(win, PANEL_BG, (px, 0, pw, HEIGHT))
    pygame.draw.rect(win, DIVIDER,  (px, 0, 2,  HEIGHT))   # left separator

    y = 28

    # ── LOGO / TITLE ─────────────────────────────────────────
    t = F_BIG.render("CHECKERS", True, TEXT_HI)
    win.blit(t, (px + (pw - t.get_width()) // 2, y))
    y += t.get_height() + 6

    sub = F_SMALL.render("Human  vs  AI", True, TEXT_LOW)
    win.blit(sub, (px + (pw - sub.get_width()) // 2, y))
    y += sub.get_height() + 18

    _hline(win, y); y += 14

    # ── TURN PILL ─────────────────────────────────────────────
    if ai_thinking:
        dot_a = int(180 + 75 * math.sin(pulse * 2))
        label, pill_clr, txt_clr = "AI  Thinking…", TAG_WHT_BG, ACCENT_WHT
    elif turn == RED:
        label, pill_clr, txt_clr = "Your Turn", TAG_RED_BG, ACCENT_RED
    else:
        label, pill_clr, txt_clr = "AI's Turn",  TAG_WHT_BG, ACCENT_WHT

    pill_w = pw - 40
    _pill(win, px + 20, y, pill_w, 34, pill_clr)
    lt = F_HEAD.render(label.upper(), True, txt_clr)
    win.blit(lt, (px + 20 + (pill_w - lt.get_width())//2, y + (34 - lt.get_height())//2))
    y += 34 + 18

    _hline(win, y); y += 18

    # ── STAT CARDS ───────────────────────────────────────────
    def stat_card(label, color_tag, bg, pieces, kings, captured, yy):
        # tag row
        _pill(win, px+20, yy, 10, 10, color_tag, radius=3)
        ht = F_HEAD.render(label, True, TEXT_MID)
        win.blit(ht, (px + 36, yy - 1))
        yy += 18

        # stats row
        for name, val in [("Pieces", pieces), ("Kings", kings), ("Taken", captured)]:
            row_bg = PANEL_BG
            nw = pw - 40
            k = F_SMALL.render(name, True, TEXT_LOW)
            v = F_HEAD.render(str(val), True, TEXT_HI)
            win.blit(k, (px + 22, yy))
            win.blit(v, (px + pw - 22 - v.get_width(), yy))
            yy += 20

        return yy + 8

    y = stat_card("YOU · RED",   ACCENT_RED, TAG_RED_BG,
                  board.red_left, board.red_kings, board.red_taken, y)
    _hline(win, y, margin=30); y += 16
    y = stat_card("AI · WHITE",  ACCENT_WHT, TAG_WHT_BG,
                  board.white_left, board.white_kings, board.white_taken, y)

    _hline(win, y); y += 16

    # ── PROGRESS BARS (pieces remaining) ─────────────────────
    bar_label = F_HEAD.render("PIECES REMAINING", True, TEXT_LOW)
    win.blit(bar_label, (px + 20, y))
    y += bar_label.get_height() + 8

    bar_w = pw - 40
    for ratio, color, bg in [
        (board.red_left   / 12, ACCENT_RED, TAG_RED_BG),
        (board.white_left / 12, ACCENT_WHT, TAG_WHT_BG),
    ]:
        _pill(win, px+20, y, bar_w, 10, bg)
        _pill(win, px+20, y, max(4, int(bar_w * ratio)), 10, color)
        y += 18

    _hline(win, y + 6); y += 22

    # ── TIPS ─────────────────────────────────────────────────
    tips = ["Click piece → select",
            "Click dot  → move",
            "Reach far side = King 👑"]
    for tip in tips:
        t = F_SMALL.render(tip, True, TEXT_LOW)
        win.blit(t, (px + 20, y))
        y += 17


# ─────────────────────────────────────────────────────────────
#  GAME-OVER OVERLAY  (drawn once, no double-flip)
# ─────────────────────────────────────────────────────────────
def draw_game_over(win, winner, board):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY)
    win.blit(overlay, (0, 0))

    cx = WIDTH // 2

    if winner == RED:
        headline, col = "YOU WIN", ACCENT_RED
        sub          = "You defeated the AI!"
    else:
        headline, col = "AI WINS", ACCENT_WHT
        sub          = "Better luck next time."

    ht = F_HUGE.render(headline, True, col)
    win.blit(ht, (cx - ht.get_width()//2, HEIGHT//2 - 120))

    st = F_BODY.render(sub, True, TEXT_MID)
    win.blit(st, (cx - st.get_width()//2, HEIGHT//2 - 28))

    score = F_HEAD.render(
        f"RED  {board.red_taken}  taken     WHITE  {board.white_taken}  taken",
        True, GOLD_TXT)
    win.blit(score, (cx - score.get_width()//2, HEIGHT//2 + 12))

    # play-again button
    bw, bh = 200, 50
    bx, by = cx - bw//2, HEIGHT//2 + 62
    btn = pygame.Rect(bx, by, bw, bh)
    hov = btn.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(win, BTN_HOV if hov else BTN_NRM, btn, border_radius=10)
    pygame.draw.rect(win, BTN_BRD, btn, 2, border_radius=10)
    bt = F_HEAD.render("PLAY AGAIN", True, TEXT_HI)
    win.blit(bt, (bx + (bw - bt.get_width())//2, by + (bh - bt.get_height())//2))
    return btn


# ─────────────────────────────────────────────────────────────
#  BOARD / PIECE LOGIC  (unchanged)
# ─────────────────────────────────────────────────────────────
class Piece:
    def __init__(self, row, col, color):
        self.row, self.col, self.color = row, col, color
        self.king = False
        self._pos()
    def _pos(self):
        self.cx = self.col * SQ + SQ//2
        self.cy = self.row * SQ + SQ//2
    def make_king(self): self.king = True
    def move(self, row, col):
        self.row, self.col = row, col
        self._pos()
    def draw(self, win, selected=False, pulse=0.0):
        draw_piece(win, self.cx, self.cy, self.color, self.king, selected, pulse)

class Board:
    def __init__(self):
        self.grid = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.red_taken = self.white_taken = 0
        self._build()

    def _build(self):
        for r in range(ROWS):
            self.grid.append([])
            for c in range(COLS):
                if c % 2 == (r+1) % 2:
                    if r < 3:   self.grid[r].append(Piece(r, c, WHITE))
                    elif r > 4: self.grid[r].append(Piece(r, c, RED))
                    else:       self.grid[r].append(0)
                else:           self.grid[r].append(0)

    def draw(self, win, sel, moves, pulse):
        draw_board_bg(win)
        draw_valid_dots(win, moves)
        for r in range(ROWS):
            for c in range(COLS):
                p = self.grid[r][c]
                if p: p.draw(win, selected=(p is sel), pulse=pulse)

    def move(self, piece, row, col):
        self.grid[piece.row][piece.col], self.grid[row][col] = \
            self.grid[row][col], self.grid[piece.row][piece.col]
        piece.move(row, col)
        if row in (0, ROWS-1) and not piece.king:
            piece.make_king()
            if piece.color == WHITE: self.white_kings += 1
            else:                    self.red_kings   += 1

    def get_piece(self, r, c): return self.grid[r][c]

    def remove(self, pieces):
        for p in pieces:
            self.grid[p.row][p.col] = 0
            if p.color == RED:
                self.red_left  -= 1; self.white_taken += 1
            else:
                self.white_left -= 1; self.red_taken   += 1

    def evaluate(self):
        return self.white_left - self.red_left + \
               (self.white_kings - self.red_kings) * 0.5

    def get_all_pieces(self, color):
        return [p for row in self.grid for p in row if p and p.color == color]

    def winner(self):
        if self.red_left   <= 0: return WHITE
        if self.white_left <= 0: return RED
        if not any(self.get_valid_moves(p) for p in self.get_all_pieces(RED)):   return WHITE
        if not any(self.get_valid_moves(p) for p in self.get_all_pieces(WHITE)): return RED
        return None

    def get_valid_moves(self, piece):
        moves, l, r, row = {}, piece.col-1, piece.col+1, piece.row
        if piece.color == RED   or piece.king:
            moves.update(self._left (row-1, max(row-3,-1),   -1, piece.color, l))
            moves.update(self._right(row-1, max(row-3,-1),   -1, piece.color, r))
        if piece.color == WHITE or piece.king:
            moves.update(self._left (row+1, min(row+3,ROWS),  1, piece.color, l))
            moves.update(self._right(row+1, min(row+3,ROWS),  1, piece.color, r))
        return moves

    def _left(self, start, stop, step, color, left, skipped=[]):
        moves, last = {}, []
        for r in range(start, stop, step):
            if left < 0: break
            cur = self.grid[r][left]
            if cur == 0:
                if skipped and not last: break
                moves[(r,left)] = last + skipped if skipped else last
                if last:
                    nxt = max(r-3,-1) if step==-1 else min(r+3,ROWS)
                    moves.update(self._left (r+step,nxt,step,color,left-1,skipped=last))
                    moves.update(self._right(r+step,nxt,step,color,left+1,skipped=last))
                break
            elif cur.color == color: break
            else: last = [cur]
            left -= 1
        return moves

    def _right(self, start, stop, step, color, right, skipped=[]):
        moves, last = {}, []
        for r in range(start, stop, step):
            if right >= COLS: break
            cur = self.grid[r][right]
            if cur == 0:
                if skipped and not last: break
                moves[(r,right)] = last + skipped if skipped else last
                if last:
                    nxt = max(r-3,-1) if step==-1 else min(r+3,ROWS)
                    moves.update(self._left (r+step,nxt,step,color,right-1,skipped=last))
                    moves.update(self._right(r+step,nxt,step,color,right+1,skipped=last))
                break
            elif cur.color == color: break
            else: last = [cur]
            right += 1
        return moves


# ─────────────────────────────────────────────────────────────
#  AI
# ─────────────────────────────────────────────────────────────
def _sim(piece, move, board, skip):
    board.move(piece, move[0], move[1])
    if skip: board.remove(skip)
    return board

def _all_moves(board, color):
    out = []
    for p in board.get_all_pieces(color):
        for mv, sk in board.get_valid_moves(p).items():
            tb = deepcopy(board)
            tp = tb.get_piece(p.row, p.col)
            out.append(_sim(tp, mv, tb, sk))
    return out

def minimax(pos, depth, maxp, a=float('-inf'), b=float('inf')):
    if depth == 0 or pos.winner() is not None:
        return pos.evaluate(), pos
    if maxp:
        best, val = None, float('-inf')
        for m in _all_moves(pos, WHITE):
            ev = minimax(m, depth-1, False, a, b)[0]
            if ev > val: val, best = ev, m
            a = max(a, ev)
            if b <= a: break
        return val, best
    else:
        best, val = None, float('inf')
        for m in _all_moves(pos, RED):
            ev = minimax(m, depth-1, True, a, b)[0]
            if ev < val: val, best = ev, m
            b = min(b, ev)
            if b <= a: break
        return val, best


# ─────────────────────────────────────────────────────────────
#  GAME
# ─────────────────────────────────────────────────────────────
class Game:
    def __init__(self, win):
        self.win = win
        self.reset()

    def reset(self):
        self.board       = Board()
        self.turn        = RED
        self.selected    = None
        self.valid_moves = {}
        self.game_over   = False
        self.winner_clr  = None
        self.ai_thinking = False

    def select(self, row, col):
        if self.game_over: return
        if self.selected:
            if self._do_move(row, col): return
            self.selected = None
            self.valid_moves = {}
        p = self.board.get_piece(row, col)
        if p and p.color == self.turn:
            self.selected    = p
            self.valid_moves = self.board.get_valid_moves(p)

    def _do_move(self, row, col):
        p = self.board.get_piece(row, col)
        if self.selected and p == 0 and (row, col) in self.valid_moves:
            self.board.move(self.selected, row, col)
            sk = self.valid_moves[(row, col)]
            if sk: self.board.remove(sk)
            self._check_win()
            self.selected    = None
            self.valid_moves = {}
            self.turn        = WHITE if self.turn == RED else RED
            return True
        return False

    def _check_win(self):
        w = self.board.winner()
        if w:
            self.game_over  = True
            self.winner_clr = w

    def do_ai_move(self):
        self.ai_thinking = True
        _, best = minimax(self.board, 3, True)
        self.ai_thinking = False
        if best is None:
            self.game_over  = True
            self.winner_clr = RED
            return
        self.board = best
        self._check_win()
        self.turn = WHITE if self.turn == RED else RED


# ─────────────────────────────────────────────────────────────
#  MAIN LOOP  (single display.flip per frame, no flicker)
# ─────────────────────────────────────────────────────────────
def main():
    win   = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("Checkers — Human vs AI")
    clock = pygame.time.Clock()
    game  = Game(win)

    t0    = time.time()
    run   = True
    btn_rect = None

    while run:
        dt     = clock.tick(60)
        pulse  = (time.time() - t0) * 3.0   # smooth sine driver

        # ── AI turn (runs synchronously; panel shows "Thinking" on next frame) ─
        if not game.game_over and game.turn == WHITE and not game.ai_thinking:
            game.ai_thinking = True
            # render once with "AI Thinking…" then compute
            win.fill(BG)
            game.board.draw(win, game.selected, game.valid_moves, pulse)
            draw_panel(win, game.board, game.turn, True, pulse)
            pygame.display.flip()
            game.do_ai_move()

        # ── Render ────────────────────────────────────────────────────────────
        win.fill(BG)
        game.board.draw(win, game.selected, game.valid_moves, pulse)
        draw_panel(win, game.board, game.turn, game.ai_thinking, pulse)

        if game.game_over:
            btn_rect = draw_game_over(win, game.winner_clr, game.board)
        else:
            btn_rect = None

        pygame.display.flip()   # single flip — no flicker

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if game.game_over:
                    if btn_rect and btn_rect.collidepoint(mx, my):
                        game.reset()
                elif game.turn == RED:
                    col = mx // SQ
                    row = my // SQ
                    if 0 <= row < ROWS and 0 <= col < COLS:
                        game.select(row, col)

    pygame.quit()


if __name__ == "__main__":
    main()