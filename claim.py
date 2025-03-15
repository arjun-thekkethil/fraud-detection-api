import joblib
import pandas as pd

# Load trained model and label encoder
model = joblib.load("fraud_detection_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Test a known fraudulent case from your dataset
sample_claim = 2368.61  # Example fraudulent claim amount
sample_diagnosis = "Hypertension"  # Example fraudulent diagnosis

# Convert diagnosis to encoded form
diagnosis_encoded = label_encoder.transform([sample_diagnosis])[0]

# Predict fraud status
prediction = model.predict([[sample_claim, diagnosis_encoded]])[0]

# Print results
print(f"Claim Amount: {sample_claim}, Diagnosis: {sample_diagnosis}")
print(f"Model Output: {'Fraudulent' if prediction == 1 else 'Valid'}")
