import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

# =============================
# Load Dataset
# =============================
data = pd.read_csv("dataset/dataset.csv")

# Clean column names
data.columns = data.columns.str.strip()

# Fix column naming issues
if "Land Size" in data.columns:
    data.rename(columns={"Land Size": "LandSize"}, inplace=True)

# =============================
# Define Columns
# =============================
categorical_cols = [
    "Climate",
    "SoilType",
    "WaterLevel",
    "PlantName",
    "FertilizerName",
    "DiseasesName",
    "MedicineName"
]

# =============================
# Encoding
# =============================
encoders = {}

for col in categorical_cols:
    if col in data.columns:
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col].astype(str))
        encoders[col] = le
    else:
        print(f"⚠ Warning: {col} not found in dataset")

# =============================
# Features + Target
# =============================
# Make sure LandSize exists
if "LandSize" not in data.columns:
    raise Exception("❌ LandSize column missing in dataset")

X = data[["Climate", "SoilType", "WaterLevel", "LandSize"]]

# Target = Plant prediction
y = data["PlantName"]

# =============================
# Train Test Split
# =============================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# =============================
# Model Training
# =============================
model = RandomForestClassifier(
    n_estimators=25,
    max_depth=8,
    random_state=42
)

model.fit(X_train, y_train)

# =============================
# Save Model + Encoders
# =============================
os.makedirs("model", exist_ok=True)

pickle.dump(model, open("model/crop_model.pkl", "wb"))
pickle.dump(encoders, open("model/encoders.pkl", "wb"))

print("✅ Training Completed Successfully")