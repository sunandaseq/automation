# Maharashtra Nursing Council Schedule Monitor

Automated script that scrapes the CPD Schedule from Maharashtra Nursing Council website, stores it in Supabase, and sends email notifications when changes are detected.

## Features

- 🕷️ Web scraping of schedule table
- 📊 Data storage in Supabase
- 🔍 Change detection and comparison
- 📧 Email notifications on updates
- ⏰ Automated execution every 30 minutes via GitHub Actions

## Setup Instructions

### 1. Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Create a table named `nursing_schedule` with the following structure:
   ```sql
   CREATE TABLE nursing_schedule (
     id BIGSERIAL PRIMARY KEY,
     "City" TEXT,
     "Starts On" TEXT,
     "Ends On" TEXT,
     "CPD Title" TEXT,
     "CPD Type" TEXT,
     "Credit Hours" TEXT,
     "No Fees" TEXT,
     "View" TEXT,
     scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```
3. Get your Supabase URL and anon key from Project Settings > API

### 2. Email Setup (Gmail)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account > Security > 2-Step Verification > App passwords
   - Create a new app password for "Mail"
3. Use this app password in the configuration

### 3. GitHub Repository Setup

1. Create a new GitHub repository
2. Push this code to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_REPO_URL
   git push -u origin main
   ```

### 4. Configure GitHub Secrets

Go to your repository Settings > Secrets and variables > Actions, and add:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `SMTP_SERVER`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SENDER_EMAIL`: Your Gmail address
- `SENDER_PASSWORD`: Your Gmail app password
- `RECIPIENT_EMAIL`: Email address to receive notifications

### 5. Local Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

3. Fill in your credentials in `.env`

4. Run the script:
   ```bash
   python test.py
   ```

## How It Works

1. **Scraping**: Fetches the schedule table from the website
2. **Comparison**: Compares scraped data with existing Supabase data
3. **Update**: If changes detected, updates Supabase with new data
4. **Notification**: Sends email with details of changes
5. **Automation**: GitHub Actions runs this every 30 minutes

## Manual Trigger

You can manually trigger the workflow from GitHub Actions tab:
1. Go to Actions > Schedule Scraper
2. Click "Run workflow"

## Monitoring

- Check GitHub Actions logs for execution details
- Email notifications will be sent only when changes are detected
- Failed runs will upload error logs as artifacts

## Customization

### Change Schedule Interval

Edit `.github/workflows/schedule-scraper.yml`:
```yaml
schedule:
  - cron: '*/30 * * * *'  # Change this (e.g., '0 */2 * * *' for every 2 hours)
```

### Modify Table Name

Change `TABLE_NAME` in `test.py`:
```python
TABLE_NAME = 'your_table_name'
```

## Troubleshooting

- **Email not sending**: Verify Gmail app password and 2FA is enabled
- **Supabase errors**: Check URL and key, verify table exists
- **Scraping fails**: Website might have changed structure; update selectors
- **GitHub Actions not running**: Verify workflow file is in `.github/workflows/`

## License

MIT
