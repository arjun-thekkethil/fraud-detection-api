import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler

# Load the trained model, scaler, and label encoder
clf = joblib.load("fraud_detection_xgboost.pkl")  # Updated model
scaler = joblib.load("scaler.pkl")  # Load scaler (XGBoost used scaled features)
label_encoder = joblib.load("label_encoder.pkl")  # Load label encoder

# Load new dataset
df = pd.read_csv("strong_medical_invoices.csv")

# Convert 'Date of Service' to numerical feature
df["Date of Service"] = pd.to_datetime(df["Date of Service"])
df["Days Since Service"] = (df["Date of Service"] - df["Date of Service"].min()).dt.days
df.drop(columns=["Invoice ID", "Patient Name", "Date of Service"], inplace=True)

# Encode categorical variable (consistent with training)
df["Diagnosis"] = label_encoder.transform(df["Diagnosis"])

# Define features and target
X = df.drop(columns=["Fraudulent"])
y = df["Fraudulent"]

# Split dataset (must match training process)
from sklearn.model_selection import train_test_split
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Scale test features (consistent with training)
X_test_scaled = scaler.transform(X_test)

# Make predictions
y_pred = clf.predict(X_test_scaled)
y_proba = clf.predict_proba(X_test_scaled)[:, 1]  


accuracy = accuracy_score(y_test, y_pred)
auc_roc = roc_auc_score(y_test, y_proba)

print(f"✅ Model Accuracy: {accuracy:.4f}")
print(f"✅ AUC-ROC Score: {auc_roc:.4f}")  

print("\nClassification Report:")
print(classification_report(y_test, y_pred))
