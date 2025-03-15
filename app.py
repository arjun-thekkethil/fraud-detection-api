import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
import pdfplumber
import pandas as pd
import os
import joblib
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, Invoice  # Import database connection

app = FastAPI()

# Load trained fraud detection model and preprocessors
model = joblib.load("fraud_detection_xgboost.pkl")  # Updated model
label_encoder = joblib.load("label_encoder.pkl")  # Updated label encoder
scaler = joblib.load("scaler.pkl")  # Load scaler for feature scaling

# Ensure upload directory exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to classify an invoice as "Valid" or "Fraudulent"
def classify_invoice(claim_amount, diagnosis, claim_frequency, high_claim, suspicious_diagnosis, days_since_service):
    try:
        # Encode Diagnosis (Handle unknown diagnoses safely)
        if diagnosis in label_encoder.classes_:
            diagnosis_encoded = label_encoder.transform([diagnosis])[0]
        else:
            print(f"⚠️ Warning: Unknown diagnosis '{diagnosis}', assigning safe default.")
            diagnosis_encoded = label_encoder.transform(["Flu"])[0]  # Assign a known label

        # Prepare input features
        input_features = [[claim_amount, diagnosis_encoded, claim_frequency, high_claim, suspicious_diagnosis, days_since_service]]

        # Debugging: Print the input features before prediction
        print(f"📌 Features Before Scaling: {input_features}")

        input_scaled = scaler.transform(input_features)

        # Predict using trained model
        prediction = model.predict(input_scaled)[0]

        return "Valid" if prediction == 0 else "Fraudulent"

    except Exception as e:
        print(f"❌ Prediction Error: {str(e)}")
        return "Prediction Failed - Check API Logs"

# Extract text from PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
    return text.strip() if text else "No text extracted"

# Process CSV file with dynamic feature handling
def process_csv(file_path):
    df = pd.read_csv(file_path)

    # Check for required columns
    required_cols = {"Claim Amount", "Diagnosis", "Date of Service"}
    missing_cols = required_cols - set(df.columns)
    
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_cols}")

    # Convert 'Date of Service' to numerical feature
    df["Date of Service"] = pd.to_datetime(df["Date of Service"])
    df["Days Since Service"] = (df["Date of Service"] - df["Date of Service"].min()).dt.days

    # Generate missing feature columns
    df["Claim Frequency"] = df.get("Claim Frequency", 1)  # Default to 1 if missing
    df["High Claim"] = (df["Claim Amount"] > df["Claim Amount"].quantile(0.95)).astype(int)
    df["Suspicious Diagnosis"] = df["Diagnosis"].apply(lambda x: 1 if x in ["Surgery", "Cancer Treatment"] else 0)

    # Drop unnecessary columns before prediction
    df = df[["Claim Amount", "Diagnosis", "Claim Frequency", "High Claim", "Suspicious Diagnosis", "Days Since Service"]]

    # Classify each invoice
    df["Fraud_Status"] = df.apply(lambda row: classify_invoice(
        row["Claim Amount"], row["Diagnosis"], row["Claim Frequency"], row["High Claim"], row["Suspicious Diagnosis"], row["Days Since Service"]
    ), axis=1)

    return df.to_dict(orient="records")

# API Endpoint: Upload invoice (CSV/PDF)
@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save file locally
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    extracted_data = {}

    # Process based on file type
    if file.filename.endswith(".pdf"):
        extracted_data["text"] = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".csv"):
        extracted_data["data"] = process_csv(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Upload a CSV or PDF.")

    # Store in PostgreSQL database
    invoice = Invoice(filename=file.filename, extracted_data=json.dumps(extracted_data))
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return {"invoice_id": invoice.id, "filename": file.filename, "extracted_data": extracted_data}

# API Endpoint: Retrieve invoice results
@app.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    extracted_data = json.loads(invoice.extracted_data)
    return {"invoice_id": invoice.id, "filename": invoice.filename, "extracted_data": extracted_data}

# Run FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
