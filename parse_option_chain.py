import pandas as pd
from utils.fetch_option_chain import fetch_option_chain

def parse_option_chain(expiry_date="2025-05-02"):
    data = fetch_option_chain(expiry_date)

    if data is None or 'records' not in data:
        print("Invalid or empty data from API.")
        return None

    all_data = data['records']['data']
    print(f"Total option entries fetched: {len(all_data)}")

    # Print unique expiry dates to debug
    expiry_dates = set(item.get("expiryDate") for item in all_data if "expiryDate" in item)
    print(f"Available expiry dates: {expiry_dates}")

    # Filter only matching expiry
    filtered_data = [item for item in all_data if item.get("expiryDate") == expiry_date]
    print(f"Entries for {expiry_date}: {len(filtered_data)}")

    if not filtered_data:
        print("⚠️ No data found for the given expiry date. Try one from above list.")
        return None

    rows = []
    for item in filtered_data:
        row = {
            "strikePrice": item.get("strikePrice"),
            "CE_OI": item.get("CE", {}).get("openInterest"),
            "CE_ChangeOI": item.get("CE", {}).get("changeinOpenInterest"),
            "CE_LTP": item.get("CE", {}).get("lastPrice"),
            "CE_Volume": item.get("CE", {}).get("totalTradedVolume"),
            "PE_OI": item.get("PE", {}).get("openInterest"),
            "PE_ChangeOI": item.get("PE", {}).get("changeinOpenInterest"),
            "PE_LTP": item.get("PE", {}).get("lastPrice"),
            "PE_Volume": item.get("PE", {}).get("totalTradedVolume"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    print("Columns in DataFrame:", df.columns.tolist())

    if "strikePrice" not in df.columns:
        print("❌ 'strikePrice' not found in DataFrame. Something went wrong.")
        return None

    df = df.sort_values(by="strikePrice").reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = parse_option_chain()
    if df is not None:
        print(df.head(10))
