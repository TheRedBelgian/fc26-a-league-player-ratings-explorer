"""EA Sports FC26 A-League Player Ratings Explorer

Dataset:
EAFC26-Men.csv from Aiden Flynn's EAFC26 Player Database on Kaggle.

This project analyses EA Sports FC 26 game ratings and attributes for players whose league is listed as "A-League".
FC 26 ratings are game values, not real-world match statistics such as actual goals, assists, minutes played, or
live performance data.

Install required packages:
    pip install pandas matplotlib seaborn

Place this Python file in the same folder as EAFC26-Men.csv, then run:
    python fc26_a_league_ratings_explorer.py"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


#=======================================================================================================================
# FILE LOCATIONS
#=======================================================================================================================

# The FC26 men's player data file.
DATA_FILE = Path("EAFC26-Men.csv")

# Folder where CSV output files and PNG charts will be saved.
OUTPUT_FOLDER = Path("outputs")


#=======================================================================================================================
# CLUB COLOURS
#=======================================================================================================================

# Club-colour approximations used for the Average_Rating_By_Club chart
# If a team name is not in this dictionary, the chart uses dark blue.
club_colours = {
    "Adelaide United": "#E31B23",
    "Auckland FC": "#0A1F44",
    "Brisbane Roar": "#F15A24",
    "Central Coast Mariners": "#FFD100",
    "Macarthur FC": "#000000",
    "Melbourne City": "#6CABDD",
    "Melbourne Victory": "#003DA5",
    "Newcastle Jets": "#003DA5",
    "Perth Glory": "#5B1A8D",
    "Sydney FC": "#4DB3E6",
    "Wellington Phoenix": "#F9D616",
    "Western Sydney Wanderers": "#D71920",
    "Western United": "#006B54",
}


#=======================================================================================================================
# DATA LOADING
#=======================================================================================================================

def load_data()-> pd.DataFrame:
   """
   Load the FC26 men's player data from CSV file.

   Returns:
       A Pandas DataFrame containing all players in EAFC26-Men.csv.
   """

   if not DATA_FILE.exists():
       raise FileNotFoundError(
           f"Cannot find data file at {DATA_FILE}."
           f"Put it in the same folder at this script.")

   # low_memory = False prevents mixed-type warnings for larger CSV files.
   return pd.read_csv(DATA_FILE, low_memory = False)


#=======================================================================================================================
# DATA CLEANING AND PREPARATION
#=======================================================================================================================

def prepare_a_league_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter A-League records and prepare the fields needed for analysis.

    Args:
        df: The original FC26 men's player DataFrame.

    Returns:
         A cleaned DataFrame containing A-League player records only.
    """

    # Filter the full dataset to keep only rows where league equals "A-League".
    # .copy() creates a separate DataFrame and avoids Pandas warnings later.
    a_league = (df[
        df["League"].astype(str).str.strip().eq("A-League")
    ].copy())

    # Select only the columns needed for this analysis.
    columns_to_keep = [
        "ID",
        "Rank",
        "Name",
        "Age",
        "Nation",
        "League",
        "Team",
        "Position",
        "OVR",
        "PAC",
        "SHO",
        "PAS",
        "DRI",
        "DEF",
        "PHY",
        "Weak foot",
        "Skill moves",
        "Preferred foot",
        "Alternative positions"
    ]

    a_league = a_league[columns_to_keep].copy()

    # Rename abbreviated FC26 columns into clearer names.
    a_league = a_league.rename(
        columns = {
            "Name": "player",
            "Age": "age",
            "Nation": "nation",
            "League": "league",
            "Team": "team",
            "Position": "position",
            "OVR": "overall_rating",
            "PAC": "pace",
            "SHO": "shooting",
            "PAS": "passing",
            "DRI": "dribbling",
            "DEF": "defending",
            "PHY": "physical",
            "Weak foot": "weak_foot",
            "Skill moves": "skill_moves",
            "Preferred foot": "preferred_foot",
            "Alternative positions": "alternative_positions"
        }
    )

    # Convert rating fields and age into numeric values.
    # errors = "coerce" changes invalid values into NaN rather than crashing.
    numeric_columns = [
        "age",
        "overall_rating",
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physical",
        "weak_foot",
        "skill_moves",
    ]

    for column in numeric_columns:
        a_league[column] = pd.to_numeric(
            a_league[column],
            errors = "coerce",
        )

    # Remove duplicate player/team combinations.
    a_league = a_league.drop_duplicates(subset = ["player", "team"])

    # Remove records without essential information for the analysis.
    a_league = a_league.dropna(
        subset = ["player", "team", "position", "overall_rating"]
    )

    # Create age categories for age-based analysis.
    a_league["age_group"] = pd.cut(
        a_league["age"],
        bins = [0, 21, 25, 29, 100],
        labels = ["21 or under", "22-25", "26-29", "30+"],
        include_lowest = True,
    )

    # Calculate an average attribute score for outfield players only.
    # Goalkeepers are excluded because goalkeeper ratings use different measures.
    outfield = a_league["position"] != "GK"

    attributes = [
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physical",
    ]

    a_league.loc[outfield, "outfield_attribute_average"] = (
        a_league.loc[outfield, attributes]
        .mean(axis = 1)
        .round(1)
    )

    return a_league


#=======================================================================================================================
# CSV OUTPUT TABLES
#=======================================================================================================================

def save_tables(a_league: pd.DataFrame) -> None:
    """
    Save the cleaned data and analysis summary tables as CSV files.

    Args:
        a_league: Cleaned A-League Player DataFrame.
    """

    # Save the cleaned data used for the analysis.
    a_league.to_csv(
        OUTPUT_FOLDER / "FC26_A_League_Players_Cleaned.csv",
        index = False,
    )

    # Sort players by overall rating and use age as a tie-breaker.
    # .head(15) keeps the first 15 rows after sorting.
    top_players = a_league.sort_values(
        ["overall_rating", "age"],
        ascending = [False, True],
    ).head(15)

    top_players.to_csv(
        OUTPUT_FOLDER / "Top_15_A_League_Players.csv",
        index = False,
    )

    # Filter players aged 21 or under, then rank them by FC26 overall rating.
    young_players = a_league[
        a_league["age"] <= 21
    ].sort_values(
        ["overall_rating", "age"],
        ascending = [False, True]
    ).head(15)

    young_players.to_csv(
        OUTPUT_FOLDER / "Top_Players_21_Or_Under.csv",
        index = False,
    )

    # groupby() combines player rows by club to calculate rating summaries.
    club_ratings = (
        a_league.groupby(
            "team",
            as_index = False)
        .agg(
            players = ("player", "count"),
            average_overall_rating = ("overall_rating", "mean"),
            median_overall_rating = ("overall_rating", "median")
        )
        .sort_values("average_overall_rating", ascending = False)
        .round(1)
    )

    club_ratings.to_csv(
        OUTPUT_FOLDER / "A_League_Club_Ratings.csv",
        index = False)

    # Save Perth Glory ratings separately because this project has a Perth focus.
    perth_glory = a_league[
        a_league["team"]
        .astype(str)
        .str.contains("Perth Glory", case = False, na = False)
    ].sort_values(
        "overall_rating",
        ascending = False)

    perth_glory.to_csv(
        OUTPUT_FOLDER / "Perth_Glory_Player_Ratings.csv",
        index = False,
    )


#=======================================================================================================================
# CHARTS
#=======================================================================================================================

def create_charts(a_league: pd.DataFrame) -> None:
    """
    Create and save charts from the cleaned A-League player data.

    Args:
        a_league: Cleaned A-League Player DataFrame.
    """

    sns.set_theme(style = "whitegrid")


    #-------------------------------------------------------------------------------------------------------------------
    # Chart 1: Top 15 players by FC26 overall rating
    #-------------------------------------------------------------------------------------------------------------------
    top_players = a_league.sort_values(
        "overall_rating",
        ascending = False,
    ).head(15)

    plt.figure(figsize = (10, 7))

    sns.barplot(
        data = top_players,
        x = "overall_rating",
        y = "player",
        hue = "position",
        dodge = False,
        palette = "tab10",
    )

    plt.title("Top 15 A-League Players by FC26 Overall Rating")
    plt.xlabel("FC26 Overall Rating")
    plt.ylabel("Player")

    plt.legend(
        title = "Position",
        bbox_to_anchor = (1.02, 1),
        loc = "upper left",
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "Top_15_A_League_Players.png",
        dpi = 200)

    plt.close()

    #-------------------------------------------------------------------------------------------------------------------
    # Chart 2: Average overall rating by A-League club
    #-------------------------------------------------------------------------------------------------------------------
    club_ratings = (
        a_league.groupby("team", as_index = False)["overall_rating"]
        .mean()
        .sort_values("overall_rating", ascending = True)
    )

    # Give each club its own colour.
    # A dark-blue fallback is used if the club is missing from the dictionary.
    bar_colours = [
        club_colours.get(team, "#1F4E79")
        for team in club_ratings["team"]
    ]

    fig, ax = plt.subplots(figsize = (11, 8))

    ax.barh(
        club_ratings["team"],
        club_ratings["overall_rating"],
        color=bar_colours,
    )

    ax.set_title("Average FC 26 Overall Rating by A-League Club")
    ax.set_xlabel("Average FC 26 Overall Rating")
    ax.set_ylabel("Club")

    # Add each club's average rating at the end of its bar.
    for index, rating in enumerate(club_ratings["overall_rating"]):
        ax.text(
            rating + 0.05,
            index,
            f"{rating:.1f}",
            va="center",
            fontsize=9,
        )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "Average_Rating_By_Club.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    #-------------------------------------------------------------------------------------------------------------------
    # Chart 3: Overall rating by age and position
    #-------------------------------------------------------------------------------------------------------------------
    plt.figure(figsize = (10, 7))

    sns.scatterplot(
        data = a_league,
        x = "age",
        y = "overall_rating",
        hue = "position",
        size = "skill_moves",
        sizes = (40, 220),
        alpha = 0.8,
        palette = "tab10",
    )

    plt.title("A-League FC 26 Overall Rating by Age and Position")
    plt.xlabel("Age")
    plt.ylabel("FC 26 Overall Rating")

    plt.legend(
        bbox_to_anchor = (1.02, 1),
        loc = "upper left",
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "FC26_Overall_Rating_By_Age_And_Position.png",
        dpi = 200,
        bbox_inches = "tight",
    )

    plt.close()

    #-------------------------------------------------------------------------------------------------------------------
    # Chart 4: Average attributes by position
    #-------------------------------------------------------------------------------------------------------------------
    outfield = a_league[
        a_league["position"] != "GK"
    ].copy()

    if not outfield.empty:
        attributes = [
            "pace",
            "shooting",
            "passing",
            "dribbling",
            "defending",
            "physical",
        ]

        # groupby() calculates the average score for each attribute by position.
        attributes_by_position = (
            outfield.groupby("position")[attributes]
            .mean()
            .T
        )

        plt.figure(figsize = (11, 7))

        sns.heatmap(
            attributes_by_position,
            annot = True,
            fmt = ".1f",
            cmap = "Blues",
        )

        plt.title("Average FC26 Attributes by A-League Position")
        plt.xlabel("Position")
        plt.ylabel("Attribute")

        plt.tight_layout()

        plt.savefig(
            OUTPUT_FOLDER / "Average_Attributes_By_Position.png",
            dpi = 200,
            bbox_inches = "tight",
        )

        plt.close()

    #-------------------------------------------------------------------------------------------------------------------
    # Chart 5: Perth Glory Player Ratings
    #-------------------------------------------------------------------------------------------------------------------
    perth_glory = a_league[
        a_league["team"]
        .astype(str)
        .str.contains("Perth Glory", case = False, na = False)
    ].sort_values(
        "overall_rating",
        ascending = True,
    )

    if not perth_glory.empty:
        plt.figure(figsize = (9, 6))

        sns.barplot(
            data = perth_glory,
            x = "overall_rating",
            y = "player",
            hue = "position",
            dodge = False,
            palette = "tab10",
            legend = True,
        )

        plt.title("Perth Glory Players: FC26 Overall Ratings")
        plt.xlabel("FC26 Overall Ratings")
        plt.ylabel("Player")

        plt.legend(
            title = "Position",
            bbox_to_anchor = (1.02, 1),
            loc = "upper left",
        )

        plt.tight_layout()

        plt.savefig(
            OUTPUT_FOLDER / "Perth_Glory_Player_Ratings.png",
            dpi = 200,
            bbox_inches = "tight",
        )

        plt.close()


#=======================================================================================================================
# CONSOLE RESULTS
#=======================================================================================================================

def print_key_results(a_league: pd.DataFrame) -> None:
    """
    Print concise results in the terminal to check the analysis.
    """

    print("-" * 60)
    print(f"A-League players analysed: {len(a_league)}")
    print(f"A-League clubs represented: {a_league['team'].nunique()}")
    print("\nTop five players by overall rating:")
    print("-" * 60)

    # head(5) shows only the first five players after the ranking.
    top_five = (
        a_league.sort_values("overall_rating", ascending = False)
        [["player", "team", "position", "age", "overall_rating"]]
        .head(5)
    )
    print(top_five.to_string(index = False))


#=======================================================================================================================
# MAIN PROGRAM
#=======================================================================================================================

def main() -> None:
    """Run the full A-League ratings analysis."""

    # Create the output folder automatically if it does not already exist.
    OUTPUT_FOLDER.mkdir(exist_ok = True)

    raw_data = load_data()

    print("\nFirst five rows of the original dataset:")

    # head() previews the first five rows before filtering or cleaning the dataset.
    print(raw_data.head())

    print("\nOriginal dataset shape (rows, columns):")
    print(raw_data.shape)

    a_league = prepare_a_league_data(raw_data)

    print_key_results(a_league)
    save_tables(a_league)
    create_charts(a_league)

    print("\nAnalysis complete!")
    print(f"Results saved in: {OUTPUT_FOLDER.resolve()}")

if __name__ == "__main__":
    main()