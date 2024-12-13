from google.oauth2 import service_account
from googleapiclient.discovery import build

# Set the scope for Google Drive and Sheets
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

# Initialize credentials
credentials = service_account.Credentials.from_service_account_file(
    './fanlink-440822-6316459498b3.json', scopes=SCOPES)

# Initialize Google Drive and Sheets services
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)

def fetch_sheet_data(spreadsheet_id, range_name):
    """Fetch data from a Google Sheet."""
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])
    
def setup_watch(file_id, webhook_url):
    """Register a webhook to watch for changes to a file."""
    body = {
        'id': 'unique-channel-id',  # A unique identifier for the channel
        'type': 'web_hook',
        'address': webhook_url,
    }
    response = drive_service.files().watch(fileId=file_id, body=body).execute()
    return response

def stop_watch(channel_id,resource_id):
    """Stop the existing watch channel."""
    body = {
        'id': channel_id,
        'resourceId': resource_id
    }
    drive_service.channels().stop(body=body).execute()
    print("Stopped watch for channel ID:",channel_id)


# Your OAuth2 credentials setup (modify as needed)
def get_google_credentials():
    return service_account.Credentials.from_service_account_file('./fanlink-440822-6316459498b3.json', scopes=[
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets',
    ])


# Function to fetch the last updated row
def get_last_updated_row(spreadsheet_id, sheet_name):
    credentials = get_google_credentials()
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    # Fetch all data from the sheet
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name
    ).execute()
    
    rows = result.get('values', [])
    return rows  

