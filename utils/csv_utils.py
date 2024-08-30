from pathlib import Path

import pandas as pd


def load_and_compare_csv(
    file1_path: str, file2_path: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load two CSV files and return their contents as DataFrames, along with their differences.

    Args:
    file1_path (str): Path to the first CSV file.
    file2_path (str): Path to the second CSV file.

    Returns:
    tuple: A tuple containing three DataFrames:
        - The contents of the first CSV file
        - The contents of the second CSV file
        - The differences between the two files
    """
    # Ensure the files exist
    for file_path in [file1_path, file2_path]:
        if not Path(file_path).is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

    # Load the CSV files
    df1 = pd.read_csv(file1_path)
    df2 = pd.read_csv(file2_path)

    # Compare the DataFrames
    differences = pd.concat([df1, df2]).drop_duplicates(keep=False)

    return df1, df2, differences


# Example usage:
# df_old, df_new, diff = load_and_compare_csv('path/to/old_file.csv', 'path/to/new_file.csv')
