import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="Data Validation Tool",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Data Validation Tool")
st.write("Upload a CSV or Excel file to check data quality issues before using it in Power BI.")

uploaded_file = st.file_uploader(
    "Upload your file",
    type=["csv", "xlsx"]
)

def load_file(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file, engine="openpyxl")

def create_excel_report(summary_df, missing_df, duplicate_df, dtype_df, negative_df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        missing_df.to_excel(writer, index=False, sheet_name="Missing Values")
        duplicate_df.to_excel(writer, index=False, sheet_name="Duplicate Rows")
        dtype_df.to_excel(writer, index=False, sheet_name="Data Types")
        negative_df.to_excel(writer, index=False, sheet_name="Negative Values")

    output.seek(0)
    return output

if uploaded_file is not None:
    df = load_file(uploaded_file)

    st.subheader("📌 Data Preview")
    st.dataframe(df.head(20), use_container_width=True)

    st.subheader("📊 Basic Summary")

    total_rows = df.shape[0]
    total_columns = df.shape[1]
    duplicate_rows_count = df.duplicated().sum()
    missing_values_count = df.isnull().sum().sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Rows", total_rows)
    col2.metric("Total Columns", total_columns)
    col3.metric("Duplicate Rows", duplicate_rows_count)
    col4.metric("Missing Values", missing_values_count)

    summary_df = pd.DataFrame({
        "Metric": [
            "Total Rows",
            "Total Columns",
            "Duplicate Rows",
            "Total Missing Values"
        ],
        "Value": [
            total_rows,
            total_columns,
            duplicate_rows_count,
            missing_values_count
        ]
    })

    st.divider()

    # Missing value check
    st.subheader("🔍 Missing Value Check")

    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": df.isnull().sum().values,
        "Missing Percentage": (df.isnull().sum().values / len(df) * 100).round(2)
    })

    missing_df = missing_df[missing_df["Missing Count"] > 0]

    if missing_df.empty:
        st.success("No missing values found.")
    else:
        st.warning("Missing values found.")
        st.dataframe(missing_df, use_container_width=True)

    st.divider()

    # Duplicate row check
    st.subheader("📋 Duplicate Row Check")

    duplicate_df = df[df.duplicated()]

    if duplicate_df.empty:
        st.success("No duplicate rows found.")
    else:
        st.warning(f"{len(duplicate_df)} duplicate rows found.")
        st.dataframe(duplicate_df, use_container_width=True)

    st.divider()

    # Duplicate check by selected key column
    st.subheader("🔑 Duplicate Check by Key Column")

    selected_key_column = st.selectbox(
        "Select a key column to check duplicates",
        df.columns
    )

    duplicate_key_df = df[df.duplicated(subset=[selected_key_column], keep=False)]

    if duplicate_key_df.empty:
        st.success(f"No duplicate values found in '{selected_key_column}'.")
    else:
        st.warning(f"Duplicate values found in '{selected_key_column}'.")
        st.dataframe(duplicate_key_df, use_container_width=True)

    st.divider()

    # Data type check
    st.subheader("🧬 Data Type Summary")

    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Unique Values": df.nunique().values,
        "Null Count": df.isnull().sum().values
    })

    st.dataframe(dtype_df, use_container_width=True)

    st.divider()

    # Negative value check
    st.subheader("➖ Negative Value Check")

    numeric_columns = df.select_dtypes(include=["int64", "float64"]).columns

    negative_records = []

    for column in numeric_columns:
        negative_count = (df[column] < 0).sum()
        if negative_count > 0:
            negative_records.append({
                "Column": column,
                "Negative Count": negative_count
            })

    negative_df = pd.DataFrame(negative_records)

    if negative_df.empty:
        st.success("No negative values found in numeric columns.")
        negative_df = pd.DataFrame(columns=["Column", "Negative Count"])
    else:
        st.warning("Negative values found.")
        st.dataframe(negative_df, use_container_width=True)

    st.divider()

    # Date validation
    st.subheader("📅 Date Validation")

    date_column = st.selectbox(
        "Select a column to validate as date",
        ["None"] + list(df.columns)
    )

    if date_column != "None":
        converted_dates = pd.to_datetime(df[date_column], errors="coerce")
        invalid_date_count = converted_dates.isnull().sum() - df[date_column].isnull().sum()

        if invalid_date_count == 0:
            st.success(f"All non-empty values in '{date_column}' are valid dates.")
        else:
            st.warning(f"{invalid_date_count} invalid date values found in '{date_column}'.")

            invalid_dates_df = df[converted_dates.isnull() & df[date_column].notnull()]
            st.dataframe(invalid_dates_df, use_container_width=True)

    st.divider()

    # Validation status
    st.subheader("🚦 Overall Validation Status")

    issues = []

    if missing_values_count > 0:
        issues.append("Missing values found")

    if duplicate_rows_count > 0:
        issues.append("Duplicate rows found")

    if not negative_df.empty:
        issues.append("Negative values found")

    if len(issues) == 0:
        st.success("Data quality looks good. No major issues found.")
    else:
        st.error("Data quality issues found:")
        for issue in issues:
            st.write(f"- {issue}")

    st.divider()

    # Download report
    st.subheader("⬇️ Download Validation Report")

    excel_report = create_excel_report(
        summary_df,
        missing_df,
        duplicate_df,
        dtype_df,
        negative_df
    )

    st.download_button(
        label="Download Validation Report",
        data=excel_report,
        file_name="data_validation_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload a CSV or Excel file to start validation.")
