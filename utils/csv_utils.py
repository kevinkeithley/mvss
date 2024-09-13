import os
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd


def combine_tournament_data(
    input_dir: str, output_file: str, file_pattern: Optional[str] = None
) -> None:
    """
    Combine tournament data (player stats or course stats) from multiple CSV files into a single CSV file.

    This function reads all CSV files in the specified input directory (or files
    matching the given pattern), combines them into a single DataFrame, and saves
    the result to a new CSV file. It's designed to work with both player statistics
    and course data, adding a 'tournament_id' column based on the filename.

    Args:
        input_dir (str): Path to the directory containing the input CSV files.
        output_file (str): Path where the combined CSV file will be saved.
        file_pattern (str, optional): If provided, only files matching this pattern will be processed.
                                      For example, "player_stats_*.csv" or "course_stats_*.csv".
                                      Defaults to None (all CSV files in the directory).

    Raises:
        FileNotFoundError: If no CSV files are found in the input directory.

    Example usage:
        combine_tournament_data(
            input_dir="data/player-stats",
            output_file="data/combined_player_stats.csv",
            file_pattern="player_stats_*.csv"
        )

        combine_tournament_data(
            input_dir="data/course-stats",
            output_file="data/combined_course_stats.csv",
            file_pattern="course_stats_*.csv"
        )
    """
    # List all CSV files in the input directory
    if file_pattern:
        csv_files = [
            f
            for f in os.listdir(input_dir)
            if f.endswith(".csv") and f.startswith(file_pattern.replace("*", ""))
        ]
    else:
        csv_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")

    print(f"Found {len(csv_files)} CSV files to process.")

    # Initialize an empty list to store dataframes
    dfs: List[pd.DataFrame] = []

    # Read each CSV file and append to the list
    for file in csv_files:
        file_path = os.path.join(input_dir, file)
        df = pd.read_csv(file_path)

        # Extract tournament ID from filename
        # Assuming filename format is like "player_stats_401353214.csv" or "course_stats_401353214.csv"
        tournament_id = file.split("_")[-1].split(".")[0]

        # Add tournament_id column if it doesn't exist
        if "tournament_id" not in df.columns:
            df["tournament_id"] = tournament_id

        dfs.append(df)
        print(f"Processed {file}")

    # Combine all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)

    # Reorder columns to put tournament_id first if it exists
    if "tournament_id" in combined_df.columns:
        columns = combined_df.columns.tolist()
        columns.insert(0, columns.pop(columns.index("tournament_id")))
        combined_df = combined_df[columns]

    # Save the combined dataframe to a new CSV file
    combined_df.to_csv(output_file, index=False)
    print(f"Combined data saved to {output_file}")

    # Print some statistics about the combined data
    print(f"Total rows in combined data: {len(combined_df)}")
    print(f"Number of unique tournaments: {combined_df['tournament_id'].nunique()}")


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
