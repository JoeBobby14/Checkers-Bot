import numpy as np
import pygame
import random
import time
from collections import defaultdict
from copy import deepcopy

# Constants
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Colors
RED = (178, 34, 34)  # Darker red
WHITE = (245, 245, 245)  # Off-white
BLACK = (30, 30, 30)  # Dark gray for board
BLUE = (70, 130, 180)  # Steel blue
GREY = (200, 200, 200)
CROWN = (255, 215, 0)  # Gold
WOOD = (210, 180, 140)  # Wooden board color
HIGHLIGHT = (100, 255, 100, 150)  # Semi-transparent green

# Font
pygame.init()
FONT = pygame.font.SysFont('Arial', 32)
LARGE_FONT = pygame.font.SysFont('Arial', 72)
SMALL_FONT = pygame.font.SysFont('Arial', 24)

class Piece:
    PADDING = 15
    OUTLINE = 2
    HIGHLIGHT_THICKNESS = 4

    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
        self.highlighted = False

    def calc_pos(self):
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2

    def make_king(self):
        self.king = True

    def draw(self, win):
        radius = SQUARE_SIZE // 2 - self.PADDING
        
        # Draw highlight if selected
        if self.highlighted:
            pygame.draw.circle(win, HIGHLIGHT, (self.x, self.y), radius + self.HIGHLIGHT_THICKNESS)
        
        # Draw piece with shadow effect
        pygame.draw.circle(win, (50, 50, 50), (self.x + 2, self.y + 2), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        
        # Add texture to pieces
        for i in range(3):
            pygame.draw.circle(win, 
                             (min(self.color[0]+20, 255), 
                              min(self.color[1]+20, 255), 
                              min(self.color[2]+20, 255)), 
                             (self.x, self.y), 
                             radius - i*3, 1)
        
        if self.king:
            # Draw crown with more detail
            crown_img = pygame.Surface((radius, radius), pygame.SRCALPHA)
            points = [
                (radius//2, 0),
                (radius//3, radius//2),
                (radius//2, radius//3),
                (2*radius//3, radius//2)
            ]
            pygame.draw.polygon(crown_img, CROWN, points)
            pygame.draw.polygon(crown_img, (200, 170, 0), points, 2)
            win.blit(crown_img, (self.x - radius//2, self.y - radius//2))

    def move(self, row, col):
        self.row = row
        self.col = col
        self.calc_pos()

    def __repr__(self):
        return str(self.color)

class Board:
    def __init__(self):
        self.board = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.red_score = 0
        self.white_score = 0
        self.create_board()
        self.wood_texture = self.create_wood_texture()

    def create_wood_texture(self):
        texture = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
        texture.fill(WOOD)
        for i in range(20):
            x, y = random.randint(0, SQUARE_SIZE), random.randint(0, SQUARE_SIZE)
            w, h = random.randint(5, 15), random.randint(1, 3)
            pygame.draw.rect(texture, (WOOD[0]-20, WOOD[1]-20, WOOD[2]-20), (x, y, w, h))
        return texture

    def draw_squares(self, win):
        # Draw wood background
        win.fill(BLACK)
        for row in range(ROWS):
            for col in range(ROWS):
                if col % 2 == ((row + 1) % 2):
                    win.blit(self.wood_texture, (row * SQUARE_SIZE, col * SQUARE_SIZE))
                else:
                    pygame.draw.rect(win, BLACK, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def evaluate(self):
        return (self.white_left - self.red_left + 
                (self.white_kings * 0.7 - self.red_kings * 0.7))

    def get_all_pieces(self, color):
        pieces = []
        for row in self.board:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces

    def move(self, piece, row, col):
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)

        if row == ROWS - 1 or row == 0:
            piece.make_king()
            if piece.color == WHITE:
                self.white_kings += 1
            else:
                self.red_kings += 1

    def get_piece(self, row, col):
        return self.board[row][col]

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row + 1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, WHITE))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, RED))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0
            if piece != 0:
                if piece.color == RED:
                    self.red_left -= 1
                    self.white_score += 1
                else:
                    self.white_left -= 1
                    self.red_score += 1

    def winner(self):
        if self.red_left <= 0:
            return WHITE
        elif self.white_left <= 0:
            return RED
        
        # Check for no valid moves
        red_moves = any(len(self.get_valid_moves(piece)) > 0 for piece in self.get_all_pieces(RED))
        white_moves = any(len(self.get_valid_moves(piece)) > 0 for piece in self.get_all_pieces(WHITE))
        
        if not red_moves:
            return WHITE
        if not white_moves:
            return RED
        
        return None

    def get_valid_moves(self, piece):
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row

        if piece.color == RED or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))

        if piece.color == WHITE or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))

        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break

            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, -1)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1

        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break

            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, -1)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1

        return moves

class Game:
    def __init__(self, win):
        self._init()
        self.win = win
        self.game_over = False
        self.winner = None

    def update(self):
        self.board.draw(self.win)
        self.draw_valid_moves(self.valid_moves)
        self.draw_score()
        pygame.display.update()

    def _init(self):
        self.selected = None
        self.board = Board()
        self.turn = RED
        self.valid_moves = {}
        self.game_over = False
        self.winner = None

    def draw_score(self):
        # Draw scoreboard at the top
        score_bg = pygame.Rect(0, 0, WIDTH, 50)
        pygame.draw.rect(self.win, (50, 50, 50), score_bg)
        
        red_text = FONT.render(f"Red: {self.board.red_score}", True, RED)
        white_text = FONT.render(f"White: {self.board.white_score}", True, WHITE)
        turn_text = FONT.render(f"Turn: {'Red' if self.turn == RED else 'White'}", True, BLUE)
        
        self.win.blit(red_text, (20, 10))
        self.win.blit(white_text, (WIDTH - 150, 10))
        self.win.blit(turn_text, (WIDTH // 2 - 50, 10))

    def winner(self):
        return self.board.winner()

    def reset(self):
        self._init()

    def select(self, row, col):
        if self.game_over:
            return False
            
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        
        piece = self.board.get_piece(row, col)
        if piece != 0 and piece.color == self.turn:
            # Remove highlight from previously selected piece
            if self.selected:
                self.selected.highlighted = False
                
            self.selected = piece
            piece.highlighted = True
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
            
        return False

    def _move(self, row, col):
        piece = self.board.get_piece(row, col)
        if self.selected and piece == 0 and (row, col) in self.valid_moves:
            self.board.move(self.selected, row, col)
            skipped = self.valid_moves[(row, col)]
            if skipped:
                self.board.remove(skipped)
            
            # Check for game over
            winner = self.board.winner()
            if winner:
                self.game_over = True
                self.winner = winner
                self.show_game_over()
                return True
                
            self.change_turn()
        else:
            return False

        return True

    def draw_valid_moves(self, moves):
        for move in moves:
            row, col = move
            # Draw a semi-transparent blue circle for valid moves
            s = pygame.Surface((SQUARE_SIZE//2, SQUARE_SIZE//2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*BLUE, 150), (SQUARE_SIZE//4, SQUARE_SIZE//4), SQUARE_SIZE//4)
            self.win.blit(s, (col * SQUARE_SIZE + SQUARE_SIZE//4, row * SQUARE_SIZE + SQUARE_SIZE//4))

    def change_turn(self):
        if self.selected:
            self.selected.highlighted = False
        self.valid_moves = {}
        self.selected = None
        if self.turn == RED:
            self.turn = WHITE
        else:
            self.turn = RED

    def get_board(self):
        return self.board

    def ai_move(self, board):
        self.board = board
        self.change_turn()
        
        # Check for game over after AI move
        winner = self.board.winner()
        if winner:
            self.game_over = True
            self.winner = winner
            self.show_game_over()

    def show_game_over(self):
        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.win.blit(overlay, (0, 0))
        
        # Game over text
        if self.winner == RED:
            text = LARGE_FONT.render("RED WINS!", True, RED)
        else:
            text = LARGE_FONT.render("WHITE WINS!", True, WHITE)
        
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        self.win.blit(text, text_rect)
        
        # Score text
        score_text = FONT.render(f"Final Score - Red: {self.board.red_score}  White: {self.board.white_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
        self.win.blit(score_text, score_rect)
        
        # Play again button
        button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50)
        pygame.draw.rect(self.win, BLUE, button_rect, border_radius=10)
        pygame.draw.rect(self.win, WHITE, button_rect, 2, border_radius=10)
        
        button_text = FONT.render("Play Again", True, WHITE)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        self.win.blit(button_text, button_text_rect)
        
        pygame.display.update()
        
        # Wait for click on button
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if button_rect.collidepoint(mouse_pos):
                        waiting = False
                        self.reset()
                        return True
        return False

def minimax(position, depth, max_player, game, alpha=float('-inf'), beta=float('inf')):
    if depth == 0 or position.winner() is not None:
        return position.evaluate(), position

    if max_player:
        maxEval = float('-inf')
        best_move = None
        for move in get_all_moves(position, WHITE, game):
            evaluation = minimax(move, depth-1, False, game, alpha, beta)[0]
            maxEval = max(maxEval, evaluation)
            alpha = max(alpha, evaluation)
            if maxEval == evaluation:
                best_move = move
            
            if beta <= alpha:
                break
                
        return maxEval, best_move
    else:
        minEval = float('inf')
        best_move = None
        for move in get_all_moves(position, RED, game):
            evaluation = minimax(move, depth-1, True, game, alpha, beta)[0]
            minEval = min(minEval, evaluation)
            beta = min(beta, evaluation)
            if minEval == evaluation:
                best_move = move
            
            if beta <= alpha:
                break
                
        return minEval, best_move

def simulate_move(piece, move, board, game, skip):
    board.move(piece, move[0], move[1])
    if skip:
        board.remove(skip)
    return board

def get_all_moves(board, color, game):
    moves = []
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skip in valid_moves.items():
            temp_board = deepcopy(board)
            temp_piece = temp_board.get_piece(piece.row, piece.col)
            new_board = simulate_move(temp_piece, move, temp_board, game, skip)
            moves.append(new_board)
    return moves

def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Checkers')
    
    game = Game(win)
    
    clock = pygame.time.Clock()
    run = True
    
    while run:
        clock.tick(60)
        
        if game.turn == WHITE and not game.game_over:
            _, board = minimax(game.get_board(), 3, True, game)
            game.ai_move(board)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = pos[1] // SQUARE_SIZE, pos[0] // SQUARE_SIZE
                
                if game.turn == RED and not game.game_over:
                    game.select(row, col)
        
        game.update()
    
    pygame.quit()

if __name__ == "__main__":
    main()