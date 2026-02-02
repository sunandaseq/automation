import requests
from bs4 import BeautifulSoup
import pandas as pd

def extract_schedule_table():
    """Extract the CPD Schedule table from Maharashtra Nursing Council website"""
    url = "https://www.maharashtranursingcouncil.org/ScheduleCNE.aspx"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
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
        for tr in table.find_all('tr')[1:]:
            cells = tr.find_all(['td', 'th'])
            row = [cell.get_text(strip=True) for cell in cells]
            if row:
                rows.append(row)
        
        if rows and table_headers:
            df = pd.DataFrame(rows, columns=table_headers)
            return df
        else:
            print("Could not extract table data properly")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

print("=" * 80)
print("SUPABASE TABLE STRUCTURE GUIDE")
print("=" * 80)

df = extract_schedule_table()

if df is not None:
    print(f"\n✓ Found {len(df)} rows with {len(df.columns)} columns\n")
    
    print("COLUMNS TO CREATE IN SUPABASE:")
    print("-" * 80)
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. {col} (type: text)")
    print(f"{len(df.columns) + 1}. scraped_at (type: timestamp)")
    
    print("\n" + "=" * 80)
    print("SAMPLE DATA:")
    print("=" * 80)
    print(df.to_string())
    
    print("\n" + "=" * 80)
    print("INSTRUCTIONS FOR SUPABASE:")
    print("=" * 80)
    print("1. Go to your Supabase project dashboard")
    print("2. Click on 'Table Editor' in the left sidebar")
    print("3. Click 'Create a new table'")
    print("4. Name it: nursing_schedule")
    print("5. Add the following columns (in addition to the auto-created 'id'):")
    print()
    for col in df.columns:
        print(f"   - Column name: {col}")
        print(f"     Type: text")
        print(f"     Default: (leave empty)")
        print()
    print(f"   - Column name: scraped_at")
    print(f"     Type: timestamp")
    print(f"     Default: (leave empty)")
    print()
    print("6. Click 'Save' to create the table")
    print("=" * 80)
else:
    print("\n✗ Failed to extract table data from website")
