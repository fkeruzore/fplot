from visualize import plot_rank_evolution, plot_points_evolution


def main():
    """Generate FPL visualizations for current season."""
    plot_rank_evolution("data/2526.csv")
    plot_points_evolution("data/2526.csv")


if __name__ == "__main__":
    main()
