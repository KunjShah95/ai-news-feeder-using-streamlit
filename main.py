import streamlit as st
import pandas as pd
from data import main  # Changed from fetch_data to data
from datetime import datetime
import time


# Use Streamlit's built-in caching
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_data():
    with st.spinner("Fetching latest AI news..."):
        return main()


def run_dashboard():
    st.title("AI News Dashboard")

    # Sidebar with about info and refresh options
    st.sidebar.title("About")
    st.sidebar.info(
        """
    This dashboard aggregates the latest AI news from top sources.
    - Use the filters to customize your feed.
    - Search by keyword, filter by date/source, and download results.
    """
    )
    st.sidebar.markdown("---")
    # --- Safe Auto-refresh Feature ---
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=False)
    refresh_interval = st.sidebar.selectbox(
        "Refresh interval (seconds)", [30, 60, 120, 300], index=1
    )
    if auto_refresh:
        st.write(f"Auto-refreshing every {refresh_interval} seconds...")
        time.sleep(refresh_interval)
        st.experimental_rerun()
    # --- New Feature: Show last refresh time ---
    st.sidebar.write(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Add a refresh button
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Load data with caching
    try:
        df = get_data()
        if df.empty:
            st.error("No news data available. Please try refreshing later.")
            return

        # --- Keyword Search ---
        keyword = st.text_input("Search news by keyword", "")
        if keyword:
            df = df[
                df["Title"].str.contains(keyword, case=False, na=False)
                | df["Description"].str.contains(keyword, case=False, na=False)
            ]

        # --- Summary Statistics ---
        st.subheader("Summary Statistics")
        st.write(f"Total news items: {len(df)}")
        st.write("Articles per Source:")
        st.bar_chart(df["Source"].value_counts())

        # --- Sorting Feature ---
        sort_by = st.selectbox(
            "Sort news by",
            [
                "date (newest)",
                "date (oldest)",
                "title (A-Z)",
                "title (Z-A)",
                "source (A-Z)",
                "source (Z-A)",
            ],
        )
        if sort_by == "date (newest)":
            df = df.sort_values(by="date", ascending=False)
        elif sort_by == "date (oldest)":
            df = df.sort_values(by="date", ascending=True)
        elif sort_by == "title (A-Z)":
            df = df.sort_values(by="Title", ascending=True)
        elif sort_by == "title (Z-A)":
            df = df.sort_values(by="Title", ascending=False)
        elif sort_by == "source (A-Z)":
            df = df.sort_values(by="Source", ascending=True)
        elif sort_by == "source (Z-A)":
            df = df.sort_values(by="Source", ascending=False)

        # --- Existing date/source filter UI ---
        min_date = df["date"].min()
        max_date = df["date"].max()
        col1, col2 = st.columns(2)
        with col1:
            selected_dates = st.date_input(
                "Choose Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if len(selected_dates) == 1:
                start_date = selected_dates[0]
                end_date = selected_dates[0]
            else:
                start_date, end_date = selected_dates
        with col2:
            all_sources = sorted(df["Source"].unique().tolist())
            source_options = ["All"] + all_sources
            selected_sources = st.multiselect(
                "Choose one or more sources", options=source_options
            )

        # --- New Feature: Download as CSV ---
        st.download_button(
            label="Download Filtered News as CSV",
            data=df.to_csv(index=False),
            file_name="ai_news.csv",
            mime="text/csv",
        )

        # --- New Feature: Show/hide descriptions ---
        show_desc = st.checkbox("Show news descriptions", value=True)

        # Show button
        if st.button("Show News", key="show"):
            if not selected_sources:
                st.error("Please select at least one source to display news.")
            else:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                df_filtered = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
                if "All" in selected_sources:
                    pass
                else:
                    df_filtered = df_filtered[
                        df_filtered["Source"].isin(selected_sources)
                    ]
                if len(df_filtered) > 0:
                    st.success(f"Found {len(df_filtered)} news items")
                    for index, row in df_filtered.iterrows():
                        st.markdown(f"### [{row['Title']}]({row['Link']})")
                        st.write(f"**Source**: {row['Source']}")
                        if show_desc:
                            st.write(f"**Description**: {row['Description']}")
                        st.write(f"**Date**: {row['date'].strftime('%Y-%m-%d')}")
                        st.markdown("---")
                else:
                    st.warning(
                        "No news found with the selected filters. Please adjust your date range or source selection."
                    )
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Try refreshing the data using the button above.")


if __name__ == "__main__":
    run_dashboard()
