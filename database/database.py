import sqlite3
import os

# Database Path
DB_PATH = os.path.join(os.path.dirname(__file__), "sepsis.db")


# ==========================
# Create Database
# ==========================
def create_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        patient_name TEXT,
        hospital_name TEXT,
        age INTEGER,
        gender TEXT,

        prediction TEXT,
        prediction_date TEXT,
        prediction_time TEXT,

        Previous_ICU_History INTEGER,
        Hypertension INTEGER,
        Hemoglobin REAL,
        Lactate_Level REAL,
        Creatinine REAL,
        Blood_Urea_Nitrogen REAL,
        Sodium REAL,
        Fever_History INTEGER,
        Urine_Output REAL,
        Mechanical_Ventilation INTEGER,
        Systolic_BP REAL,
        Diastolic_BP REAL,
        Oxygen_Saturation REAL,
        PaO2 REAL,
        CRP REAL

    )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL

)
""")

    conn.commit()
    conn.close()

    print("✅ Database Created Successfully")


# ==========================
# Save Patient
# ==========================
def save_patient(
    patient_name,
    hospital_name,
    age,
    gender,
    prediction,
    prediction_date,
    prediction_time,
    values
):

    print("Inside save_patient()")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(values)

    cursor.execute("""
    INSERT INTO patient_history(

        patient_name,
        hospital_name,
        age,
        gender,
        prediction,
        prediction_date,
        prediction_time,

        Previous_ICU_History,
        Hypertension,
        Hemoglobin,
        Lactate_Level,
        Creatinine,
        Blood_Urea_Nitrogen,
        Sodium,
        Fever_History,
        Urine_Output,
        Mechanical_Ventilation,
        Systolic_BP,
        Diastolic_BP,
        Oxygen_Saturation,
        PaO2,
        CRP

    )

    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, ( patient_name, hospital_name, age, gender, prediction, prediction_date, prediction_time, *values)
    )

    conn.commit()

    print("✅ Patient Data Saved Successfully")
    print("Rows inserted:", cursor.rowcount)

    conn.close()

# ==========================
# Get Patient History
# ==========================
def get_all_patients():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            patient_name,
            hospital_name,
            age,
            gender,
            prediction,
            prediction_date,
            prediction_time
        FROM patient_history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


if __name__ == "__main__":
    create_database()