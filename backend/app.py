from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
CORS(app)

# ================= DATABASE =================

try:
    db = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

    cursor = db.cursor()

except Exception as e:
    print("Database Connection Error:", e)


# ================= LOAD DATASET =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

data = pd.read_csv(os.path.join(BASE_DIR, "dataset/dataset.csv"))

# clean column names
data.columns = data.columns.str.strip()

# fix LandSize column
if "Land Size" in data.columns:
    data.rename(columns={"Land Size": "LandSize"}, inplace=True)


# ================= SIGNUP =================

@app.route('/signup', methods=['POST'])
def signup():

    try:
        data_req = request.json

        name = data_req.get('name')
        phone = data_req.get('phone')
        email = data_req.get('email')
        gender = data_req.get('gender')
        city = data_req.get('city')

        password = generate_password_hash(data_req.get('password'))

        sql = """INSERT INTO users
        (name, phone, email, gender, city, password)
        VALUES (%s,%s,%s,%s,%s,%s)"""

        values = (name, phone, email, gender, city, password)

        cursor.execute(sql, values)
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Account created successfully"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })


# ================= LOGIN =================

@app.route('/login', methods=['POST'])
def login():

    try:
        data_req = request.json

        email = data_req.get("email")
        password = data_req.get("password")

        cursor.execute(
            "SELECT id,password,name FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):

            return jsonify({
                "status": "success",
                "user_id": user[0],
                "name": user[2],
                "message": "Login success"
            })

        return jsonify({
            "status": "error",
            "message": "Invalid credentials"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })


# ================= CROP RECOMMENDATION =================

@app.route("/crop-recommendation", methods=["POST"])
def predict_crop():

    try:
        data_req = request.json

        climate = str(data_req.get("climate")).lower()
        soil = str(data_req.get("soil_type")).lower()
        water = str(data_req.get("water_level")).lower()
        land = float(data_req.get("land_size", 0))

        # ================= FILTER DATASET =================

        filtered = data[
            (data["Climate"].str.lower() == climate) &
            (data["SoilType"].str.lower() == soil) &
            (data["WaterLevel"].str.lower() == water)
        ]

        if filtered.empty:
            return jsonify({
                "status": "fail",
                "message": "No crops found for selected conditions"
            })

        # ================= NEAREST LAND SIZE =================

        filtered = filtered.copy()

        filtered["diff"] = abs(filtered["LandSize"] - land)

        filtered = filtered.sort_values("diff")

        # remove duplicate plants
        filtered = filtered.drop_duplicates(subset=["PlantName"])

        # ================= CREATE RESULTS =================

        results = []

        for _, row in filtered.iterrows():

            results.append({
                "plant_name": row["PlantName"],
                "fertilizer_name": row["FertilizerName"],
                "disease_name": row["DiseasesName"],
                "medicine_name": row["MedicineName"]
            })

        return jsonify({
            "status": "success",
            "recommendations": results
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })


# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
