
# FinSight — AI Finance Operations & Invoice Intelligence Platform

FinSight is a Python-based finance operations application designed to streamline invoice processing, payment tracking, financial reconciliation, supplier analysis, and invoice risk monitoring.

## Key Features

- **Invoice Processing:** Upload PDF invoices and extract invoice information.
- **OCR Extraction:** Extract information from scanned PDF invoices.
- **Invoice Validation:** Validate extracted invoice details.
- **Duplicate Detection:** Identify potentially duplicated invoices.
- **Approval Management:** Track invoice approval workflows.
- **Payment Management:** Record payments and monitor outstanding balances.
- **Payment Reconciliation:** Compare invoice totals against recorded payments.
- **Supplier Analytics:** Monitor supplier spending and payment activity.
- **Anomaly Monitoring:** Flag unusual invoice patterns for review.
- **Finance Assistant:** Answer finance questions using stored application records.
- **CSV Exports:** Export financial and reconciliation reports.

## Technology Stack

- Python
- Streamlit
- SQLite
- Pandas
- PyMuPDF
- Tesseract OCR
- Pytesseract
- Pillow

## Project Structure

```text
AI_Finance_Intelligence/
│
├── app/
├── database/
├── data/
│   ├── sample_invoices/
│   └── processed/
├── docs/
├── models/
├── reports/
├── src/
│   ├── extraction/
│   └── validation/
├── tests/
├── .streamlit/
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

1. Clone or download the repository.
2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Install Tesseract OCR separately and configure its executable path in the application.

## Run the Application

From the project root:

```bash
streamlit run app/dashboard.py
```

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

## Database

FinSight uses SQLite to store invoice, approval, and payment information.

The local database contains development records and should not be published publicly.

## Project Purpose

This project demonstrates practical application of Python, data processing, database management, financial operations, document extraction, reporting, and business intelligence concepts.

## Disclaimer

FinSight is a portfolio and demonstration project. Financial anomaly flags are indicators for human review, not proof of fraud. Always verify financial records before making payment or approval decisions.
```

Save the file and tell me when it's done.