from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

deployment_root = Path(__file__).resolve().parents[1]
if (deployment_root / "common" / "contracts.py").is_file():
    sys.path.insert(0, str(deployment_root))

from common.contracts import (
    MODEL_FEATURES,
    PRODUCT_TYPES,
    engineer_raw_record,
)

st.set_page_config(page_title="Shelf Signal | SuperKart", page_icon="◉", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 84% 2%, rgba(211, 222, 177, .32), transparent 28rem),
            #f5f2e9;
        color: #20362a;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMainBlockContainer"] {
        max-width: 1220px;
        padding: 2rem 2.2rem 4rem;
    }
    [data-testid="stSidebar"] {
        background: #203d30;
        border-right: 1px solid rgba(255, 255, 255, .12);
    }
    [data-testid="stSidebar"] * { color: #f6f2e6; }
    [data-testid="stSidebar"] input {
        background: #f7f3e9;
        color: #20362a;
        border: 1px solid #b7c5b5;
    }
    [data-testid="stSidebar"] button {
        background: #d9e6a7;
        border: 0;
        border-radius: 999px;
        color: #20362a;
        font-weight: 700;
    }
    .masthead {
        align-items: center;
        border-bottom: 1px solid #d9d8c9;
        display: flex;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        padding: .25rem 0 1.15rem;
    }
    .brand-lockup { align-items: center; display: flex; gap: .8rem; }
    .brand-mark {
        align-items: center;
        background: #d8e5a5;
        border-radius: 14px 14px 14px 4px;
        display: flex;
        height: 42px;
        justify-content: center;
        position: relative;
        transform: rotate(-5deg);
        width: 42px;
    }
    .brand-mark::before {
        border: 2px solid #28533e;
        border-radius: 50%;
        content: "";
        height: 20px;
        position: absolute;
        width: 20px;
    }
    .brand-mark::after {
        background: #e8835b;
        border: 2px solid #f5f2e9;
        border-radius: 50%;
        content: "";
        height: 8px;
        position: absolute;
        right: 7px;
        top: 7px;
        width: 8px;
    }
    .brand-name strong {
        color: #203d30;
        display: block;
        font-size: .95rem;
        letter-spacing: .13em;
    }
    .brand-name small, .issue-pill, .eyebrow, .sidebar-kicker {
        color: #667568;
        font-size: .66rem;
        font-weight: 750;
        letter-spacing: .15em;
    }
    .issue-pill {
        border: 1px solid #c9ceba;
        border-radius: 999px;
        padding: .5rem .8rem;
    }
    .hero {
        align-items: center;
        background: #fffdf6;
        border: 1px solid #e4e1d2;
        border-radius: 24px;
        box-shadow: 0 14px 36px rgba(39, 57, 41, .06);
        display: grid;
        gap: 2rem;
        grid-template-columns: minmax(0, 1.6fr) minmax(190px, .7fr);
        margin-bottom: 2rem;
        overflow: hidden;
        padding: clamp(1.5rem, 4vw, 3rem);
        position: relative;
    }
    .hero::after {
        border: 1px solid rgba(40, 83, 62, .12);
        border-radius: 50%;
        content: "";
        height: 360px;
        position: absolute;
        right: -110px;
        top: -205px;
        width: 360px;
    }
    .eyebrow { color: #bd684a; margin: 0 0 .6rem; }
    .hero h1 {
        color: #203d30;
        font-size: clamp(2.25rem, 5.2vw, 4.15rem);
        letter-spacing: -.055em;
        line-height: .98;
        margin: 0;
        max-width: 720px;
    }
    .hero h1 em { color: #bd684a; font-style: normal; }
    .hero-copy {
        color: #647066;
        font-size: 1rem;
        line-height: 1.65;
        margin: 1rem 0 0;
        max-width: 590px;
    }
    .signal-card {
        background: #eaf0d8;
        border-radius: 20px;
        justify-self: stretch;
        padding: 1.2rem;
        position: relative;
        z-index: 1;
    }
    .signal-label { color: #62715e; font-size: .69rem; font-weight: 750; letter-spacing: .14em; }
    .signal-card strong {
        color: #203d30;
        display: block;
        font-size: 1.22rem;
        margin: .35rem 0 .15rem;
    }
    .signal-card span { color: #667568; font-size: .82rem; }
    .signal-bars {
        align-items: end;
        display: flex;
        gap: 7px;
        height: 70px;
        margin: .6rem 0 .8rem;
    }
    .signal-bars i {
        background: #5c8763;
        border-radius: 6px 6px 2px 2px;
        display: block;
        flex: 1;
    }
    .signal-bars i:nth-child(1) { height: 35%; }
    .signal-bars i:nth-child(2) { height: 58%; }
    .signal-bars i:nth-child(3) { height: 45%; }
    .signal-bars i:nth-child(4) { height: 78%; }
    .signal-bars i:nth-child(5) { background: #df9168; height: 100%; }
    .section-heading {
        align-items: end;
        display: flex;
        gap: .8rem;
        margin: 0 0 .85rem;
    }
    .section-number {
        align-items: center;
        background: #e5ebd2;
        border-radius: 10px;
        color: #345b40;
        display: inline-flex;
        font-size: .75rem;
        font-weight: 800;
        height: 34px;
        justify-content: center;
        width: 38px;
    }
    .section-title { color: #203d30; font-size: 1.12rem; font-weight: 750; }
    .section-note { color: #788176; font-size: .83rem; margin-left: auto; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: #e9e9dc;
        border: 1px solid #dcddce;
        border-radius: 14px;
        gap: .45rem;
        padding: .35rem;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: #58675c;
        height: 2.8rem;
        padding: 0 1rem;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: #fffdf6;
        box-shadow: 0 2px 8px rgba(39, 57, 41, .08);
        color: #203d30;
    }
    [data-testid="stTabs"] [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 253, 246, .84);
        border-color: #e2dfd0;
        border-radius: 18px;
    }
    h2, h3 { color: #203d30; }
    [data-testid="stCaptionContainer"] { color: #748075; }
    button[kind="primary"] {
        background: #285a42;
        border: 0;
        border-radius: 12px;
        color: #fffdf6;
        font-weight: 750;
        min-height: 2.8rem;
    }
    button[kind="primary"]:hover { background: #1e4934; border: 0; color: white; }
    [data-testid="stMetric"] {
        background: #edf2de;
        border: 1px solid #dbe5c5;
        border-radius: 14px;
        padding: 1rem;
    }
    [data-testid="stMetricLabel"] { color: #687667; }
    [data-testid="stMetricValue"] { color: #244b37; }
    [data-testid="stFileUploader"] {
        background: #f4f5e9;
        border: 1px dashed #aab99d;
        border-radius: 14px;
        padding: .65rem;
    }
    .footer-note {
        border-top: 1px solid #d9d8c9;
        color: #778176;
        font-size: .78rem;
        line-height: 1.6;
        margin-top: 2.2rem;
        padding-top: 1rem;
    }
    @media (max-width: 760px) {
        [data-testid="stMainBlockContainer"] { padding: 1rem 1rem 2.5rem; }
        .hero { grid-template-columns: 1fr; gap: 1.2rem; padding: 1.4rem; }
        .signal-card { max-width: 280px; }
        .issue-pill { display: none; }
        .section-note { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="masthead">
      <div class="brand-lockup">
        <div class="brand-mark"></div>
        <div class="brand-name">
          <strong>SUPERKART</strong>
          <small>FIELD NOTES / SALES STUDIO</small>
        </div>
      </div>
      <div class="issue-pill">PRODUCT x STORE / ESTIMATOR</div>
    </div>
    <section class="hero">
      <div>
        <p class="eyebrow">A CLEARER READ ON THE SHELF</p>
        <h1>Put the next sale<br><em>in sharper focus.</em></h1>
        <p class="hero-copy">
          Explore an estimated sales total for a product in a store.
          Use each result as a planning signal, not a guarantee.
        </p>
      </div>
      <div class="signal-card">
        <div class="signal-label">THE MODEL OUTPUT</div>
        <div class="signal-bars"><i></i><i></i><i></i><i></i><i></i></div>
        <strong>One product. One store.</strong>
        <span>A focused estimate from the selected details.</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

default_api = os.environ.get("API_BASE_URL", "http://127.0.0.1:7860").rstrip("/")
with st.sidebar:
    st.markdown('<p class="sidebar-kicker">CONNECTION / 01</p>', unsafe_allow_html=True)
    st.subheader("Model endpoint")
    api_url = st.text_input("Prediction API URL", default_api).strip().rstrip("/")
    if not api_url:
        st.error("Enter a prediction API URL.")

    if st.button("Test connection", type="primary", disabled=not bool(api_url)):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            response.raise_for_status()
            st.success("Model API is ready.")
        except requests.RequestException as exc:
            st.error(f"Connection check failed: {exc}")

    st.markdown("---")
    st.caption(
        "This endpoint is used by Streamlit, not the browser. The public UI calls "
        "the API over the private Docker network."
    )

st.markdown(
    """
    <div class="section-heading">
      <span class="section-number">01</span>
      <span class="section-title">Choose a workflow</span>
      <span class="section-note">single estimate or a whole file</span>
    </div>
    """,
    unsafe_allow_html=True,
)

single_tab, batch_tab = st.tabs(["Single product", "Batch CSV"])


def response_error(response: requests.Response) -> str:
    try:
        body = response.json()
    except requests.exceptions.JSONDecodeError:
        return response.text or f"HTTP {response.status_code}"
    if isinstance(body, dict) and isinstance(body.get("error"), str):
        return body["error"]
    return response.text or f"HTTP {response.status_code}"


with single_tab:
    with st.container(border=True):
        st.subheader("Build a product-store profile")
        st.caption("Enter the item and outlet details to request one estimate.")
        with st.form("single_prediction"):
            left, right = st.columns(2)
            with left:
                product_id = st.text_input("Product_Id", "FD6114").strip().upper()
                product_type = st.selectbox(
                    "Product_Type",
                    PRODUCT_TYPES,
                    index=PRODUCT_TYPES.index("Frozen Foods"),
                )
                product_weight = st.number_input(
                    "Product_Weight", min_value=0.01, value=12.66, step=0.1
                )
                sugar_content = st.selectbox(
                    "Product_Sugar_Content", ["Low Sugar", "Regular", "No Sugar"]
                )
                allocated_area = st.number_input(
                    "Product_Allocated_Area",
                    min_value=0.001,
                    max_value=1.0,
                    value=0.027,
                    step=0.001,
                    format="%.3f",
                )
                product_mrp = st.number_input(
                    "Product_MRP", min_value=0.01, value=117.08, step=0.1
                )
            with right:
                store_size = st.selectbox(
                    "Store_Size", ["High", "Medium", "Small"], index=1
                )
                city_type = st.selectbox(
                    "Store_Location_City_Type",
                    ["Tier 1", "Tier 2", "Tier 3"],
                    index=1,
                )
                store_type = st.selectbox(
                    "Store_Type",
                    [
                        "Departmental Store",
                        "Food Mart",
                        "Supermarket Type1",
                        "Supermarket Type2",
                    ],
                    index=3,
                )
                establishment_year = st.number_input(
                    "Store_Establishment_Year",
                    min_value=1987,
                    max_value=2025,
                    value=2009,
                    step=1,
                )
            submitted = st.form_submit_button(
                "Estimate product-store sales", type="primary", use_container_width=True
            )

    if submitted:
        # Keep raw form values on the shared training/inference feature contract.
        raw_record = {
            "Product_Id": product_id,
            "Product_Weight": product_weight,
            "Product_Sugar_Content": sugar_content,
            "Product_Allocated_Area": allocated_area,
            "Product_Type": product_type,
            "Product_MRP": product_mrp,
            "Store_Establishment_Year": establishment_year,
            "Store_Size": store_size,
            "Store_Location_City_Type": city_type,
            "Store_Type": store_type,
        }
        try:
            payload = engineer_raw_record(raw_record)
            response = requests.post(
                f"{api_url}/v1/predict", json=payload, timeout=15
            )
            if response.ok:
                result = response.json()
                with st.container(border=True):
                    st.markdown(
                        '<p class="eyebrow">ESTIMATE / PRODUCT x STORE</p>',
                        unsafe_allow_html=True,
                    )
                    st.metric(
                        "Predicted product-store sales",
                        f"{result['Predicted_Product_Store_Sales_Total']:,.2f}",
                    )
                    st.caption(
                        "Model estimate for the selected inputs; validate against "
                        "realized sales before making inventory changes."
                    )
                    with st.expander("Inspect engineered API features"):
                        st.json(payload)
            else:
                st.error(
                    f"Prediction request failed ({response.status_code}): "
                    f"{response_error(response)}"
                )
        except ValueError as exc:
            st.error(f"Input validation failed: {exc}")
        except requests.RequestException as exc:
            st.error(f"Could not reach the model API: {exc}")

with batch_tab:
    with st.container(border=True):
        st.subheader("Bring a batch")
        st.caption(
            "Upload one row per product-store combination. Supported rows receive "
            "estimates; unsupported rows remain visible for review. Unlike the "
            "single-item form, batch CSVs must contain the 10 model-ready columns below."
        )
        with st.expander("Required CSV fields"):
            st.code(", ".join(MODEL_FEATURES), language="text")
        template = pd.DataFrame(
            [{
                "Product_Weight": 12.66,
                "Product_Sugar_Content": "Regular",
                "Product_Allocated_Area": 0.027,
                "Product_MRP": 117.08,
                "Store_Size": "Medium",
                "Store_Location_City_Type": "Tier 2",
                "Store_Type": "Supermarket Type1",
                "Product_Id_char": "FD",
                "Store_Age_Years": 16,
                "Product_Type_Category": "Perishables",
            }],
            columns=MODEL_FEATURES,
        )
        st.download_button(
            "Download model-ready CSV template",
            template.to_csv(index=False).encode("utf-8"),
            file_name="superkart_model_input_template.csv",
            mime="text/csv",
        )
    uploaded = st.file_uploader(
        "Choose a CSV file", type=["csv"], accept_multiple_files=False
    )
    if uploaded is not None and st.button(
        "Estimate batch", type="primary", use_container_width=True
    ):
        try:
            source = pd.read_csv(uploaded)
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            st.error(f"Could not read the CSV: {exc}")
        else:
            missing = [field for field in MODEL_FEATURES if field not in source.columns]
            extra = [field for field in source.columns if field not in MODEL_FEATURES]
            if missing or extra:
                details = []
                if missing:
                    details.append(f"missing columns: {', '.join(missing)}")
                if extra:
                    details.append(f"unexpected columns: {', '.join(map(str, extra))}")
                st.error("; ".join(details))
            else:
                try:
                    response = requests.post(
                        f"{api_url}/v1/predictbatch",
                        files={
                            "file": (
                                uploaded.name,
                                uploaded.getvalue(),
                                "text/csv",
                            )
                        },
                        timeout=60,
                    )
                except requests.RequestException as exc:
                    st.error(f"Could not reach the model API: {exc}")
                else:
                    if not response.ok:
                        st.error(
                            f"Batch request failed ({response.status_code}): "
                            f"{response_error(response)}"
                        )
                    else:
                        result = response.json()
                        st.markdown(
                            '<p class="eyebrow">BATCH RUN / ROW SUMMARY</p>',
                            unsafe_allow_html=True,
                        )
                        rows, predicted, rejected = st.columns(3)
                        rows.metric("Rows received", result["rows_received"])
                        predicted.metric("Predicted", result["predicted_count"])
                        rejected.metric("Needs review", result["error_count"])
                        predictions = pd.DataFrame(
                            result["predictions"],
                            columns=[
                                "row",
                                "Predicted_Product_Store_Sales_Total",
                            ],
                        )
                        if not predictions.empty:
                            st.subheader("Sales estimates")
                            st.dataframe(
                                predictions, use_container_width=True, hide_index=True
                            )
                            st.download_button(
                                "Download estimates CSV",
                                predictions.to_csv(index=False).encode("utf-8"),
                                file_name="superkart_sales_estimates.csv",
                                mime="text/csv",
                            )
                        errors = pd.DataFrame(result["errors"])
                        if not errors.empty:
                            st.subheader("Rows to review")
                            st.info(
                                "Unsupported values are reported, not silently "
                                "converted into a prediction."
                            )
                            st.dataframe(errors, use_container_width=True, hide_index=True)
                        if result["warnings"]:
                            st.subheader("Warnings")
                            st.write(result["warnings"])

st.markdown(
    """
    <div class="footer-note">
      SUPERKART / SALES STUDIO &nbsp;·&nbsp; Estimates are model outputs based on
      supplied product and store attributes. This snapshot contains no transaction
      dates, so it does not model seasonality or guarantee future-quarter sales.
    </div>
    """,
    unsafe_allow_html=True,
)
