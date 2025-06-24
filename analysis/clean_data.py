"""
Data cleaning and preprocessing module for beer ratings analysis.
"""

import pandas as pd


def load_data(filepath):
    """Load beer ratings data from CSV file."""
    try:
        df = pd.read_csv(filepath)
        print(f"Data loaded successfully. Shape: {df.shape}")
        return df
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        return None
    except pd.errors.ParserError as e:
        print(f"Parsing error loading data: {e}")
        return None
    except pd.errors.EmptyDataError as e:
        print(f"Empty data error loading data: {e}")
        return None
    except pd.errors.DtypeWarning as e:
        print(f"Dtype warning loading data: {e}")
        return None


def clean_ratings(df):
    """Clean and validate rating data."""
    if df is None:
        return None

    # Make a copy to avoid modifying original data
    cleaned_df = df.copy()

    # Identify essential columns (ratings and identifiers)
    rating_columns = [col for col in cleaned_df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]

    # Find identifier columns (judge and beer name)
    identifier_columns = []
    for col in cleaned_df.columns:
        if 'judge' in col.lower() or 'reviewer' in col.lower() or 'beer' in col.lower() or 'name' in col.lower():
            identifier_columns.append(col)

    # Only drop rows with missing values in essential columns (ratings + identifiers)
    essential_columns = rating_columns + identifier_columns
    initial_rows = len(cleaned_df)
    cleaned_df = cleaned_df.dropna(subset=essential_columns)
    dropped_rows = initial_rows - len(cleaned_df)

    if dropped_rows > 0:
        print(f"Removed {dropped_rows} rows with missing values in essential columns.")

    # Convert rating columns to numeric if they're not already
    rating_columns = [col for col in cleaned_df.columns if
                     ('rating' in col.lower() or 'score' in col.lower() or
                      '(1-5)' in col or any(word in col.lower() for word in ['aroma', 'flavor', 'sip', 'mouthfeel', 'aftertaste']))]
    for col in rating_columns:
        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')

    return cleaned_df


def validate_data(df):
    """Validate the structure and content of the data."""
    if df is None:
        return False

    print("Data validation:")
    print(f"- Shape: {df.shape}")
    print(f"- Columns: {list(df.columns)}")
    print(f"- Data types:\n{df.dtypes}")
    print(f"- Missing values:\n{df.isnull().sum()}")

    return True


def main():
    """Main function to demonstrate data cleaning."""
    data_path = "data/beer_ratings.csv"

    # Load data
    df = load_data(data_path)

    # Clean data
    cleaned_df = clean_ratings(df)

    # Validate data
    validate_data(cleaned_df)

    return cleaned_df


if __name__ == "__main__":
    main()
