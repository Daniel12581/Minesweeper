from solve_bt import *

def play_round(algo, row, col, mine):
    game = Minesweeper(row, col, mine)
    return algo(game)

def simulate_easy_games(algo, n, bt_method, bt_heuristic, guessing_heuristic, balance_param,
                        pause = False, print_board = False, save = False, algo_name = ""):
    print("Easy Games")
    easy_c = 0
    for i in range(n):
        print(i)
        game = Minesweeper(9, 9, 10)
        if not save:
            easy_c += algo(game, bt_method, bt_heuristic, guessing_heuristic, print_board=print_board)
        else:
            csv_file = f"../games/{bt_method}_{bt_heuristic}_{guessing_heuristic}/easy/easy.csv"
            txt_file = f"../games/{bt_method}_{bt_heuristic}_{guessing_heuristic}/easy/easy_{i}.txt"
            easy_c += algo(game, bt_method, bt_heuristic, guessing_heuristic, balance_param,
                           print_board=print_board, files=(csv_file, txt_file))

        if pause:
            input()

    return easy_c

def simulate_interm_games(algo, n, bt_method, bt_heuristic, guessing_heuristic, balance_param,
                          pause = False, print_board = False, save = False, algo_name = ""):
    print("Intermediate Games")
    interm_c = 0
    for i in range(n):
        print(i)
        game = Minesweeper(16, 16, 40)
        if not save:
            interm_c += algo(game, bt_method, bt_heuristic, guessing_heuristic, print_board=print_board)
        else:
            csv_file = f"../games/{bt_method}_{bt_heuristic}_{guessing_heuristic}/interm/interm.csv"
            txt_file = f"../games/{bt_method}_{bt_heuristic}_{guessing_heuristic}/interm/interm_{i}.txt"
            interm_c += algo(game, bt_method, bt_heuristic, guessing_heuristic, balance_param,
                             print_board=print_board, files=(csv_file, txt_file))

        if pause:
            input()

    return interm_c

def simulate_expert_games(algo, n, bt_method, bt_heuristic, guessing_heuristic, balance_param,
                          pause = False, print_board = False, save = False, algo_name = ""):
    print("Expert Games")
    expert_c = 0
    for i in range(n):
        print(i)
        game = Minesweeper(16, 30, 99)
        if not save:
            expert_c += algo(game, bt_method, bt_heuristic, guessing_heuristic,print_board=print_board)
        else:
            csv_file = f"../games/{bt_method}_{bt_heuristic}_{guessing_heuristic}/expert/expert.csv"
            txt_file = f"../games/{bt_method}_{bt_heuristic}_{guessing_heuristic}/expert/expert_{i}.txt"
            expert_c += algo(game, bt_method, bt_heuristic, guessing_heuristic, balance_param,
                             print_board=print_board, files=(csv_file, txt_file))

        if pause:
            input()

    return expert_c

def simulate_rounds(algo, n, bt_method, bt_heuristic, guessing_heuristic, balance_param = -1,
                    pause = False, print_board = False, save = False,
                    easy = True, interm = True, expert = True):
    if bt_method not in {"BT", "FC", "GAC"} or bt_heuristic not in {"random", "mrv"} or \
        guessing_heuristic not in {"random", "safest", "frontier", "balanced"}:
        return

    if guessing_heuristic == "balanced" and (balance_param < 0 or balance_param > 1):
        return

    if easy:
        easy_c = simulate_easy_games(algo = algo, n = n, pause = pause, print_board = print_board,
                                     save = save, bt_method = bt_method, bt_heuristic = bt_heuristic,
                                     guessing_heuristic = guessing_heuristic, balance_param = balance_param)

    if interm:
        interm_c = simulate_interm_games(algo = algo, n = n, pause = pause, print_board = print_board,
                                         save = save, bt_method = bt_method, bt_heuristic = bt_heuristic,
                                         guessing_heuristic = guessing_heuristic, balance_param = balance_param)

    if expert:
        expert_c = simulate_expert_games(algo = algo, n = n, pause = pause, print_board = print_board,
                                         save = save, bt_method = bt_method, bt_heuristic = bt_heuristic,
                                         guessing_heuristic = guessing_heuristic, balance_param = balance_param)

    if easy:
        print(f"Easy Difficulty - Win Rate:{easy_c / n}")

    if interm:
        print(f"Intermediate Difficulty - Win Rate:{interm_c / n}")

    if expert:
        print(f"Expert Difficulty - Win Rate:{expert_c / n}")

if __name__ == "__main__":
    # bt_method = "BT", "FC", "GAC"
    # bt_heuristic = "random", "mrv"
    # guessing_heuristic = "random", "safest", "frontier", "custom", "optimal"
    simulate_rounds(solve_bt, 200, pause = False,
                   print_board = False, save = True, bt_method = "GAC",
                    bt_heuristic = "mrv", guessing_heuristic = "safest", easy = False, interm = False,
                    expert = True)