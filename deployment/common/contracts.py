"""Shared feature engineering and validation for training and inference."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping

import pandas as pd

RAW_FEATURES = (
    "Product_Id",
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_Type",
    "Product_MRP",
    "Store_Establishment_Year",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
)
MODEL_FEATURES = (
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
)
NUMERIC_FEATURES = (
    "Product_Weight",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Age_Years",
)
CATEGORICAL_FEATURES = tuple(
    feature for feature in MODEL_FEATURES if feature not in NUMERIC_FEATURES
)
TARGET = "Product_Store_Sales_Total"
STORE_AGE_REFERENCE_YEAR = 2025

PRODUCT_TYPES = (
    "Baking Goods",
    "Breads",
    "Breakfast",
    "Canned",
    "Dairy",
    "Frozen Foods",
    "Fruits and Vegetables",
    "Hard Drinks",
    "Health and Hygiene",
    "Household",
    "Meat",
    "Others",
    "Seafood",
    "Snack Foods",
    "Soft Drinks",
    "Starchy Foods",
)
PERISHABLE_PRODUCT_TYPES = frozenset(
    {"Breads", "Dairy", "Frozen Foods", "Fruits and Vegetables", "Meat", "Seafood"}
)
PRODUCT_ID_PREFIXES = ("DR", "FD", "NC")
CATEGORY_VALUES = {
    "Product_Sugar_Content": ("Low Sugar", "No Sugar", "Regular"),
    "Store_Size": ("High", "Medium", "Small"),
    "Store_Location_City_Type": ("Tier 1", "Tier 2", "Tier 3"),
    "Store_Type": (
        "Departmental Store",
        "Food Mart",
        "Supermarket Type1",
        "Supermarket Type2",
    ),
    "Product_Id_char": PRODUCT_ID_PREFIXES,
    "Product_Type_Category": ("Non Perishables", "Perishables"),
}

_SUGAR_LABELS = {
    "low sugar": "Low Sugar",
    "no sugar": "No Sugar",
    "regular": "Regular",
    "reg": "Regular",
}
_PRODUCT_ID_PATTERN = re.compile(r"([A-Za-z]{2})\d+\Z")


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite.")
    return number


def _sugar_label(value: object) -> str:
    label = str(value).strip()
    normalized = _SUGAR_LABELS.get(label.casefold())
    if normalized is None:
        raise ValueError(
            "Product_Sugar_Content must be Low Sugar, No Sugar, or Regular."
        )
    return normalized


def engineer_raw_record(record: Mapping[str, object]) -> dict[str, object]:
    """Validate raw product/store fields and create the model's ten features."""
    missing = [field for field in RAW_FEATURES if field not in record]
    if missing:
        raise ValueError(f"Missing required raw fields: {', '.join(missing)}.")

    product_id = str(record["Product_Id"]).strip().upper()
    match = _PRODUCT_ID_PATTERN.fullmatch(product_id)
    if match is None:
        raise ValueError("Product_Id must start with two letters followed by digits.")
    product_id_prefix = match.group(1)
    if product_id_prefix not in PRODUCT_ID_PREFIXES:
        raise ValueError(f"Unsupported Product_Id prefix: {product_id_prefix}.")

    product_type = str(record["Product_Type"]).strip()
    if product_type not in PRODUCT_TYPES:
        raise ValueError(f"Unsupported Product_Type: {product_type}.")

    sugar_content = _sugar_label(record["Product_Sugar_Content"])
    store_size = str(record["Store_Size"]).strip()
    city_type = str(record["Store_Location_City_Type"]).strip()
    store_type = str(record["Store_Type"]).strip()
    for field, value in (
        ("Store_Size", store_size),
        ("Store_Location_City_Type", city_type),
        ("Store_Type", store_type),
    ):
        if value not in CATEGORY_VALUES[field]:
            raise ValueError(f"Unsupported {field}: {value}.")

    weight = _finite_number(record["Product_Weight"], "Product_Weight")
    area = _finite_number(record["Product_Allocated_Area"], "Product_Allocated_Area")
    mrp = _finite_number(record["Product_MRP"], "Product_MRP")
    establishment_year = _finite_number(
        record["Store_Establishment_Year"], "Store_Establishment_Year"
    )
    if weight <= 0:
        raise ValueError("Product_Weight must be greater than zero.")
    if not 0 < area <= 1:
        raise ValueError("Product_Allocated_Area must be greater than zero and at most one.")
    if mrp <= 0:
        raise ValueError("Product_MRP must be greater than zero.")
    if not establishment_year.is_integer():
        raise ValueError("Store_Establishment_Year must be a whole year.")
    store_age = STORE_AGE_REFERENCE_YEAR - int(establishment_year)
    if store_age < 0:
        raise ValueError(
            f"Store_Establishment_Year cannot be later than {STORE_AGE_REFERENCE_YEAR}."
        )

    return {
        "Product_Weight": weight,
        "Product_Sugar_Content": sugar_content,
        "Product_Allocated_Area": area,
        "Product_MRP": mrp,
        "Store_Size": store_size,
        "Store_Location_City_Type": city_type,
        "Store_Type": store_type,
        "Product_Id_char": product_id_prefix,
        "Store_Age_Years": store_age,
        "Product_Type_Category": (
            "Perishables"
            if product_type in PERISHABLE_PRODUCT_TYPES
            else "Non Perishables"
        ),
    }


def engineer_raw_dataframe(raw: pd.DataFrame) -> pd.DataFrame:
    """Apply the same validated transformations to every labeled raw row."""
    missing = [field for field in RAW_FEATURES if field not in raw.columns]
    if missing:
        raise ValueError(f"Missing required raw columns: {', '.join(missing)}.")
    engineered = []
    for index, row in raw.iterrows():
        try:
            engineered.append(engineer_raw_record(row.to_dict()))
        except ValueError as exc:
            raise ValueError(f"Invalid source row {index}: {exc}") from exc
    return pd.DataFrame(engineered, index=raw.index, columns=MODEL_FEATURES)


def validate_model_record(record: Mapping[str, object]) -> dict[str, object]:
    """Validate one already-engineered inference row against the training contract."""
    missing = [field for field in MODEL_FEATURES if field not in record]
    extra = [field for field in record if field not in MODEL_FEATURES]
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected fields: {', '.join(map(str, extra))}")
        raise ValueError("; ".join(details))

    cleaned: dict[str, object] = {}
    for field in NUMERIC_FEATURES:
        number = _finite_number(record[field], field)
        if field in {"Product_Weight", "Product_MRP"} and number <= 0:
            raise ValueError(f"{field} must be greater than zero.")
        if field == "Product_Allocated_Area" and not 0 < number <= 1:
            raise ValueError(
                "Product_Allocated_Area must be greater than zero and at most one."
            )
        if field == "Store_Age_Years" and (number < 0 or not number.is_integer()):
            raise ValueError("Store_Age_Years must be a non-negative whole number.")
        cleaned[field] = int(number) if field == "Store_Age_Years" else number

    for field in CATEGORICAL_FEATURES:
        value = str(record[field]).strip()
        if field == "Product_Sugar_Content":
            value = _sugar_label(value)
        if value not in CATEGORY_VALUES[field]:
            raise ValueError(f"Unsupported {field}: {value}.")
        cleaned[field] = value
    return {field: cleaned[field] for field in MODEL_FEATURES}
