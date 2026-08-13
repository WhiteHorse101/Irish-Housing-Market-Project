import os
import zipfile
from datetime import datetime, timedelta

import pandas as pd
import requests
import re
import numpy as np

PPR_URL = "https://www.propertypriceregister.ie/website/npsra/ppr/npsra-ppr.nsf/Downloads/PPR-ALL.zip/$FILE/PPR-ALL.zip"
DATA_DIR = "data"
ZIP_PATH = os.path.join(DATA_DIR, "PPR-ALL.zip")
CLEAN_CSV_PATH = os.path.join(DATA_DIR, "ppr_clean.csv")


def download_ppr_zip(dest_path=ZIP_PATH):
    if os.path.exists(dest_path):
        print(f"Zip already downloaded at {dest_path}, skipping.")
        return dest_path

    print("Downloading Property Price Register data...")
    response = requests.get(PPR_URL, stream=True, timeout=60)
    response.raise_for_status()

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return dest_path


def extract_csv(zip_path=ZIP_PATH, extract_dir=DATA_DIR):
    with zipfile.ZipFile(zip_path) as zf:
        csv_name = zf.namelist()[0]
        zf.extract(csv_name, extract_dir)
    return os.path.join(extract_dir, csv_name)


def load_and_filter(csv_path, months_back=24):
    # The register export is Windows-1252 encoded, not UTF-8 (the "€" in
    # "Price (€)" is a single 0x80 byte, which only decodes correctly as cp1252).
    df = pd.read_csv(csv_path, encoding="cp1252", low_memory=False)

    df["Date of Sale (dd/mm/yyyy)"] = pd.to_datetime(
        df["Date of Sale (dd/mm/yyyy)"], format="%d/%m/%Y"
    )

    cutoff = datetime.now() - timedelta(days=months_back * 30)
    return df[df["Date of Sale (dd/mm/yyyy)"] >= cutoff]


def clean(df):
    df = df.copy()

    df["Price"] = (
        df["Price (€)"]
        .str.replace("€", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    df["Not Full Market Price"] = df["Not Full Market Price"].map({"Yes": True, "No": False})
    df["VAT Exclusive"] = df["VAT Exclusive"].map({"Yes": True, "No": False})
    df["County"] = df["County"].str.strip().str.title()
    df = df.drop_duplicates()

    df["Date"] = df["Date of Sale (dd/mm/yyyy)"]
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month

    df = df.rename(columns={
        "Description of Property": "Property Type",
        "Property Size Description": "Size Band",
    })

        # Bulk/institutional sale detection — see notebooks/EDA.ipynb Section 3
    # for the full investigation and per-unit-price validation (~70% of
    # extractable cases confirmed mathematically plausible)
    bulk_pattern = re.compile(
        r'\bblocks\b'
        r'|\bsite for\b'
        r'|\b\d+\s*units?\b'
        r'|\b\d+\s*(?:residential\s+)?apartments?\b'
        r'|\b\d+\s*-\s*\d+\b'
        r'|\b\d+\s+to\s+\d+\b',
        re.IGNORECASE
    )
    flag_address = df["Address"].str.contains(bulk_pattern, regex=True)

    def _county_upper_bound(s, k=3):
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        return q3 + k * (q3 - q1)

    log_price = np.log(df["Price"])
    log_bounds = log_price.groupby(df["County"]).apply(_county_upper_bound)
    flag_statistical = log_price > df["County"].map(log_bounds)

    df["Likely Bulk Sale"] = flag_address | flag_statistical

    columns = [
    "Date", "Year", "Month", "Address", "County", "Eircode",
    "Price", "Not Full Market Price", "VAT Exclusive",
    "Property Type", "Likely Bulk Sale",
    ]

    df["Property Type"] = df["Property Type"].replace({
    "Teach/Árasán Cónaithe Atháimhe": "Second-Hand Dwelling house /Apartment",
    })

    return df[columns]


def save(df, out_path=CLEAN_CSV_PATH):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df):,} rows to {out_path}")


if __name__ == "__main__":
    zip_path = download_ppr_zip()
    csv_path = extract_csv(zip_path)
    filtered = load_and_filter(csv_path, months_back=24)
    cleaned = clean(filtered)
    save(cleaned)
