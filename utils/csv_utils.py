import os
from pathlib import Path
from typing import List, Tuple

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


def identify_csv_files_for_rescrape(
    folder_path: str, unnamed_threshold: float = 0.5
) -> List[Tuple[str, float]]:
    """
    Identify CSV files in a given folder that likely need to be rescraped due to having many unnamed columns.

    This function checks each CSV file in the specified folder and calculates the proportion of unnamed columns.
    Files with a proportion of unnamed columns above the specified threshold are flagged for rescaping.

    Args:
        folder_path (str): Path to the folder containing CSV files to check.
        unnamed_threshold (float, optional): The threshold proportion of unnamed columns above which
                                             a file is flagged for rescraping. Defaults to 0.5 (50%).

    Returns:
        List[Tuple[str, float]]: A list of tuples, each containing:
            - The filename that needs to be rescraped
            - The proportion of unnamed columns in that file

    Raises:
        FileNotFoundError: If the specified folder does not exist.

    Example:
        >>> folder_path = '/path/to/csv/folder'
        >>> files_to_rescrape = identify_csv_files_for_rescrape(folder_path)
        >>> for file, proportion in files_to_rescrape:
        ...     print(f"File: {file}, Proportion of unnamed columns: {proportion:.2f}")
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    files_to_rescrape = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)

            # Count unnamed columns
            unnamed_count = sum(1 for col in df.columns if col.startswith("Unnamed:"))
            total_columns = len(df.columns)
            unnamed_proportion = unnamed_count / total_columns

            if unnamed_proportion >= unnamed_threshold:
                files_to_rescrape.append((filename, unnamed_proportion))

    return files_to_rescrape


# Example usage:
# folder_path = '/path/to/your/csv/folder'
# files_to_rescrape = identify_csv_files_for_rescrape(folder_path)
# for file, proportion in files_to_rescrape:
#     print(f"File: {file}, Proportion of unnamed columns: {proportion:.2f}")
