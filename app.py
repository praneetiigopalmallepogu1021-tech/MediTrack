from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv
import pymysql
import os
from datetime import date

load_dotenv()

app = Flask(__name__)

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------------- DASHBOARD ----------------
@app.route("/")
def home():

    conn = get_connection()
    cursor = conn.cursor()

    # all equipment
    cursor.execute("SELECT * FROM equipment")
    equipment = cursor.fetchall()

    # counts
    cursor.execute("SELECT COUNT(*) as total FROM equipment")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as active FROM equipment WHERE status='Active'")
    active = cursor.fetchone()["active"]

    cursor.execute("SELECT COUNT(*) as maintenance FROM equipment WHERE status='Under Maintenance'")
    maintenance = cursor.fetchone()["maintenance"]

    # overdue maintenance
    cursor.execute("""
        SELECT e.*
        FROM equipment e
        JOIN maintenance_log m ON e.equipment_id = m.equipment_id
        WHERE m.next_due_date < CURDATE()
    """)
    overdue = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        equipment=equipment,
        total=total,
        active=active,
        maintenance=maintenance,
        overdue=overdue
    )

# ---------------- ADD EQUIPMENT ----------------
@app.route("/add_equipment", methods=["GET", "POST"])
def add_equipment():

    if request.method == "POST":

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO equipment
            (equipment_name, serial_number, department, purchase_date, status)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            request.form["equipment_name"],
            request.form["serial_number"],
            request.form["department"],
            request.form["purchase_date"],
            request.form["status"]
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_equipment.html")


# ---------------- ADD MAINTENANCE ----------------
@app.route("/add_log/<int:eid>", methods=["GET", "POST"])
def add_log(eid):

    if request.method == "POST":

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO maintenance_log
            (equipment_id, maintenance_date, technician_name, issue_reported, resolution_notes, next_due_date)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            eid,
            request.form["maintenance_date"],
            request.form["technician_name"],
            request.form["issue_reported"],
            request.form["resolution_notes"],
            request.form["next_due_date"]
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_log.html", eid=eid)


# ---------------- HISTORY ----------------
@app.route("/history/<int:eid>")
def history(eid):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM maintenance_log
        WHERE equipment_id=%s
        ORDER BY maintenance_date DESC
    """, (eid,))

    logs = cursor.fetchall()

    conn.close()

    return render_template("history.html", logs=logs, eid=eid)


# ---------------- STATUS UPDATE ----------------
@app.route("/update_status/<int:eid>", methods=["POST"])
def update_status(eid):

    new_status = request.form["status"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE equipment
        SET status=%s
        WHERE equipment_id=%s
    """, (new_status, eid))

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
