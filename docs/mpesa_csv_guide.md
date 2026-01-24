# How to Convert M-Pesa Statement to CSV

## Required CSV Format

The AfricGraph ingestion system expects an M-Pesa CSV file with the following columns (column names are flexible):

### Required Columns:
- **Receipt No** (or: Receipt No., Receipt, Transaction ID, Receipt Number)
- **Completion Time** (or: Date, Completion Time, Time)
- **Details** (or: Description, Narration, Particulars)
- **Transaction Status** (or: Status, Transaction Status)
- **Paid In** (or: Credit, Amount Received, Deposit) - for money received
- **Withdrawn** (or: Debit, Amount Sent, Withdrawal) - for money sent
- **Balance** (or: Running Balance, Account Balance)

### Example CSV Format:

```csv
Receipt No,Completion Time,Details,Transaction Status,Paid In,Withdrawn,Balance
RFT123456789,2024-01-15 10:30:00,Payment from John Doe,Completed,5000.00,,15000.00
RFT123456790,2024-01-15 14:20:00,Payment to Jane Smith,Completed,,2000.00,13000.00
RFT123456791,2024-01-16 09:15:00,Paybill 123456 - Utility Co,Completed,,1500.00,11500.00
```

## Methods to Convert M-Pesa Statement to CSV

### Method 1: Download from M-Pesa Website (Recommended)

1. **Log in to M-Pesa Portal:**
   - Go to https://www.safaricom.co.ke/personal/m-pesa/m-pesa-services/m-pesa-statement/
   - Log in with your M-Pesa credentials

2. **Download Statement:**
   - Navigate to "Statement" or "Transaction History"
   - Select your date range
   - Download as CSV (if available) or Excel
   - If Excel, open in Excel/Google Sheets and save as CSV

3. **Verify Format:**
   - Open the CSV file
   - Ensure it has the columns listed above
   - If column names differ, rename them to match (or the parser will auto-detect)

### Method 2: Export from M-Pesa App

1. **Open M-Pesa App:**
   - Launch the M-Pesa app on your phone
   - Go to "Statements" or "Transaction History"

2. **Export:**
   - Look for "Export" or "Share" option
   - Select CSV format if available
   - Email it to yourself or save to cloud storage

### Method 3: Manual Conversion from PDF

If you only have a PDF statement:

1. **Extract Data:**
   - Use a PDF to Excel converter (online tools like Adobe Acrobat, SmallPDF, or Zamzar)
   - Or manually copy data from PDF to Excel/Google Sheets

2. **Format in Excel/Google Sheets:**
   - Create columns: Receipt No, Completion Time, Details, Transaction Status, Paid In, Withdrawn, Balance
   - Copy data from PDF into appropriate columns
   - Ensure dates are in format: `YYYY-MM-DD HH:MM:SS` or `DD/MM/YYYY HH:MM:SS`
   - Amounts should be numbers (no currency symbols)

3. **Save as CSV:**
   - File → Save As → CSV (Comma delimited)

### Method 4: Convert from SMS/Text Format

If you have transaction data in text format:

1. **Create CSV Template:**
   - Open Excel or Google Sheets
   - Create headers: Receipt No, Completion Time, Details, Transaction Status, Paid In, Withdrawn, Balance

2. **Parse Text Data:**
   - Extract receipt numbers, dates, amounts, and descriptions
   - Fill in each column
   - For "Paid In" vs "Withdrawn":
     - If money came in → put amount in "Paid In", leave "Withdrawn" empty
     - If money went out → put amount in "Withdrawn", leave "Paid In" empty

3. **Save as CSV**

## CSV Template

Here's a blank template you can use:

```csv
Receipt No,Completion Time,Details,Transaction Status,Paid In,Withdrawn,Balance
```

## Important Notes

1. **Date Format:**
   - Preferred: `YYYY-MM-DD HH:MM:SS` (e.g., `2024-01-15 10:30:00`)
   - Also accepted: `DD/MM/YYYY HH:MM:SS` or `MM/DD/YYYY HH:MM:SS`

2. **Amount Format:**
   - Use numbers only (no currency symbols, commas, or spaces)
   - Decimal separator: period (.) not comma
   - Example: `5000.00` not `5,000.00` or `KES 5000`

3. **Empty Values:**
   - If a transaction is "Paid In", leave "Withdrawn" empty
   - If a transaction is "Withdrawn", leave "Paid In" empty
   - Balance should always have a value

4. **File Encoding:**
   - Save CSV as UTF-8 encoding to handle special characters

5. **File Location:**
   - The CSV file must be accessible to the backend server
   - Use absolute path when triggering ingestion via Admin panel
   - Example: `/path/to/your/mpesa_statement.csv`

## Using the CSV in AfricGraph

Once you have your CSV file:

1. **Place file on server:**
   - Upload CSV to a location accessible by the backend
   - Note the full path (e.g., `/Users/la/Desktop/mpesa_statement.csv`)

2. **Trigger Ingestion:**
   - Go to Admin → Ingestion Management
   - Select "Mobile Money Ingestion"
   - Enter the file path
   - Select provider: "M-Pesa"
   - Currency: "KES"
   - Click "Start Ingestion"

3. **Monitor Progress:**
   - Watch the job status in the Admin panel
   - Check for any parsing errors

## Troubleshooting

- **"Column not found" errors:** Ensure column names match one of the accepted names
- **"Date parsing error":** Check date format matches expected formats
- **"Amount parsing error":** Remove currency symbols and commas from amounts
- **"File not found":** Ensure the file path is absolute and accessible to the backend
