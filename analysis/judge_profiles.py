"""
Judge profiling module for analyzing individual judge characteristics.
"""

import sys
import pandas as pd
import numpy as np

# Import from other modules
sys.path.append('.')
try:
    from compute_statistics import compute_judge_statistics
    from clean_data import load_data, clean_ratings
except ImportError:
    # Handle case where modules aren't available
    compute_judge_statistics = None
    load_data = None
    clean_ratings = None


def analyze_judge_consistency(df):
    """Analyze how consistent each judge is in their ratings."""
    if df is None:
        return None

    # Identify judge and rating columns
    judge_col = None
    for col in df.columns:
        if 'judge' in col.lower() or 'reviewer' in col.lower():
            judge_col = col
            break

    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    if judge_col is None or not rating_columns:
        print("Could not identify judge or rating columns.")
        return None

    judge_consistency = {}

    for judge in df[judge_col].unique():
        judge_data = df[df[judge_col] == judge]

        # Calculate standard deviation across all ratings for this judge
        all_ratings = []
        for _, row in judge_data.iterrows():
            for col in rating_columns:
                if pd.notna(row[col]):
                    all_ratings.append(row[col])

        if len(all_ratings) > 1:
            consistency_score = np.std(all_ratings)
            judge_consistency[judge] = {
                'std_dev': consistency_score,
                'num_ratings': len(all_ratings),
                'avg_rating': np.mean(all_ratings),
                'rating_range': max(all_ratings) - min(all_ratings)
            }

    return judge_consistency


def identify_harsh_lenient_judges(df):
    """Identify which judges tend to be harsh vs lenient."""
    if df is None:
        return None

    if compute_judge_statistics is None:
        print("Error: compute_statistics module not available")
        return None

    judge_stats = compute_judge_statistics(df)
    if judge_stats is None:
        return None

    # Calculate overall average rating across all judges
    all_averages = [stats['mean_rating'] for stats in judge_stats.values()]
    overall_average = np.mean(all_averages)

    harsh_judges = []
    lenient_judges = []

    for judge, stats in judge_stats.items():
        if stats['mean_rating'] < overall_average - 0.5:  # Threshold for harsh
            harsh_judges.append((judge, stats['mean_rating']))
        elif stats['mean_rating'] > overall_average + 0.5:  # Threshold for lenient
            lenient_judges.append((judge, stats['mean_rating']))

    # Sort by severity
    harsh_judges.sort(key=lambda x: x[1])  # Lowest first
    lenient_judges.sort(key=lambda x: x[1], reverse=True)  # Highest first

    return {
        'overall_average': overall_average,
        'harsh_judges': harsh_judges,
        'lenient_judges': lenient_judges
    }


def analyze_judge_preferences(df):
    """Analyze what types of beers each judge prefers."""
    if df is None:
        return None

    # Identify columns
    judge_col = None
    beer_col = None
    for col in df.columns:
        if 'judge' in col.lower() or 'reviewer' in col.lower():
            judge_col = col
        elif 'beer' in col.lower() or 'name' in col.lower():
            beer_col = col

    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    if judge_col is None or beer_col is None or not rating_columns:
        print("Could not identify required columns for preference analysis.")
        return None

    judge_preferences = {}

    for judge in df[judge_col].unique():
        judge_data = df[df[judge_col] == judge]

        # Calculate average rating given by this judge to each beer
        beer_ratings = {}
        for _, row in judge_data.iterrows():
            beer = row[beer_col]
            ratings = [row[col] for col in rating_columns if pd.notna(row[col])]
            if ratings:
                beer_ratings[beer] = np.mean(ratings)

        if beer_ratings:
            # Find top and bottom beers for this judge
            sorted_beers = sorted(beer_ratings.items(), key=lambda x: x[1], reverse=True)

            judge_preferences[judge] = {
                'favorite_beer': sorted_beers[0] if sorted_beers else None,
                'least_favorite_beer': sorted_beers[-1] if sorted_beers else None,
                'all_ratings': dict(sorted_beers)
            }

    return judge_preferences


def find_judge_agreements_disagreements(df):
    """Find pairs of judges who agree/disagree most."""
    if df is None:
        return None

    # Identify columns
    judge_col = None
    beer_col = None
    for col in df.columns:
        if 'judge' in col.lower() or 'reviewer' in col.lower():
            judge_col = col
        elif 'beer' in col.lower() or 'name' in col.lower():
            beer_col = col

    rating_columns = [col for col in df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    if judge_col is None or beer_col is None or not rating_columns:
        return None

    judges = df[judge_col].unique()
    agreements = {}

    # Compare each pair of judges
    for i, judge1 in enumerate(judges):
        for judge2 in judges[i+1:]:
            judge1_data = df[df[judge_col] == judge1]
            judge2_data = df[df[judge_col] == judge2]

            # Find beers both judges rated
            common_beers = set(judge1_data[beer_col]) & set(judge2_data[beer_col])

            if len(common_beers) > 0:
                correlations = []

                for beer in common_beers:
                    judge1_ratings = judge1_data[judge1_data[beer_col] == beer][rating_columns].values.flatten()
                    judge2_ratings = judge2_data[judge2_data[beer_col] == beer][rating_columns].values.flatten()

                    # Remove NaN values
                    judge1_ratings = judge1_ratings[~pd.isna(judge1_ratings)]
                    judge2_ratings = judge2_ratings[~pd.isna(judge2_ratings)]

                    if len(judge1_ratings) > 0 and len(judge2_ratings) > 0:
                        # Calculate correlation for this beer
                        avg1 = np.mean(judge1_ratings)
                        avg2 = np.mean(judge2_ratings)
                        correlations.append((avg1, avg2))

                if len(correlations) > 1:
                    corr_data = np.array(correlations)
                    correlation = np.corrcoef(corr_data[:, 0], corr_data[:, 1])[0, 1]

                    agreements[f"{judge1} vs {judge2}"] = {
                        'correlation': correlation,
                        'common_beers': len(common_beers),
                        'agreement_level': 'High' if correlation > 0.7 else 'Medium' if correlation > 0.3 else 'Low'
                    }

    return agreements


def generate_judge_profiles(df):
    """Generate comprehensive profiles for each judge."""
    if df is None:
        return None

    consistency = analyze_judge_consistency(df)
    harsh_lenient = identify_harsh_lenient_judges(df)
    preferences = analyze_judge_preferences(df)

    profiles = {}

    if consistency:
        for judge, stats in consistency.items():
            profile = {
                'consistency': stats,
                'avg_rating': stats['avg_rating'],
                'rating_style': 'Harsh' if judge in [j[0] for j in harsh_lenient.get('harsh_judges', [])]
                              else 'Lenient' if judge in [j[0] for j in harsh_lenient.get('lenient_judges', [])]
                              else 'Moderate'
            }

            if preferences and judge in preferences:
                profile['preferences'] = preferences[judge]

            profiles[judge] = profile

    return profiles


def main():
    """Main function to demonstrate judge profiling."""
    if load_data is None or clean_ratings is None:
        print("Error: clean_data module not available")
        return

    data_path = "data/beer_ratings.csv"

    # Load and clean data
    df = load_data(data_path)
    cleaned_df = clean_ratings(df)

    if cleaned_df is None:
        return

    print("=== JUDGE CONSISTENCY ANALYSIS ===")
    consistency = analyze_judge_consistency(cleaned_df)
    if consistency:
        for judge, stats in consistency.items():
            print(f"{judge}: std_dev={stats['std_dev']:.2f}, avg={stats['avg_rating']:.2f}")

    print("\n=== HARSH vs LENIENT JUDGES ===")
    harsh_lenient = identify_harsh_lenient_judges(cleaned_df)
    if harsh_lenient:
        print(f"Overall average: {harsh_lenient['overall_average']:.2f}")
        print("Harsh judges:", harsh_lenient['harsh_judges'])
        print("Lenient judges:", harsh_lenient['lenient_judges'])

    print("\n=== JUDGE AGREEMENTS ===")
    agreements = find_judge_agreements_disagreements(cleaned_df)
    if agreements:
        for pair, stats in agreements.items():
            print(f"{pair}: correlation={stats['correlation']:.2f}, agreement={stats['agreement_level']}")

    print("\n=== COMPREHENSIVE JUDGE PROFILES ===")
    profiles = generate_judge_profiles(cleaned_df)
    if profiles:
        for judge, profile in profiles.items():
            print(f"\n{judge}:")
            print(f"  Style: {profile['rating_style']}")
            print(f"  Average Rating: {profile['avg_rating']:.2f}")
            if 'preferences' in profile and profile['preferences']['favorite_beer']:
                fav = profile['preferences']['favorite_beer']
                print(f"  Favorite Beer: {fav[0]} ({fav[1]:.2f})")


if __name__ == "__main__":
    main()
