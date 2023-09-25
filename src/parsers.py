import pandas as pd
from rapidfuzz import fuzz, process
from rich import print


def normalize_columns(in_df: pd.DataFrame, song_column: str, artist_column: str, prefix: str) -> pd.DataFrame:
    working_df = in_df.copy()
    working_df.rename(columns={song_column: f"{prefix}_song", artist_column: f"{prefix}_artist"},
                      inplace=True)
    working_df["search_song"] = in_df[song_column].str.strip().str.lower()
    working_df["search_artist"] = in_df[artist_column].str.strip().str.lower()
    # if "col_" in working_df.columns[0]:
    #    working_df.rename(columns={song_column: "Song Title", artist_column: "Song Artist"}, inplace=True)
    return working_df


def find_best_match(playlist_df, gmr_df):
    extractions = playlist_df["search_song"].apply(
        lambda x: process.extractOne(
            x,
            gmr_df["search_song"],
            scorer=fuzz.WRatio,
        )
    )
    playlist_df["fuzzy_match"], playlist_df["fuzzy_score"] = zip(*extractions.apply(_split_song_score))


def _split_song_score(row):
    return ('', '') if row is None else (row[0], row[1])


def score_artist(df):
    df["fuzz_artist_set_ratio"] = df.apply(
        lambda x: fuzz.token_set_ratio(x["search_artist_x"], x["search_artist_y"]), axis=1
    )
    df["artist_direct_match"] = df.apply(
        lambda x: 1 if x["search_artist_x"] in x["search_artist_y"] else 0, axis=1
    )


def sort_df(df):
    df.sort_values(by=["artist_direct_match", "fuzz_artist_set_ratio", "fuzzy_score"], axis=0,
                   inplace=True,
                   ascending=False)
