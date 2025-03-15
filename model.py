import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb

# Load the new strong dataset
df = pd.read_csv("strong_medical_invoices.csv")

# Convert 'Date of Service' to numeric (days since earliest date)
df["Date of Service"] = pd.to_datetime(df["Date of Service"])
df["Days Since Service"] = (df["Date of Service"] - df["Date of Service"].min()).dt.days

# Drop unnecessary columns
df.drop(columns=["Invoice ID", "Patient Name", "Date of Service"], inplace=True)

# Encode categorical features
label_encoder = LabelEncoder()
df["Diagnosis"] = label_encoder.fit_transform(df["Diagnosis"])

# Define features and target
X = df.drop(columns=["Fraudulent"])
y = df["Fraudulent"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Apply SMOTE only if fraud cases are underrepresented
if y_train.value_counts()[1] < 100:  # If fewer than 100 fraud cases, apply SMOTE
    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)

# Standardize numeric features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train XGBoost Model
clf = xgb.XGBClassifier(
    n_estimators=300,  # Reduce from 500 to prevent overfitting
    max_depth=5,  # Reduce for better generalization
    learning_rate=0.05,  # Higher learning rate for better performance
    scale_pos_weight=(y_train.value_counts()[0] / y_train.value_counts()[1]),  # Dynamic fraud balancing
    colsample_bytree=0.8,
    subsample=0.8,
    random_state=42
)
clf.fit(X_train_scaled, y_train)

# Predictions
y_pred = clf.predict(X_test_scaled)
y_proba = clf.predict_proba(X_test_scaled)[:, 1]

# Evaluation
print("\n✅ Optimized Model Trained Successfully!")
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("AUC-ROC Score:", roc_auc_score(y_test, y_proba))

# Save model and preprocessing tools
joblib.dump(clf, "fraud_detection_xgboost.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")

print("\n✅ Model saved as fraud_detection_xgboost.pkl")
