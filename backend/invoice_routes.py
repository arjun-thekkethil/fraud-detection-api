from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pandas as pd
import io

router = APIRouter()

# Dummy classification function using "Claim Amount"
def classify_invoices(df):
    if 'Claim Amount' not in df.columns:
        raise HTTPException(status_code=400, detail="CSV missing 'Claim Amount' column for classification")

    # Example rule-based classification
    return [
        "Valid" if amt > 1000 else "Fraudulent"
        for amt in df["Claim Amount"]
    ]

# JWT Bearer Authentication
bearer_scheme = HTTPBearer()

@router.post("/upload-invoice/")
async def upload_invoice(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials  # Token already validated in main.py

    contents = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a CSV file.")

    # Perform fraud detection
    classification_results = classify_invoices(df)

    return {
        "filename": file.filename,
        "message": "Invoice received successfully",
        "classification": classification_results
    }
