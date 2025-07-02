import random

class Minesweeper:
    HIDDEN = '■'
    FLAG   = '⚑'
    MINE   = 'X'

    def __init__(self, rows=9, cols=9, mines=10):
        self.rows = rows
        self.cols = cols
        self.total_mines = mines

        self.board = None
        self.first_move = True

        self.revealed = [[False]*cols for _ in range(rows)]
        self.flagged = [[False]*cols for _ in range(rows)]
        self.game_over = False

    def _generate_board(self, excluded_r, excluded_c):
        all_positions = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if not (r == excluded_r and c == excluded_c)
        ]
        mines_positions = random.sample(all_positions, self.total_mines)

        # Initialize empty board
        self.board = [[0]*self.cols for _ in range(self.rows)]
        for r, c in mines_positions:
            self.board[r][c] = self.MINE

        # Compute neighbour mine counts
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == self.MINE:
                    continue
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r+dr, c+dc
                        if (
                            0 <= rr < self.rows
                            and 0 <= cc < self.cols
                            and self.board[rr][cc] == self.MINE
                        ):
                            count += 1
                self.board[r][c] = count

    def flood_fill(self, r, c):
        stack = [(r, c)]
        revealed = {(r, c)}
        while stack:
            r, c = stack.pop()
            if self.revealed[r][c]:
                continue
            self.revealed[r][c] = True
            if self.board[r][c] == 0:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r+dr, c+dc
                        if (
                            0 <= rr < self.rows
                            and 0 <= cc < self.cols
                            and not self.revealed[rr][cc]
                        ):
                            revealed.add((rr, cc))
                            stack.append((rr, cc))

        return revealed


    def probe(self, r, c):
        if self.first_move:
            self._generate_board(r, c)
            self.first_move = False

        if self.flagged[r][c] or self.revealed[r][c]:
            return set()

        newly = set()

        if self.board[r][c] == self.MINE:
            self.game_over = True
            for i in range(self.rows):
                for j in range(self.cols):
                    if self.board[i][j] == self.MINE and not self.revealed[i][j]:
                        self.revealed[i][j] = True
                        newly.add((i, j))

        elif self.board[r][c] == 0:
            newly = self.flood_fill(r, c)

        else:
            self.revealed[r][c] = True
            newly.add((r, c))

        return newly

    def get_cell_number(self, r, c):
        if self.revealed[r][c]:
            return self.board[r][c]

        return None

    def toggle_flag(self, r, c):
        if not self.revealed[r][c]:
            self.flagged[r][c] = not self.flagged[r][c]

    def check_win(self):
        if self.board is None:
            return False

        # Win if all non-mine cells are revealed
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != self.MINE and not self.revealed[r][c]:
                    return False
        return True

    def get_board_str(self) -> str:
        flags_placed = sum(
            self.flagged[r][c]
            for r in range(self.rows)
            for c in range(self.cols)
        )
        lines = [f"Mines remaining: {self.total_mines - flags_placed}"]

        header = "    " + "".join(f"{c:>3}" for c in range(self.cols))
        lines.append(header)
        lines.append("    " + "—" * (3 * (self.cols + 1)))

        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                if self.revealed[r][c]:
                    if self.board[r][c] == self.MINE:
                        ch = self.MINE
                    else:
                        ch = str(self.board[r][c])
                else:
                    if self.flagged[r][c]:
                        #ch = f"\033[31m{self.FLAG}\033[0m"
                        ch = self.FLAG
                    else:
                        # Alternating light and grey square patterns
                        if (r + c) % 2 == 0:
                            #ch = f"\033[97m{self.HIDDEN}\033[0m"
                            ch = self.HIDDEN
                        else:
                            #ch = f"\033[37m{self.HIDDEN}\033[0m"
                            ch = self.HIDDEN

                row_cells.append(f"  {ch}")

            lines.append(f"{r:>2} |" + "".join(row_cells))

        return "\n".join(lines)

    def print_board(self):
        print(self.get_board_str())


def parse_input(s, rows, cols):
    """ 'p [row] [col]' for probing or 'f [row] [col]' for flagging."""
    parts = s.strip().split()
    if len(parts) != 3 or parts[0] not in ('p','f'):
        return None
    cmd, r, c = parts[0], parts[1], parts[2]
    if not (r.isdigit() and c.isdigit()):
        return None
    r, c = int(r), int(c)
    if not (0 <= r < rows and 0 <= c < cols):
        return None
    return cmd, r, c

def play():
    print("Select difficulty:")
    print("1) Beginner     (9×9,   10 mines)")
    print("2) Intermediate (16×16, 40 mines)")
    print("3) Expert       (16×30, 99 mines)")
    print("4) Custom")

    choice = input("Enter choice [1-4]: ").strip()
    while True:
        if choice == "1":
            rows, cols, mines = 9, 9, 10
            break
        elif choice == "2":
            rows, cols, mines = 16, 16, 40
            break
        elif choice == "3":
            rows, cols, mines = 16, 30, 99
            break
        elif choice == "4":
            rows = int(input("Rows: ").strip())
            cols = int(input("Cols: ").strip())
            max_mines = rows * cols - 1
            while True:
                mines = int(input(f"Mines (1–{max_mines}): ").strip())
                if 1 <= mines <= max_mines:
                    break
                print(f"Please enter a number between 1 and {max_mines}.")
            break
        else:
            print("Invalid choice :<")

    game = Minesweeper(rows, cols, mines)

    while True:
        game.print_board()              # ← updated

        if game.game_over:
            print("You lost!")
            break
        if game.check_win():
            print("You won!")
            break

        s = input("Enter move (p [row] [col] to probe, f [row] [col] to flag): ")
        parsed = parse_input(s, rows, cols)
        if not parsed:
            print("Invalid input.")
            continue
        cmd, r, c = parsed
        if cmd == 'p':
            game.probe(r, c)
        else:
            game.toggle_flag(r, c)

if __name__ == "__main__":
    play()