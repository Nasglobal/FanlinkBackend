import pandas as pd
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials


BATCH_SIZE = 500
SLEEP_TIME = 60  # seconds

# Authenticate and connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("./fanlink-440822-6316459498b3.json", scope)
client = gspread.authorize(creds)

# Open Google Sheet by its key
spreadsheet = client.open_by_key("1j4DSWgEECumRDfJ6ZEOLg4NapMpxgRa-dX6QMifQCy0") 
# Open the specific worksheet
sheet = spreadsheet.worksheet("The Orchard")  # Change "Sheet1" if needed

# Load local Excel file
df_catalogue = pd.read_excel("data/20250210_172548_DRMSYS_CATALOGUE_ALL_352404.xlsx")


# Filter out deleted entries
df_catalogue = df_catalogue[df_catalogue['Deleted'] == 'N']

# Rename columns to match Google Sheet
df_catalogue_renamed = df_catalogue.rename(columns={
    'LabelName': 'Label',
    'Artist': 'Artist',
    'ReleaseName': 'Release',
    'DisplayUPC': 'UPC',
    'ISRC': 'ISRC',
    'ReleaseDate': 'Date'
})

# Get existing sheet data
expected_headers = ['Label', 'Artist', 'Release', 'UPC', 'Date', 'Links','ISRC']
sheet_data = sheet.get_all_records(expected_headers=expected_headers)
df_sheet = pd.DataFrame(sheet_data)

# Create a set of existing key tuples for fast lookup
existing_keys = set(
    zip(df_sheet['Label'], df_sheet['Artist'], df_sheet['UPC'], df_sheet['ISRC'])
)

# Filter out rows that already exist
def is_new_row(row):
    return (row['Label'], row['Artist'], row['UPC'], row['ISRC']) not in existing_keys

df_new_rows = df_catalogue_renamed[df_catalogue_renamed.apply(is_new_row, axis=1)]

print(f"{len(df_new_rows)} new rows to be added...")

# Reorder to match Google Sheet: Label, Artist, Release, UPC, Date, Links, ISRC
new_rows = df_new_rows[['Label', 'Artist', 'Release', 'UPC', 'Date', 'ISRC']].fillna('').values.tolist()
row_batches = [new_rows[i:i+BATCH_SIZE] for i in range(0, len(new_rows), BATCH_SIZE)]

for i, batch in enumerate(row_batches):
    # Insert empty 'Links' column between Date and ISRC
    for row in batch:
        row.insert(5, '')  # Insert empty string at index 5 for 'Links'
    sheet.append_rows(batch, value_input_option='RAW')
    print(f"Batch {i+1}/{len(row_batches)} uploaded: {len(batch)} rows.")
    
    if i < len(row_batches) - 1:
        print(f"Sleeping for {SLEEP_TIME} seconds to avoid rate limit...")
        time.sleep(SLEEP_TIME)

print("✅ All rows processed.")
