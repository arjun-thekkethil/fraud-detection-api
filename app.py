import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
import pdfplumber
import pandas as pd
import os
import joblib
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, Invoice 

app = FastAPI()


model = joblib.load("fraud_detection_xgboost.pkl")  
label_encoder = joblib.load("label_encoder.pkl")  
scaler = joblib.load("scaler.pkl")  


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def classify_invoice(claim_amount, diagnosis, claim_frequency, high_claim, suspicious_diagnosis, days_since_service):
    try:
       
        if diagnosis in label_encoder.classes_:
            diagnosis_encoded = label_encoder.transform([diagnosis])[0]
        else:
            print(f"⚠️ Warning: Unknown diagnosis '{diagnosis}', assigning safe default.")
            diagnosis_encoded = label_encoder.transform(["Flu"])[0]  # Assign a known label

        
        input_features = [[claim_amount, diagnosis_encoded, claim_frequency, high_claim, suspicious_diagnosis, days_since_service]]

        
        print(f"📌 Features Before Scaling: {input_features}")

        input_scaled = scaler.transform(input_features)

        
        prediction = model.predict(input_scaled)[0]

        return "Valid" if prediction == 0 else "Fraudulent"

    except Exception as e:
        print(f"❌ Prediction Error: {str(e)}")
        return "Prediction Failed - Check API Logs"


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
    return text.strip() if text else "No text extracted"

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

   
    df = df[["Claim Amount", "Diagnosis", "Claim Frequency", "High Claim", "Suspicious Diagnosis", "Days Since Service"]]

    df["Fraud_Status"] = df.apply(lambda row: classify_invoice(
        row["Claim Amount"], row["Diagnosis"], row["Claim Frequency"], row["High Claim"], row["Suspicious Diagnosis"], row["Days Since Service"]
    ), axis=1)

    return df.to_dict(orient="records")


@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

   
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    extracted_data = {}

   
    if file.filename.endswith(".pdf"):
        extracted_data["text"] = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".csv"):
        extracted_data["data"] = process_csv(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Upload a CSV or PDF.")


    invoice = Invoice(filename=file.filename, extracted_data=json.dumps(extracted_data))
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return {"invoice_id": invoice.id, "filename": file.filename, "extracted_data": extracted_data}


@app.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    extracted_data = json.loads(invoice.extracted_data)
    return {"invoice_id": invoice.id, "filename": invoice.filename, "extracted_data": extracted_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
