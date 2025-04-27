from django.core.management.base import BaseCommand
from createFanlink.views import generate_fanlink_toSheet
import time
from google.oauth2 import service_account
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

class Command(BaseCommand):
    help = "Continuously update Google Sheet fanlinks"

    def handle(self, *args, **kwargs):
        print("🚀 Fanlink updater started...")
        while True:
            try:
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                # Get the absolute path to the root directory
                BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
                creds_path = os.path.join(BASE_DIR, "fanlink-440822-6316459498b3.json")

                # Use the credentials path
                creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
                client = gspread.authorize(creds)
                # Open Google Sheet by its key
                spreadsheet = client.open_by_key("1j4DSWgEECumRDfJ6ZEOLg4NapMpxgRa-dX6QMifQCy0") 
                # Open the specific worksheet
                sheet = spreadsheet.worksheet("The Orchard")  # Change "Sheet1" if needed
                expected_headers = ['Label', 'Artist', 'Release', 'UPC', 'Date', 'Links','ISRC']
                all_data = sheet.get_all_records(expected_headers=expected_headers)
                empty_fanlink_rows = [i for i, row in enumerate(all_data) if row.get('Fanlinks', '').strip() == '']
                print("connected to sheet and empty rows collected the sheet")
                if not empty_fanlink_rows:
                    print("No empty Fanlink found on the sheet")
                else:
                    target_indexes = empty_fanlink_rows[:5]

                    for idx in target_indexes:
                        row_data = all_data[idx]
                        fanlink = generate_fanlink_toSheet(row_data["Artist"],row_data["Release"],row_data["Label"],row_data["ISRC"],row_data["Date"])
                        sheet.update_cell(idx + 2, 8, fanlink["fanlink"])
                        sheet.update_cell(idx + 2, 9, fanlink["missingLinks"])  
                print("✅ Fanlink update done. Waiting for next round...")
                time.sleep(120)  # wait 3 minutes
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)
