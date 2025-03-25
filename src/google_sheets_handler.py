import os
import pandas as pd
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

API_KEY = os.getenv('GOOGLE_SHEETS_API_KEY')

def extract_sheet_id_from_url(sheet_url):
    """Extract the sheet ID from a Google Sheets URL."""
    try:
        if '/d/' in sheet_url:
            # Format: https://docs.google.com/spreadsheets/d/[spreadsheet_id]/edit#gid=0
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            return sheet_id
        raise ValueError("Could not find sheet ID in URL")
    except Exception:
        raise ValueError("Invalid Google Sheets URL format")

def get_available_sheets(spreadsheet_id):
    """Get list of available sheets in the spreadsheet."""
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'sheets' in data:
            available_sheets = [sheet['properties']['title'] for sheet in data['sheets']]
            logger.debug(f"Available sheets: {available_sheets}")
            return available_sheets
            
        raise ValueError("No sheets found in the spreadsheet")
    except requests.exceptions.RequestException as e:
        if e.response.status_code == 403:
            raise ValueError("Access denied. Please make sure the sheet is publicly accessible (Anyone with the link can view).")
        raise

def read_google_sheet(sheet_url, sheet_name=None):
    """Read data from a public Google Sheet using API key."""
    try:
        logger.debug(f"Attempting to read Google Sheet from URL: {sheet_url}")
        
        # Extract the spreadsheet ID from the URL
        spreadsheet_id = extract_sheet_id_from_url(sheet_url)
        logger.debug(f"Extracted spreadsheet ID: {spreadsheet_id}")
        
        # If no sheet name provided, get available sheets
        if not sheet_name:
            return get_available_sheets(spreadsheet_id)
        
        logger.debug(f"Using sheet name: {sheet_name}")
        
        # Construct the Google Sheets API URL
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}?key={API_KEY}"
        logger.debug(f"Making request to: {url}")
        
        # Make the request
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        if 'values' not in data:
            raise ValueError("No data found in the Google Sheet")
            
        values = data['values']
        if not values:
            raise ValueError("Sheet is empty")
        
        # Debug log the data structure
        logger.debug("Raw data from Google Sheets:")
        logger.debug(f"Number of rows: {len(values)}")
        
        # Find the payroll section start (row that contains "Name" in first column)
        payroll_start = None
        for idx, row in enumerate(values):
            if row and row[0].strip() == 'Name':
                payroll_start = idx
                break
        
        if payroll_start is None:
            raise ValueError("Could not find payroll header (row starting with 'Name') in the sheet")
            
        logger.debug(f"Found payroll header at row {payroll_start}")
        
        # Get the header row and data
        header_row = values[payroll_start]
        data_rows = values[payroll_start + 1:]
        
        # Ensure all rows have the same number of columns as the header
        max_cols = len(header_row)
        padded_rows = []
        for row in data_rows:
            # Pad shorter rows with empty strings
            padded_row = row + [''] * (max_cols - len(row)) if len(row) < max_cols else row[:max_cols]
            padded_rows.append(padded_row)
        
        # Clean up column names - keep original names but handle empty ones
        column_names = []
        for i, col in enumerate(header_row):
            if not col:  # Empty column name
                column_names.append(f'Unnamed: {i}')
            else:
                column_names.append(str(col).strip())
        
        logger.debug(f"Column names: {column_names}")
        
        # Convert to DataFrame
        df = pd.DataFrame(padded_rows, columns=column_names)
        
        # Debug log the DataFrame
        logger.debug("DataFrame after conversion:")
        logger.debug(f"DataFrame columns: {df.columns.tolist()}")
        logger.debug(f"DataFrame shape: {df.shape}")
        logger.debug(f"First row of DataFrame:\n{df.iloc[0] if not df.empty else 'Empty DataFrame'}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 403:
                raise Exception("Access denied. Please make sure the sheet is publicly accessible (Anyone with the link can view).")
            elif e.response.status_code == 404:
                raise Exception("Sheet not found. Please check the URL and make sure the sheet exists.")
        logger.error(f"Error reading Google Sheet: {str(e)}")
        raise Exception(f"Error reading Google Sheet: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Google Sheet: {str(e)}")
        raise Exception(f"Error processing Google Sheet: {str(e)}")

def get_user_email():
    """Get the email of the currently authenticated user."""
    return None 