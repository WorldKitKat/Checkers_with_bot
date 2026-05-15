import tkinter as tk
from tkinter import messagebox
import os
import random
from PIL import Image, ImageTk

class CheckersGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Шашки")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path_icon = os.path.join(current_dir, "static", "favicon.ico")
        if os.path.exists(path_icon):
            try:
                self.root.iconbitmap(path_icon)
            except tk.TclError:
                try:
                    img_ico = tk.PhotoImage(file=path_icon)
                    self.root.iconphoto(True, img_ico)
                except Exception:
                    pass
        
        self.cell_size = 80
        self.canvas = tk.Canvas(root, width=8 * self.cell_size, height=8 * self.cell_size)
        self.canvas.pack()
        
        self.path_white = os.path.join(current_dir, "static", "Сhecker_white.png")
        self.path_black = os.path.join(current_dir, "static", "Checker_black.png")
        
        try:
            target_size = (64, 64)
            pil_white = Image.open(self.path_white).resize(target_size, Image.Resampling.LANCZOS)
            self.img_white = ImageTk.PhotoImage(pil_white)
            
            pil_black = Image.open(self.path_black).resize(target_size, Image.Resampling.LANCZOS)
            self.img_black = ImageTk.PhotoImage(pil_black)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось обработать картинки.\nОшибка: {e}")
            self.root.destroy()
            return
        
        self.board = [
            [' ', 'B', ' ', 'B', ' ', 'B', ' ', 'B'],
            ['B', ' ', 'B', ' ', 'B', ' ', 'B', ' '],
            [' ', 'B', ' ', 'B', ' ', 'B', ' ', 'B'],
            [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
            [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
            ['W', ' ', 'W', ' ', 'W', ' ', 'W', ' '],
            [' ', 'W', ' ', 'W', ' ', 'W', ' ', 'W'],
            ['W', ' ', 'W', ' ', 'W', ' ', 'W', ' ']
        ]
        
        self.turn = 'W'  
        self.selected_piece = None  
        self.possible_moves = {}  
        self.active_capturing_piece = None  
        
        self.canvas.bind("<Button-1>", self.handle_click)
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = "#FFF8DC" if (r + c) % 2 == 0 else "#663300"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                if (r, c) in self.possible_moves:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#77AABB", stipple="gray50")

                if (r, c) == self.selected_piece:
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="#FF0000", width=4)

                piece = self.board[r][c]
                center_x = x1 + self.cell_size // 2
                center_y = y1 + self.cell_size // 2
                
                if 'W' in piece:
                    self.canvas.create_image(center_x, center_y, image=self.img_white)
                elif 'B' in piece:
                    self.canvas.create_image(center_x, center_y, image=self.img_black)
                
                if 'D' in piece:
                    self.canvas.create_text(center_x, center_y, text="👑", font=("Arial", 24), fill="#FFD700")

    def handle_click(self, event):
        if self.turn == 'B':
            return  
            
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        
        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board[row][col]
        
        if self.active_capturing_piece and (row, col) != self.active_capturing_piece:
            if (row, col) in self.possible_moves:
                self.execute_move(row, col)
            return

        if piece.startswith(self.turn):
            all_captures = self.get_all_moves_for_side(self.turn, only_captures=True)
            if all_captures and (row, col) not in all_captures:
                return  
                
            self.selected_piece = (row, col)
            self.possible_moves = self.get_piece_moves(row, col, force_capture=bool(all_captures))
        elif (row, col) in self.possible_moves and self.selected_piece:
            self.execute_move(row, col)
        else:
            if not self.active_capturing_piece:
                self.selected_piece = None
                self.possible_moves = {}
            
        self.draw_board()

    def execute_move(self, row, col):
        s_row, s_col = self.selected_piece
        piece = self.board[s_row][s_col]
        
        self.board[row][col] = piece
        self.board[s_row][s_col] = ' '
        
        captured_pieces = self.possible_moves.get((row, col), [])
        for r, c in captured_pieces:
            self.board[r][c] = ' '
            
        if piece == 'W' and row == 0:
            self.board[row][col] = 'WD'
        elif piece == 'B' and row == 7:
            self.board[row][col] = 'BD'

        if captured_pieces:
            next_captures = self.get_piece_moves(row, col, force_capture=True, only_captures=True)
            if next_captures:
                self.active_capturing_piece = (row, col)
                self.selected_piece = (row, col)
                self.possible_moves = next_captures
                self.draw_board()
                
                if self.turn == 'B':
                    self.root.after(600, self.ai_move)
                return

        self.active_capturing_piece = None
        self.selected_piece = None
        self.possible_moves = {}
        self.turn = 'B' if self.turn == 'W' else 'W'
        
        self.draw_board()
        if not self.check_win_condition():
            if self.turn == 'B':
                self.root.after(600, self.ai_move)

    def get_piece_moves(self, row, col, force_capture=False, only_captures=False):
        moves = {}
        piece = self.board[row][col]
        is_king = 'D' in piece
        side = 'W' if 'W' in piece else 'B'
        enemy_side = 'B' if side == 'W' else 'W'
        
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            if is_king:
                r, c = row + dr, col + dc
                last_enemy = None
                while 0 <= r < 8 and 0 <= c < 8:
                    current = self.board[r][c]
                    if current == ' ':
                        if last_enemy:
                            moves[(r, c)] = [last_enemy]
                        r += dr
                        c += dc
                    elif current.startswith(enemy_side):
                        if last_enemy: 
                            break  
                        last_enemy = (r, c)
                        r += dr
                        c += dc
                    else:
                        break
            else:
                r_enemy, c_enemy = row + dr, col + dc
                r_target, c_target = row + 2*dr, col + 2*dc
                if 0 <= r_target < 8 and 0 <= c_target < 8:
                    if self.board[r_enemy][c_enemy].startswith(enemy_side) and self.board[r_target][c_target] == ' ':
                        moves[(r_target, c_target)] = [(r_enemy, c_enemy)]
                        
        if moves or only_captures:
            return moves
            
        if not force_capture:
            allowed_rows = [-1] if piece == 'W' else [1]
            if is_king:
                allowed_rows = [-1, 1]
                
            for dr, dc in directions:
                if not is_king and dr not in allowed_rows:
                    continue
                    
                r, c = row + dr, col + dc
                if is_king:
                    while 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == ' ':
                        moves[(r, c)] = []
                        r += dr
                        c += dc
                else:
                    if 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == ' ':
                        moves[(r, c)] = []
                        
        return moves

    def get_all_moves_for_side(self, side, only_captures=False):
        all_moves = {}
        has_captures = False
        
        for r in range(8):
            for c in range(8):
                if self.board[r][c].startswith(side):
                    caps = self.get_piece_moves(r, c, force_capture=True, only_captures=True)
                    if caps:
                        has_captures = True
                        all_moves[(r, c)] = caps
                        
        if only_captures:
            return all_moves if has_captures else {}
            
        if not has_captures:
            for r in range(8):
                for c in range(8):
                    if self.board[r][c].startswith(side):
                        mvs = self.get_piece_moves(r, c, force_capture=False)
                        if mvs:
                            all_moves[(r, c)] = mvs
                            
        return all_moves

    def ai_move(self):
        if self.active_capturing_piece:
            from_pos = self.active_capturing_piece
            to_pos = random.choice(list(self.possible_moves.keys()))
            self.execute_move(to_pos[0], to_pos[1])
            return

        all_captures = self.get_all_moves_for_side('B', only_captures=True)
        all_quiet_moves = self.get_all_moves_for_side('B', only_captures=False)
        
        if not all_captures and not all_quiet_moves:
            self.check_win_condition(forced_win='W')
            return

        if all_captures and all_quiet_moves and random.random() < 0.40:
            valid_moves = all_quiet_moves
        else:
            valid_moves = all_captures if all_captures else all_quiet_moves

        if not valid_moves:
            valid_moves = all_captures if all_captures else all_quiet_moves

        from_pos = random.choice(list(valid_moves.keys()))
        to_pos = random.choice(list(valid_moves[from_pos].keys()))
        
        self.selected_piece = from_pos
        self.possible_moves = valid_moves[from_pos]
        
        self.execute_move(to_pos[0], to_pos[1])

    def check_win_condition(self, forced_win=None):
        if forced_win == 'W':
            messagebox.showinfo("Конец игры", "У компьютера не осталось ходов. Белые победили!")
            self.root.quit()
            return True
            
        w_exists = any('W' in cell for row in self.board for cell in row)
        b_exists = any('B' in cell for row in self.board for cell in row)
        
        if not w_exists:
            messagebox.showinfo("Конец игры", "Черные (ИИ) победили!")
            self.root.quit()
            return True
        elif not b_exists:
            messagebox.showinfo("Конец игры", "Поздравляем! Белые победили!")
            self.root.quit()
            return True
            
        if self.turn == 'W' and not self.get_all_moves_for_side('W'):
            messagebox.showinfo("Конец игры", "У вас нет доступных ходов. Черные победили!")
            self.root.quit()
            return True
            
        return False

if __name__ == "__main__":
    root = tk.Tk()
    game = CheckersGame(root)
    root.mainloop()
