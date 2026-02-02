import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
import hashlib
import json

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
TABLE_NAME = 'nursing_schedule'

# Email configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

def extract_schedule_table():
    """
    Extract the CPD Schedule table from Maharashtra Nursing Council website
    """
    url = "https://www.maharashtranursingcouncil.org/ScheduleCNE.aspx"
    
    try:
        # Send GET request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table
        table = soup.find('table')
        
        if not table:
            print("No table found on the page")
            return None
        
        # Extract table headers
        table_headers = []
        header_row = table.find('tr')
        if header_row:
            table_headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # Extract table rows
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header row
            cells = tr.find_all(['td', 'th'])
            row = [cell.get_text(strip=True) for cell in cells]
            if row:  # Only add non-empty rows
                rows.append(row)
        
        # Create DataFrame
        if rows and table_headers:
            df = pd.DataFrame(rows, columns=table_headers)
            return df
        else:
            print("Could not extract table data properly")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error processing the data: {e}")
        return None

def initialize_supabase():
    """Initialize Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_data_hash(df):
    """Generate hash of dataframe for comparison"""
    data_string = df.to_json(orient='records')
    return hashlib.md5(data_string.encode()).hexdigest()

def fetch_existing_data(supabase: Client):
    """Fetch existing data from Supabase"""
    try:
        response = supabase.table(TABLE_NAME).select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return pd.DataFrame()

def update_supabase(supabase: Client, new_df):
    """Update Supabase with new data"""
    try:
        # Delete all existing records
        supabase.table(TABLE_NAME).delete().neq('id', 0).execute()
        
        # Insert new records
        records = new_df.to_dict('records')
        for record in records:
            # Add timestamp
            record['scraped_at'] = datetime.now().isoformat()
            supabase.table(TABLE_NAME).insert(record).execute()
        
        print(f"✓ Successfully updated {len(records)} records in Supabase")
        return True
    except Exception as e:
        print(f"Error updating Supabase: {e}")
        return False

def send_email_notification(subject, body):
    """Send email notification about changes using SendGrid"""
    if not all([SENDGRID_API_KEY, SENDER_EMAIL, RECIPIENT_EMAIL]):
        print("Email configuration not complete. Skipping email notification.")
        print(f"  - SendGrid API Key: {'✓' if SENDGRID_API_KEY else '✗'}")
        print(f"  - Sender Email: {'✓' if SENDER_EMAIL else '✗'}")
        print(f"  - Recipient Email: {'✓' if RECIPIENT_EMAIL else '✗'}")
        return False
    
    try:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=RECIPIENT_EMAIL,
            subject=subject,
            html_content=body
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"✓ Email notification sent successfully (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def compare_dataframes(old_df, new_df):
    """Compare two dataframes and return differences"""
    changes = {
        'added': [],
        'removed': [],
        'modified': []
    }
    
    if old_df.empty:
        changes['added'] = new_df.to_dict('records')
        return changes
    
    # Normalize column names for comparison
    old_cols = old_df.columns.tolist()
    new_cols = new_df.columns.tolist()
    
    # Use first column as identifier (usually City or similar)
    if len(new_cols) > 0:
        key_col = new_cols[0]
        
        old_keys = set(old_df[key_col].values) if key_col in old_df.columns else set()
        new_keys = set(new_df[key_col].values)
        
        # Find added rows
        added_keys = new_keys - old_keys
        if len(added_keys) > 0:
            changes['added'] = new_df[new_df[key_col].isin(added_keys)].to_dict('records')
        
        # Find removed rows
        removed_keys = old_keys - new_keys
        if len(removed_keys) > 0:
            changes['removed'] = old_df[old_df[key_col].isin(removed_keys)].to_dict('records')
    
    return changes

def format_email_body(changes, new_df):
    """Format email body with changes"""
    html = f"""
    <html>
        <head>
            <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 20px;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                td {{
                    padding: 10px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                tr:hover {{
                    background-color: #e0e0e0;
                }}
                .added-header {{
                    background-color: #4CAF50;
                }}
                .removed-header {{
                    background-color: #f44336;
                }}
            </style>
        </head>
        <body>
            <h2>Maharashtra Nursing Council Schedule Update</h2>
            <p><strong>Update Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Records:</strong> {len(new_df)}</p>
            <p><strong>Website:</strong> <a href="https://www.maharashtranursingcouncil.org/CNE/CNELogin.aspx">https://www.maharashtranursingcouncil.org/CNE/CNELogin.aspx</a></p>
            <hr>
    """
    
    if changes['added']:
        html += f"<h3>✅ New Entries Added ({len(changes['added'])})</h3>"
        added_df = pd.DataFrame(changes['added'])
        html += "<table>"
        # Add table headers
        html += "<tr>"
        for col in added_df.columns:
            html += f"<th class='added-header'>{col}</th>"
        html += "</tr>"
        # Add table rows (limit to first 20 to keep email manageable)
        for _, row in added_df.head(20).iterrows():
            html += "<tr>"
            for val in row:
                html += f"<td>{val}</td>"
            html += "</tr>"
        html += "</table>"
        if len(added_df) > 20:
            html += f"<p><em>Showing first 20 of {len(added_df)} added entries</em></p>"
    
    if changes['removed']:
        html += f"<h3>❌ Entries Removed ({len(changes['removed'])})</h3>"
        removed_df = pd.DataFrame(changes['removed'])
        html += "<table>"
        # Add table headers
        html += "<tr>"
        for col in removed_df.columns:
            html += f"<th class='removed-header'>{col}</th>"
        html += "</tr>"
        # Add table rows (limit to first 20 to keep email manageable)
        for _, row in removed_df.head(20).iterrows():
            html += "<tr>"
            for val in row:
                html += f"<td>{val}</td>"
            html += "</tr>"
        html += "</table>"
        if len(removed_df) > 20:
            html += f"<p><em>Showing first 20 of {len(removed_df)} removed entries</em></p>"
    
    if not changes['added'] and not changes['removed']:
        html += "<p>No changes detected in this run.</p>"
    
    html += """
            <hr>
            <p>This is an automated notification from the schedule monitoring system.</p>
        </body>
    </html>
    """
    return html

if __name__ == "__main__":
    print("=" * 80)
    print("Maharashtra Nursing Council Schedule Monitor")
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # Extract the table
        print("\n1. Extracting schedule table from website...")
        new_df = extract_schedule_table()
        
        if new_df is None:
            print("✗ Failed to extract table data")
            exit(1)
        
        print(f"   ✓ Extracted {len(new_df)} rows")
        
        # Initialize Supabase
        print("\n2. Connecting to Supabase...")
        supabase = initialize_supabase()
        print("   ✓ Connected to Supabase")
        
        # Fetch existing data
        print("\n3. Fetching existing data from Supabase...")
        old_df = fetch_existing_data(supabase)
        print(f"   ✓ Found {len(old_df)} existing records")
        
        # Compare data
        print("\n4. Comparing data...")
        new_hash = get_data_hash(new_df)
        old_hash = get_data_hash(old_df) if not old_df.empty else ""
        
        if new_hash != old_hash:
            print("   ✓ Data difference detected - checking for actual changes...")
            changes = compare_dataframes(old_df, new_df)
            print(f"     - New entries: {len(changes['added'])}")
            print(f"     - Removed entries: {len(changes['removed'])}")
            
            # Only update and notify if there are actual row changes
            if len(changes['added']) > 0 or len(changes['removed']) > 0:
                # Update Supabase
                print("\n5. Updating Supabase...")
                if update_supabase(supabase, new_df):
                    # Send email notification
                    print("\n6. Sending email notification...")
                    email_subject = f"Schedule Update Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    email_body = format_email_body(changes, new_df)
                    send_email_notification(email_subject, email_body)
                else:
                    print("✗ Failed to update Supabase")
            else:
                print("   ✓ No actual row changes detected - skipping update and notification")
        else:
            print("   ✓ No changes detected - data is up to date")
        
        print("\n" + "=" * 80)
        print("✓ Process completed successfully")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        exit(1)
