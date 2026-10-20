import os
import io
import sqlite3
import joblib
import base64
import numpy as np
import tensorflow as tf
import shap
import lime
import lime.lime_tabular
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
from tensorflow.keras.models import Model
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from database.database import (
    create_database,
    save_patient,
    get_all_patients
)
import socket
import qrcode
import webbrowser

app = Flask(__name__)
app.secret_key="7103"

create_database()


cnn = tf.keras.models.load_model("model/cnn_model.keras")

feature_extractor = Model(
    inputs=cnn.input,
    outputs=cnn.get_layer("FeatureLayer").output
)

svm = joblib.load("model/cnn_svm_model.pkl")
scaler = joblib.load("model/scaler.pkl")


feature_names = [
    "Previous_ICU_History", "Hypertension", "Hemoglobin", "Lactate_Level",
    "Creatinine", "Blood_Urea_Nitrogen", "Sodium", "Fever_History",
    "Urine_Output", "Mechanical_Ventilation", "Systolic_BP", "Diastolic_BP",
    "Oxygen_Saturation", "PaO2", "CRP"
]

def model_predict_pipeline(raw_inputs):
    """Pipeline required for SHAP & LIME continuous predictions."""
    raw_inputs = np.array(raw_inputs)
    if raw_inputs.ndim == 1:
        raw_inputs = raw_inputs.reshape(1, -1)
    
    scaled = scaler.transform(raw_inputs)
    cnn_in = scaled.reshape(-1, 15, 1)
    deep_feats = feature_extractor.predict(cnn_in, verbose=0)
    
    if hasattr(svm, "predict_proba"):
        return svm.predict_proba(deep_feats)
    elif hasattr(svm, "decision_function"):
        scores = svm.decision_function(deep_feats)
        
        probs = 1 / (1 + np.exp(-scores))
        return np.vstack([1 - probs, probs]).T
    else:
        preds = svm.predict(deep_feats)
        return np.vstack([1 - preds, preds]).T


background_data = np.zeros((1, len(feature_names)))
explainer_shap = shap.KernelExplainer(
    lambda x: model_predict_pipeline(x)[:, 1], 
    background_data
)


explainer_lime = lime.lime_tabular.LimeTabularExplainer(
    training_data=background_data,
    feature_names=feature_names,
    class_names=['No Sepsis', 'Sepsis Risk'],
    mode='classification'
)


def plot_to_base64():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return img_b64



@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database/sepsis.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    if user:
        conn.close()
        return "<h2>Email already registered!</h2>"

    cursor.execute("INSERT INTO users(name, email, password) VALUES(?, ?, ?)", (name, email, password))
    conn.commit()
    conn.close()

    return redirect(url_for("landing"))

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database/sepsis.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return redirect(url_for("index"))
    else:
        return "<h2>Invalid Email or Password</h2>"

@app.route("/index")
def index():
    return render_template("index.html", features=feature_names)

@app.route("/history")
def history():
    patients = get_all_patients()
    return render_template("history.html", patients=patients)

@app.route("/predict", methods=["POST"])
def predict():
    try:
        patient_name = request.form["patient_name"]
        hospital_name = request.form["hospital_name"]
        age = request.form["age"]
        gender = request.form["gender"]

        values = [float(request.form[feature]) for feature in feature_names]
        input_data = np.array([values])

        
        input_scaled = scaler.transform(input_data)
        input_cnn = input_scaled.reshape(1, 15, 1)
        deep_features = feature_extractor.predict(input_cnn, verbose=0)
        prediction = svm.predict(deep_features)[0]

        result = "High Risk of Sepsis" if prediction != 0 else "No Sepsis Detected"
        status_class = "danger" if prediction != 0 else "success"

        
        raw_shap = explainer_shap.shap_values(input_data)
        shap_vals = raw_shap[0].flatten() if isinstance(raw_shap, list) else raw_shap.flatten()

        explanation_data = []
        for name, val, s_val in zip(feature_names, values, shap_vals):
            explanation_data.append({
                'feature': name,
                'value': val,
                'shap_val': round(float(s_val), 4),
                'abs_shap': abs(float(s_val))
            })
        explanation_data.sort(key=lambda x: x['abs_shap'], reverse=True)

       
        plt.figure(figsize=(8, 5))
        y_pos = np.arange(len(feature_names))
        colors_shap = ['#d9534f' if v > 0 else '#5cb85c' for v in shap_vals]
        plt.barh(y_pos, shap_vals, color=colors_shap, align='center')
        plt.yticks(y_pos, feature_names)
        plt.xlabel("SHAP Value (Impact on Sepsis Risk)")
        plt.title("SHAP Feature Contributions")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        shap_plot_b64 = plot_to_base64()

        
        exp_lime = explainer_lime.explain_instance(
            input_data[0], 
            model_predict_pipeline, 
            num_features=10
        )
        
        fig_lime = exp_lime.as_pyplot_figure()
        plt.title("LIME Explanation (Top 10 Features)")
        plt.tight_layout()
        lime_plot_b64 = plot_to_base64()

        
        now = datetime.now()
        save_patient(
            patient_name, hospital_name, age, gender, result,
            now.strftime("%d-%m-%Y"), now.strftime("%I:%M %p"), values
        )

        return render_template(
            "result.html",
            prediction=result,
            status_class=status_class,
            patient_name=patient_name,
            explanation_data=explanation_data,
            shap_plot=shap_plot_b64,
            lime_plot=lime_plot_b64
        )

    except Exception as e:
        return f"<h2>Error processing prediction:</h2><br><pre>{e}</pre>"

@app.route("/download/<int:id>")
def download(id):
    conn = sqlite3.connect("database/sepsis.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient_history WHERE id=?", (id,))
    patient = cursor.fetchone()
    conn.close()

    if not patient:
        return "<h2>Report not found</h2>"

    pdf_name = f"Patient_{id}.pdf"
    doc = SimpleDocTemplate(pdf_name)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("<b>Sepsis Prediction Clinical Report</b>", styles["Title"]),
        Spacer(1, 15)
    ]

    patient_info = [
        [Paragraph("<b>Patient Name:</b>", styles["Normal"]), Paragraph(str(patient[1]), styles["Normal"])],
        [Paragraph("<b>Hospital:</b>", styles["Normal"]), Paragraph(str(patient[2]), styles["Normal"])],
        [Paragraph("<b>Age:</b>", styles["Normal"]), Paragraph(str(patient[3]), styles["Normal"])],
        [Paragraph("<b>Gender:</b>", styles["Normal"]), Paragraph(str(patient[4]), styles["Normal"])],
        [Paragraph("<b>Prediction Result:</b>", styles["Normal"]), Paragraph(f"<b>{patient[5]}</b>", styles["Normal"])],
        [Paragraph("<b>Date:</b>", styles["Normal"]), Paragraph(str(patient[6]), styles["Normal"])],
        [Paragraph("<b>Time:</b>", styles["Normal"]), Paragraph(str(patient[7]), styles["Normal"])]
    ]

    t = Table(patient_info, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6)
    ]))

    elements.append(t)
    doc.build(elements)

    return send_file(pdf_name, as_attachment=True)

def generate_qr():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    url = f"http://{ip_address}:7103"

    os.makedirs("qr_code", exist_ok=True)

    qr = qrcode.make(url)

    qr_path = os.path.join("qr_code", "flask_qrcode.png")
    qr.save(qr_path)

    print("Flask URL:", url)
    print("QR Code Saved:", qr_path)

    
    webbrowser.open(qr_path)
    

if __name__ == "__main__":
    generate_qr()
    app.run(host="0.0.0.0", port=7103, debug=False)
