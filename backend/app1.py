from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, UploadFile, File
import joblib
import json
import os
import pdfplumber
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, Invoice
from main import oauth2_scheme  # Import oauth2_scheme for token authentication

# Load fraud detection model, scaler, and label encoder
model = joblib.load("fraud_detection_xgboost.pkl")
label_encoder = joblib.load("label_encoder.pkl")
scaler = joblib.load("scaler.pkl")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to classify invoices
def classify_invoice(claim_amount, diagnosis, claim_frequency, high_claim, suspicious_diagnosis, days_since_service):
    try:
        if diagnosis in label_encoder.classes_:
            diagnosis_encoded = label_encoder.transform([diagnosis])[0]
        else:
            diagnosis_encoded = label_encoder.transform(["Flu"])[0]  # Default to "Flu"
        
        input_features = [[claim_amount, diagnosis_encoded, claim_frequency, high_claim, suspicious_diagnosis, days_since_service]]
        input_scaled = scaler.transform(input_features)
        prediction = model.predict(input_scaled)[0]

        return "Valid" if prediction == 0 else "Fraudulent"
    except Exception as e:
        print(f"❌ Prediction Error: {str(e)}")
        return "Prediction Failed - Check API Logs"

# Function to process CSV file
def process_csv(file_path):
    df = pd.read_csv(file_path)
    required_cols = {"Claim Amount", "Diagnosis", "Date of Service"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_cols}")

    df["Date of Service"] = pd.to_datetime(df["Date of Service"])
    df["Days Since Service"] = (df["Date of Service"] - df["Date of Service"].min()).dt.days
    df["Claim Frequency"] = df.get("Claim Frequency", 1)  # Default to 1 if missing
    df["High Claim"] = (df["Claim Amount"] > df["Claim Amount"].quantile(0.95)).astype(int)
    df["Suspicious Diagnosis"] = df["Diagnosis"].apply(lambda x: 1 if x in ["Surgery", "Cancer Treatment"] else 0)
    
    df["Fraud_Status"] = df.apply(lambda row: classify_invoice(
        row["Claim Amount"], row["Diagnosis"], row["Claim Frequency"], row["High Claim"], row["Suspicious Diagnosis"], row["Days Since Service"]
    ), axis=1)

    return df.to_dict(orient="records")

# Route to handle file uploads with fraud detection
@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save uploaded file to server
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Extract data based on file type (PDF or CSV)
    extracted_data = {}
    if file.filename.endswith(".pdf"):
        extracted_data["text"] = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".csv"):
        extracted_data["data"] = process_csv(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Upload a CSV or PDF.")
    
    # Save the invoice and extracted data to database
    invoice = Invoice(filename=file.filename, extracted_data=json.dumps(extracted_data))
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return {"invoice_id": invoice.id, "filename": file.filename, "extracted_data": extracted_data}

# Additional route to view uploaded claims
@app.get("/claims")
async def get_all_claims(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    claims = db.query(Invoice).all()  # Fetch all claims from the database
    return [{"id": claim.id, "patient_name": claim.extracted_data.get("patient_name"), "amount": claim.extracted_data.get("amount"), "status": claim.extracted_data.get("status")} for claim in claims]

