"""
Statistical analysis module for beer ratings data.
"""

import sys
import numpy as np

# Import from other modules
sys.path.append('.')
try:
    from clean_data import load_data, clean_ratings
except ImportError:
    # Handle case where clean_data module isn't available
    load_data = None
    clean_ratings = None


def compute_basic_statistics(df):
    """Compute basic descriptive statistics for all ratings."""
    if df is None:
        return None

    # Identify rating columns - look for numeric columns that contain scoring data
    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    if not rating_columns:
        print("No rating columns found in the data.")
        return None

    stats_dict = {}

    for col in rating_columns:
        stats_dict[col] = {
            'mean': df[col].mean(),
            'median': df[col].median(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'count': df[col].count()
        }

    return stats_dict


def compute_beer_averages(df):
    """Compute average ratings for each beer."""
    if df is None:
        return None

    # Identify beer identifier column
    beer_col = None
    for col in df.columns:
        if 'beer' in col.lower() or 'name' in col.lower():
            beer_col = col
            break

    if beer_col is None:
        print("No beer identifier column found.")
        return None

    # Identify rating columns - look for numeric columns that contain scoring data
    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    # Group by beer and calculate averages
    beer_averages = df.groupby(beer_col)[rating_columns].agg(['mean', 'std', 'count'])

    return beer_averages


def find_best_worst_beers(df):
    """Identify the best and worst rated beers."""
    beer_averages = compute_beer_averages(df)

    if beer_averages is None:
        return None

    # Get overall average rating for each beer
    # Extract only the 'mean' columns from the MultiIndex
    mean_columns = [col for col in beer_averages.columns if col[1] == 'mean']
    beer_means = beer_averages[mean_columns]

    # Calculate overall average across all rating categories for each beer
    overall_ratings = beer_means.mean(axis=1)

    best_beer = overall_ratings.idxmax()
    worst_beer = overall_ratings.idxmin()

    results = {
        'best_beer': {
            'name': best_beer,
            'average_rating': overall_ratings[best_beer]
        },
        'worst_beer': {
            'name': worst_beer,
            'average_rating': overall_ratings[worst_beer]
        },
        'all_averages': overall_ratings.sort_values(ascending=False)
    }

    return results


def compute_judge_statistics(df):
    """Compute statistics for each judge's rating patterns."""
    if df is None:
        return None

    # Identify judge identifier column
    judge_col = None
    for col in df.columns:
        if 'judge' in col.lower() or 'reviewer' in col.lower():
            judge_col = col
            break

    if judge_col is None:
        print("No judge identifier column found.")
        return None

    # Identify rating columns - look for numeric columns that contain scoring data
    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    judge_stats = {}

    for judge in df[judge_col].unique():
        judge_data = df[df[judge_col] == judge]
        judge_ratings = judge_data[rating_columns].values.flatten()
        judge_ratings = judge_ratings[~np.isnan(judge_ratings)]  # Remove NaN values

        judge_stats[judge] = {
            'mean_rating': np.mean(judge_ratings),
            'std_rating': np.std(judge_ratings),
            'rating_range': np.max(judge_ratings) - np.min(judge_ratings),
            'num_ratings': len(judge_ratings)
        }

    return judge_stats


def compute_correlations(df):
    """Compute correlations between different rating dimensions."""
    if df is None:
        return None

    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    if len(rating_columns) < 2:
        print("Need at least 2 rating columns to compute correlations.")
        return None

    correlation_matrix = df[rating_columns].corr()

    return correlation_matrix


def main():
    """Main function to demonstrate statistical analysis."""
    if load_data is None or clean_ratings is None:
        print("Error: clean_data module not available")
        return

    data_path = "data/beer_ratings.csv"

    # Load and clean data
    df = load_data(data_path)
    cleaned_df = clean_ratings(df)

    if cleaned_df is None:
        return

    # Compute statistics
    print("=== BASIC STATISTICS ===")
    basic_stats = compute_basic_statistics(cleaned_df)
    for col, stats in basic_stats.items():
        print(f"\n{col}:")
        for stat, value in stats.items():
            print(f"  {stat}: {value:.2f}")

    print("\n=== BEER RANKINGS ===")
    best_worst = find_best_worst_beers(cleaned_df)
    if best_worst:
        print(f"Best beer: {best_worst['best_beer']['name']} (avg: {best_worst['best_beer']['average_rating']:.2f})")
        print(f"Worst beer: {best_worst['worst_beer']['name']} (avg: {best_worst['worst_beer']['average_rating']:.2f})")

    print("\n=== JUDGE STATISTICS ===")
    judge_stats = compute_judge_statistics(cleaned_df)
    if judge_stats:
        for judge, stats in judge_stats.items():
            print(f"{judge}: mean={stats['mean_rating']:.2f}, std={stats['std_rating']:.2f}")

    print("\n=== CORRELATIONS ===")
    correlations = compute_correlations(cleaned_df)
    if correlations is not None:
        print(correlations.round(2))


if __name__ == "__main__":
    main()
