import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use('TkAgg')

def get_stat(path, name = "na", graph_time = False, graph_win_rate = False):
    df = pd.read_csv(path, header = None, names = ["status", "time", "numberofguesses"])

    df["statusflag"] = df["status"].apply(lambda x: 1 if x == "Won" else 0)
    df["time"] = df["time"].astype(float)
    df["numberofguesses"] = df["numberofguesses"].astype(int)

    win_rate = df["statusflag"].mean()
    mean_time = df["time"].mean()
    mean_guesses = df["numberofguesses"].mean()
    max_time = df["time"].max()

    print(f"Win Rate: {win_rate}")
    print(f"Mean Time: {mean_time}")
    print(f"Mean Guesses: {mean_guesses}")
    print(f"Max Time: {max_time}")

    if graph_time:
        df.plot(x = "numberofguesses", y = "time", kind = "scatter")
        plt.yscale("log")
        plt.title(f"Number of Guesses vs Time ({name})")
        plt.xlabel("Number of Guesses")
        plt.ylabel("Time (s)")

        ax = plt.gca()
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.show()

    if graph_win_rate:
        df2 = df.groupby(["numberofguesses"])["statusflag"].mean().reset_index(name = "win_rate")
        df2.plot(x = "numberofguesses", y = "win_rate", kind = "scatter")
        # plt.yscale("log")
        plt.title(f"Number of Guesses vs Win Rate ({name})")
        plt.xlabel("Number of Guesses")
        plt.ylabel("Win Rate")

        ax = plt.gca()
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.show()

def get_multi_graph(path, difficulty, name, decimal_place, start, end, step):
    curr_path = ""
    total_df = pd.DataFrame(columns=["alpha", "win rate"])

    for i in np.arange(start, end, step):
        alpha = round(i, decimal_place)
        curr_path = f"{path}_{alpha}/{difficulty}/summary.csv"

        df = pd.read_csv(curr_path, header=None, names=["status", "time", "numberofguesses"])

        df["statusflag"] = df["status"].apply(lambda x: 1 if x == "Won" else 0)
        win_rate = df["statusflag"].mean()

        new_row = pd.DataFrame([{"alpha": i, "win rate": win_rate}])
        total_df = pd.concat([total_df, new_row], ignore_index=True)

    total_df.plot(x = "alpha", y = "win rate", kind = "scatter")
    plt.title(f"Alpha vs Win Rate ({name})")
    plt.xlabel("Alpha")
    plt.ylabel("Win Rate")

    ax = plt.gca()
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.show()





if __name__ == "__main__":
    # path_dssp_easy = "../dssp/easy/easy.csv"
    # path_dssp_interm = "../dssp/interm/interm.csv"
    # path_dssp_expert = "../dssp/expert/expert.csv"
    # path_random_easy = "../bt_random_guess/easy/easy.csv"
    # path_safest_easy = "../bt_safest_guess/easy/easy.csv"
    # path_safest_interm = "../bt_safest_guess/interm/interm.csv"
    # path_safest_expert = "../bt_parallel/bt_improved_guess_parallel/expert/expert.csv"

    path_GAC_safest_easy = "../games/GAC_mrv_safest/easy/easy.csv"
    path_GAC_safest_interm = "../games/GAC_mrv_safest/interm/interm.csv"
    path_GAC_safest_expert = "../games/GAC_mrv_safest_5000/expert/summary.csv"

    path_GAC_frontier_easy = "../games/GAC_mrv_frontier/easy/easy.csv"
    path_GAC_frontier_interm = "../games/GAC_mrv_frontier/interm/interm.csv"
    path_GAC_frontier_expert = "../games/GAC_mrv_frontier_5000/expert/summary.csv"

    path_GAC_balanced_expert = "../games/GAC_mrv_balanced_5000"

    path_GAC_relative_balanced_expert = "../games/GAC_mrv_relative_balanced_5000"

    # get_stat(path_dssp_easy)
    # get_stat(path_dssp_interm)
    # get_stat(path_dssp_expert)

    #get_stat(path_random_easy, name = "Easy + Random Guess", graph_win_rate= True)
    # get_stat(path_safest_easy, name="Easy + Safest Guess", graph_win_rate=True)
    # get_stat(path_safest_interm, name="Interm + Safest Guess", graph_win_rate=True)

    #get_stat(path_GAC_frontier_expert)

    get_multi_graph(path_GAC_relative_balanced_expert, difficulty = "expert",
                    name = "Relative-Balanced Guess Heuristic",
                    decimal_place = 2, start = 0.0, end = 0.45, step = 0.05)