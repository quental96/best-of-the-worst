"""
Visualization module for beer ratings analysis.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Import from other modules
sys.path.append('.')
try:
    from compute_statistics import compute_beer_averages, find_best_worst_beers, compute_judge_statistics
    from clean_data import load_data, clean_ratings
except ImportError:
    # Handle case where modules aren't available
    compute_beer_averages = None
    find_best_worst_beers = None
    compute_judge_statistics = None
    load_data = None
    clean_ratings = None


def setup_plotting_style():
    """Set up consistent plotting style."""
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 12


def plot_average_scores(df, output_dir="figures"):
    """Create bar plot of average scores by beer."""
    if compute_beer_averages is None:
        print("Error: compute_statistics module not available")
        return

    beer_averages = compute_beer_averages(df)
    if beer_averages is None:
        return

    # Calculate overall average for each beer
    # Extract only the 'mean' columns from the MultiIndex
    mean_columns = [col for col in beer_averages.columns if col[1] == 'mean']
    beer_means = beer_averages[mean_columns]

    # Calculate overall average across all rating categories for each beer
    overall_averages = beer_means.mean(axis=1)
    overall_averages = overall_averages.sort_values(ascending=True)

    plt.figure(figsize=(12, 8))
    bars = plt.barh(range(len(overall_averages)), overall_averages.values)

    # Color bars based on rating (green for high, red for low)
    colors = ['green' if rating >= 3 else 'red' for rating in overall_averages]
    for barh, color in zip(bars, colors):
        barh.set_color(color)

    plt.yticks(range(len(overall_averages)), overall_averages.index)
    plt.xlabel('Average Rating')
    plt.title('Average Beer Ratings')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()

    # Save figure
    output_path = Path(output_dir) / "average_scores.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved average scores plot to {output_path}")


def plot_boxplots_by_beer(df, output_dir="figures"):
    """Create box plots showing rating distribution for each beer."""
    # Identify beer and rating columns
    beer_col = None
    for col in df.columns:
        if 'beer' in col.lower() or 'name' in col.lower():
            beer_col = col
            break

    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    if beer_col is None or not rating_columns:
        print("Could not identify beer or rating columns for boxplot.")
        return

    # Melt the data for easier plotting
    melted_data = []
    for _, row in df.iterrows():
        for rating_col in rating_columns:
            melted_data.append({
                'Beer': row[beer_col],
                'Rating': row[rating_col],
                'Category': rating_col
            })

    melted_df = pd.DataFrame(melted_data)

    plt.figure(figsize=(14, 8))
    sns.boxplot(data=melted_df, x='Beer', y='Rating', hue='Category')
    plt.xticks(rotation=45, ha='right')
    plt.title('Rating Distribution by Beer')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    output_path = Path(output_dir) / "boxplots_by_beer.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved boxplots to {output_path}")


def plot_radar_best_worst(df, output_dir="figures"):
    """Create radar chart comparing best and worst beers."""
    if find_best_worst_beers is None or compute_beer_averages is None:
        print("Error: compute_statistics module not available")
        return

    best_worst = find_best_worst_beers(df)
    beer_averages = compute_beer_averages(df)

    if best_worst is None or beer_averages is None:
        return

    # Get data for best and worst beers
    best_beer_name = best_worst['best_beer']['name']
    worst_beer_name = best_worst['worst_beer']['name']

    # Extract average ratings for each category
    # Get only the 'mean' values for each rating category
    mean_columns = [col for col in beer_averages.columns if col[1] == 'mean']
    best_ratings = beer_averages.loc[best_beer_name, mean_columns]
    worst_ratings = beer_averages.loc[worst_beer_name, mean_columns]

    # Extract category names (removing the '(1-5)' part for cleaner display)
    categories = [col[0].replace(' (1-5)', '') for col in mean_columns]

    # Set up radar chart
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    best_values = best_ratings.values.tolist()
    best_values += best_values[:1]

    worst_values = worst_ratings.values.tolist()
    worst_values += worst_values[:1]

    _, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    ax.plot(angles, best_values, 'o-', linewidth=2, label=f'Best: {best_beer_name}', color='green')
    ax.fill(angles, best_values, alpha=0.25, color='green')

    ax.plot(angles, worst_values, 'o-', linewidth=2, label=f'Worst: {worst_beer_name}', color='red')
    ax.fill(angles, worst_values, alpha=0.25, color='red')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title('Best vs Worst Beer Comparison', size=16, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))

    output_path = Path(output_dir) / "radar_best_worst.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved radar chart to {output_path}")


def plot_judge_variability(df, output_dir="figures"):
    """Create plot showing judge rating variability."""
    if compute_judge_statistics is None:
        print("Error: compute_statistics module not available")
        return

    judge_stats = compute_judge_statistics(df)
    if judge_stats is None:
        return

    judges = list(judge_stats.keys())
    means = [judge_stats[judge]['mean_rating'] for judge in judges]
    stds = [judge_stats[judge]['std_rating'] for judge in judges]

    _, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Mean ratings by judge
    _ = ax1.bar(judges, means)
    ax1.set_title('Average Rating by Judge')
    ax1.set_xlabel('Judge')
    ax1.set_ylabel('Average Rating')
    ax1.tick_params(axis='x', rotation=45)

    # Standard deviation by judge
    _ = ax2.bar(judges, stds, color='orange')
    ax2.set_title('Rating Variability by Judge')
    ax2.set_xlabel('Judge')
    ax2.set_ylabel('Standard Deviation')
    ax2.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    output_path = Path(output_dir) / "judge_variability.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved judge variability plot to {output_path}")


def create_all_plots(df, output_dir="figures"):
    """Create all visualization plots."""
    setup_plotting_style()

    print("Creating visualizations...")

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    plot_average_scores(df, output_dir)
    plot_boxplots_by_beer(df, output_dir)
    plot_radar_best_worst(df, output_dir)
    plot_judge_variability(df, output_dir)

    print("All plots created successfully!")


def main():
    """Main function to demonstrate plotting functionality."""
    if load_data is None or clean_ratings is None:
        print("Error: clean_data module not available")
        return

    data_path = "data/beer_ratings.csv"

    # Load and clean data
    df = load_data(data_path)
    cleaned_df = clean_ratings(df)

    if cleaned_df is None:
        return

    # Create all plots
    create_all_plots(cleaned_df)


if __name__ == "__main__":
    main()
