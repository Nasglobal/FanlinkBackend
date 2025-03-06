import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate and connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("./fanlink-440822-6316459498b3.json", scope)
client = gspread.authorize(creds)

# Open Google Sheet by its key
spreadsheet = client.open_by_key("1j4DSWgEECumRDfJ6ZEOLg4NapMpxgRa-dX6QMifQCy0")  

# Open the specific worksheet
worksheet = spreadsheet.worksheet("The Orchard")  # Change "Sheet1" if needed

# Fetch all data from the worksheet
google_data = worksheet.get_all_values()

# Convert Google Sheet data to DataFrame
headers = google_data[0]  # Extract headers
google_df = pd.DataFrame(google_data[1:], columns=headers)

# Load local Excel file
local_df = pd.read_excel("data/20250127_153700_DRMSYS_CATALOGUE_ALL_352404.xlsx")

# Convert UPC to string to avoid mismatches due to type differences
google_df["UPC"] = google_df["UPC"].astype(str)
local_df["DisplayUPC"] = local_df["DisplayUPC"].astype(str)

# Create a dictionary mapping UPC to ISRC from local file
upc_to_isrc = dict(zip(local_df["DisplayUPC"], local_df["ISRC"]))

# Update only the ISRC column in Google Sheets DataFrame where UPC matches
google_df["ISRC"] = google_df["UPC"].map(lambda x: upc_to_isrc.get(x, google_df.loc[google_df["UPC"] == x, "ISRC"].values[0]))

# Prepare the updated ISRC column values for Google Sheets
isrc_column_index = headers.index("ISRC") + 1  # Find ISRC column index (1-based for Google Sheets)
updated_isrc_values = google_df["ISRC"].tolist()
print("Access granted! updating....")
# Update only the ISRC column in Google Sheets
cell_range = f"{chr(64 + isrc_column_index)}2:{chr(64 + isrc_column_index)}{len(updated_isrc_values) + 1}"  # Example: B2:B100
worksheet.update(cell_range, [[value] for value in updated_isrc_values])

print("ISRC column updated successfully!")
