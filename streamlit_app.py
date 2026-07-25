import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="U.S. Life Expectancy Explorer", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("2025 County Health Rankings Data - v4 Jen.csv")
    df = df[df["County"].notna()].copy()
    numeric_cols = [
        "Life Expectancy",
        "Median Household Income",
        "% Uninsured Adults",
        "% Food Insecure",
        "% Enrolled in Free or Reduced Lunch",
        "% Physically Inactive",
        "% Adults Reporting Currently Smoking",
        "% Rural",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = load_data()

REGION_COLORS = {
    "Midwest": "#4C78A8",
    "Northeast": "#F58518",
    "South": "#E45756",
    "West": "#8B3FA8",
}
all_regions = sorted(df["Region"].dropna().unique())

region_scale = alt.Scale(
    domain=list(REGION_COLORS.keys()),
    range=list(REGION_COLORS.values()),
)

st.sidebar.title("Dashboard Controls")

selected_region = st.sidebar.radio(
    "Select Region",
    options=["All Regions"] + all_regions,
)

st.sidebar.markdown("---")

determinant_options = {
    "Median Household Income": "Median Household Income",
    "% Uninsured Adults": "% Uninsured Adults",
    "% Food Insecure": "% Food Insecure",
    "% Free or Reduced Lunch": "% Enrolled in Free or Reduced Lunch",
    "% Physically Inactive": "% Physically Inactive",
    "% Smoking": "% Adults Reporting Currently Smoking",
    "% Rural": "% Rural",
}
selected_label = st.sidebar.selectbox("Select Social Determinant", list(determinant_options.keys()))
selected_determinant = determinant_options[selected_label]

if selected_region == "All Regions":
    filtered_df = df.copy()
else:
    filtered_df = df[df["Region"] == selected_region].copy()


def plot_strip_and_scatter(full_df, determinant_col, label, selected_region):
    """Strip plot and scatter composed into one chart, sharing a county-level
    click selection. Clicking a dot in the strip plot highlights the same
    county in the scatter below."""

    strip_data = full_df.dropna(subset=["Life Expectancy", "Region"]).copy()
    scatter_data = full_df.dropna(subset=["Life Expectancy", determinant_col, "Region"]).copy()

    if selected_region != "All Regions":
        scatter_data = scatter_data[scatter_data["Region"] == selected_region]

    strip_data["Selected"] = (
        True if selected_region == "All Regions"
        else (strip_data["Region"] == selected_region)
    )

    county_hover = alt.selection_point(fields=["County", "State"], on="mouseover", empty=False)

    strip = alt.Chart(strip_data).mark_circle(size=25).encode(
        x=alt.X(
            "Life Expectancy:Q",
            title="Life Expectancy (Years)",
            scale=alt.Scale(zero=False),
        ),
        y=alt.Y(
            "Region:N",
            title=None,
            sort=all_regions,
            scale=alt.Scale(paddingOuter=0.3, paddingInner=0.4),
        ),
        color=alt.condition(
            alt.datum.Selected,
            alt.Color("Region:N", scale=region_scale, legend=None),
            alt.value("#d0d0d0"),
        ),
        opacity=alt.condition(county_hover, alt.value(1.0), alt.value(0.4) if selected_region == "All Regions" else alt.value(0.65)),
        size=alt.condition(county_hover, alt.value(180), alt.value(25) if selected_region == "All Regions" else alt.value(45)),
        tooltip=["County:N", "State:N", "Region:N", "Life Expectancy:Q"],
    ).add_params(
        county_hover
    ).properties(
        height=260,
        title=alt.TitleParams(
            text="Life Expectancy Distribution by Region",
            subtitle="Hover over a county dot to highlight it in the scatter plot below",
            subtitleColor="#E45756",
            subtitleFontSize=12,
            subtitleFontStyle="italic",
        ),
    )

    scatter = alt.Chart(scatter_data).mark_circle(size=45).encode(
        x=alt.X(
            f"{determinant_col}:Q",
            title=label,
            scale=alt.Scale(zero=False),
        ),
        y=alt.Y(
            "Life Expectancy:Q",
            title="Life Expectancy (Years)",
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color("Region:N", scale=region_scale, legend=alt.Legend(orient="right")),
        opacity=alt.condition(county_hover, alt.value(1.0), alt.value(0.4)),
        size=alt.condition(county_hover, alt.value(120), alt.value(20)),
        tooltip=["County:N", "State:N", "Region:N", "Life Expectancy:Q", f"{determinant_col}:Q"],
    ).add_params(
        county_hover
    ).properties(
        height=420,
        title=alt.TitleParams(
            text=f"{label} vs. Life Expectancy",
            subtitle="Hover over a county dot to highlight it in the strip plot above",
            subtitleColor="#E45756",
            subtitleFontSize=12,
            subtitleFontStyle="italic",
        ),
    )

    return strip & scatter


def plot_top_bottom(data, ascending, title):
    """Horizontal bar chart of top/bottom 10 counties, with hover highlight."""
    subset = data.dropna(subset=["Life Expectancy"]).sort_values(
        "Life Expectancy", ascending=ascending
    ).head(10)

    hover = alt.selection_point(on="mouseover", nearest=True, empty=False)

    chart = (
        alt.Chart(subset)
        .mark_bar()
        .encode(
            x=alt.X(
                "Life Expectancy:Q",
                title="Life Expectancy (Years)",
                scale=alt.Scale(zero=False),
            ),
            y=alt.Y("County:N", sort="x" if ascending else "-x", title=None),
            color=alt.Color(
                "Region:N",
                scale=region_scale,
                legend=alt.Legend(orient="bottom"),
            ),
            opacity=alt.condition(hover, alt.value(1), alt.value(0.75)),
            tooltip=["County:N", "State:N", "Region:N", "Life Expectancy:Q"],
        )
        .add_params(hover)
        .properties(height=340, title=title)
    )
    return chart


st.image("Project Logo_v3.png", use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
Life expectancy in the United States tells a deeply unequal story. County-level averages vary by more than 20 years, and that gap reflects systematic differences in the social and economic conditions of communities across the country. This dashboard draws on 2025 County Health Rankings data to examine how factors like household income, food access, insurance coverage, and physical activity relate to longevity across the United States.

Select a region and a social determinant from the sidebar to begin exploring the data.
""")
st.divider()

st.altair_chart(
    plot_strip_and_scatter(df, selected_determinant, selected_label, selected_region),
    use_container_width=True,
)

st.divider()

scope = selected_region if selected_region != "All Regions" else "All Regions"
st.subheader(f"County Extremes ({scope})")
col3, col4 = st.columns(2)

with col3:
    st.altair_chart(
        plot_top_bottom(filtered_df, ascending=True, title="Lowest Life Expectancy (Bottom 10)"),
        use_container_width=True,
    )
with col4:
    st.altair_chart(
        plot_top_bottom(filtered_df, ascending=False, title="Highest Life Expectancy (Top 10)"),
        use_container_width=True,
    )
