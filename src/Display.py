import pandas as pd
import streamlit as st
import charset_normalizer
from parsers import normalize_columns, find_best_match, score_artist, sort_df
from io import BytesIO


# TODO: Config settings


# TODO: Functions
def file_to_df(uploaded_file, header: int | None = None, encoding: str = "utf-8") -> pd.DataFrame:
    if uploaded_file.name.endswith("csv"):
        return pd.read_csv(uploaded_file, encoding=encoding, header=header, dtype="object")
    elif "xls" in uploaded_file.name:  # did not do endswith due to possibility of getting both xls and xlsx files
        return pd.read_excel(uploaded_file, header=header, dtype="object")


# TODO: Start page
st.header("Song checker site")

playlist_tab, gmr_tab, results_tab = st.tabs(["Playlist uploader", "GMR file uploader", "Results"])

# TODO: Accept files
# TODO: Address files that may or may not have headers
with playlist_tab:
    if playlist := st.file_uploader(
            "Radio station playlist", accept_multiple_files=False, type=('csv', 'xls', 'xlsx')
    ):
        st.divider()
        if playlist.type == 'text/csv':
            enc = charset_normalizer.detect(playlist.read())
            playlist.seek(0)
            encoding = enc["encoding"]
        else:
            encoding = 'utf-8'

        playlist_header = st.checkbox("Does the file have a header row?", key="playlist_check")
        col1, col2 = st.columns(2)

        if playlist_header:
            playlist_df = file_to_df(playlist, header=0, encoding=encoding)
        else:
            playlist_df = file_to_df(playlist, header=None, encoding=encoding)
            playlist_df.columns = [f"col_{i}" for i in playlist_df.columns]

        st.dataframe(playlist_df.head(), hide_index=True, use_container_width=True)

        playlist_song_title = col1.selectbox("Song title column", playlist_df.columns, key="playlist_song_title")
        playlist_artist = col2.selectbox("Artist column", playlist_df.columns, key="playlist_artist")

with gmr_tab:
    # TODO: Implement file upload of GRM file
    if gmr_file := st.file_uploader(
            "GRM info", accept_multiple_files=False
    ):
        st.divider()
        if gmr_file.type == 'text/csv':
            enc = charset_normalizer.detect(gmr_file.read())
            gmr_file.seek(0)
            encoding = enc["encoding"]
        else:
            encoding = 'utf-8'

        gmr_header = st.checkbox("Does the file have a header row?", key="gmr_check")
        col3, col4 = st.columns(2)

        if gmr_header:
            gmr_df = file_to_df(gmr_file, encoding=encoding, header=0)
        else:
            gmr_df = file_to_df(gmr_file, encoding=encoding, header=None)

        st.dataframe(gmr_df.head(), hide_index=True)

        # TODO: Require user to set key columns (artist, song title, etc)
        gmr_song_title = col3.selectbox("Song title column", gmr_df.columns, key="gmr_song_title")
        gmr_artist = col4.selectbox("Artist column", gmr_df.columns, key="gmr_artist")

with results_tab:
    # TODO: Compare files
    parse_files = st.button("Analyze files")
    # TODO: Add 'normalized' song / artist to df
    if parse_files:
        prepped_playlist = normalize_columns(playlist_df, playlist_song_title, playlist_artist)
        prepped_gmr = normalize_columns(gmr_df, gmr_song_title, gmr_artist)

        find_best_match(prepped_playlist, prepped_gmr)

        # st.write(f"Playlist dimenstions {prepped_playlist.shape}")
        # st.dataframe(prepped_playlist, use_container_width=True, hide_index=True)
        # st.write(f"GMR dimenstions {prepped_gmr.shape}")
        # st.dataframe(prepped_gmr, use_container_width=True, hide_index=True)

        merge_df = pd.merge(prepped_playlist, prepped_gmr, left_on="fuzzy_match", right_on="search_song",
                            how="inner").fillna("")

        score_artist(merge_df)

        sort_df(merge_df)

        print(merge_df.columns)

        final_df = merge_df[['col_0', 'Song Title', 'fuzzy_match', 'fuzzy_score', 'Our Title',
                             'Song Artist', 'fuzz_artist_match', 'artist_direct_match', 'Frequently Performed By',
                             'Our Work ID', 'ISWC', 'Our Writers', 'Our Publishers', 'Our Share', 'ISRC']]

        for col_name in ('Song Title', 'fuzzy_match', 'Our Title', 'Song Artist', 'Frequently Performed By'):
            final_df[col_name] = final_df[col_name].str.title()

        st.write(final_df.shape)
        st.dataframe(final_df)

        output = BytesIO()

        final_df.to_excel(output)

        st.download_button("Download", output, file_name="download.xlsx", mime="application/vnd.ms-excel")
