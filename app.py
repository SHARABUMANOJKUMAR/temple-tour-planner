# -------------------------
# Imports
# -------------------------
from flask import Flask, render_template, request, jsonify, redirect, url_for
import pyodbc
import config
import requests  # For LibreTranslate API

# -------------------------
# Initialize Flask App
# -------------------------
app = Flask(__name__)

# -------------------------
# Function: DB Connection String
# -------------------------
def get_connection():
    conn_str = (
        f"DRIVER={{{config.DB_CONFIG['driver']}}};"
        f"SERVER={config.DB_CONFIG['server']};"
        f"DATABASE={config.DB_CONFIG['database']};"
        f"Trusted_Connection={config.DB_CONFIG['trusted_connection']};"
    )
    return pyodbc.connect(conn_str)

# -------------------------
# Function: Save User to Database
# -------------------------
def save_to_db(name, age, location, preference):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO UserPlans (name, age, location, preference)
        VALUES (?, ?, ?, ?)
    """
    cursor.execute(query, (name, age, location, preference))
    conn.commit()
    conn.close()

# -------------------------
# Function: Generate Temple Recommendation
# -------------------------
def generate_recommendation(preference):
    recommendations = {
        'spiritual': ("Visit the Tirumala Temple in Tirupati... Early morning darshan is best.",
                      "https://upload.wikimedia.org/wikipedia/commons/2/2e/Tirumala_Venkateswara_Temple_Gopuram.jpg"),
        'historical': ("Explore the Kailasa Temple in Ellora Caves... Carry water and sun cap.",
                       "https://upload.wikimedia.org/wikipedia/commons/e/e6/Kailasanatha_Temple%2C_Ellora.jpg"),
        'peaceful': ("Visit the Golden Temple in Amritsar... Peaceful environment, carry ID.",
                     "https://upload.wikimedia.org/wikipedia/commons/8/84/Golden_Temple%2C_Amritsar.jpg"),
        'adventure': ("Plan a trip to Kedarnath... Light luggage, check weather forecast.",
                      "https://upload.wikimedia.org/wikipedia/commons/3/37/Kedarnath_Temple_2016.jpg"),
        'coastal': ("Enjoy Srikalahasti Temple by the river... Carry cotton clothes and umbrella.",
                    "https://upload.wikimedia.org/wikipedia/commons/f/f3/Srikalahasti_Temple.jpg"),
        'south indian': ("Visit Meenakshi Temple in Madurai... Best experienced during festivals.",
                         "https://upload.wikimedia.org/wikipedia/commons/6/6b/Meenakshi_Temple_1.jpg"),
    }
    return recommendations.get(preference, (
        "Visit local peaceful temples... Easy and close to home.",
        "https://upload.wikimedia.org/wikipedia/commons/9/9f/Indian_temple_example.jpg"
    ))

# -------------------------
# Route: Home Page
# -------------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------------
# Route: Search Temple Plans
# -------------------------
@app.route('/search')
def search():
    conn = get_connection()
    cursor = conn.cursor()
    query = request.args.get('q')

    if query:
        cursor.execute("""
            SELECT * FROM UserPlans 
            WHERE name LIKE ? OR location LIKE ? OR preference LIKE ?
        """, ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
    else:
        cursor.execute("SELECT * FROM UserPlans")

    data = cursor.fetchall()
    conn.close()
    return render_template('index.html', data=data)

# -------------------------
# Route: Recommendation Result
# -------------------------
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        name = request.form['name']
        age = int(request.form['age'])
        location = request.form['location'].strip().lower()
        preference = request.form['preference'].strip().lower()

        if preference == 'historical':
            temple = "Brihadeeswara Temple, Tamil Nadu"
            darshan = "6 AM - 12 PM, 4 PM - 8 PM"
            tips = "Wear comfortable footwear, carry water, avoid midday heat"
        elif preference == 'spiritual':
            temple = "Kedarnath Temple, Uttarakhand"
            darshan = "4 AM - 9 PM"
            tips = "Senior-friendly facilities available, avoid during snow"
        elif preference == 'peaceful':
            temple = "Lotus Temple, Delhi"
            darshan = "9 AM - 5 PM"
            tips = "Wheelchair accessible, clean restrooms available"
        elif preference == 'south indian':
            temple = "Meenakshi Temple, Madurai"
            darshan = "5 AM - 10 PM"
            tips = "Best experienced during festivals, wear comfortable clothes"
        else:
            temple = "Vaishno Devi, Jammu"
            darshan = "24x7"
            tips = "Trekking involved, helicopter options for seniors"

        recommendation = f"""
Hello {name} 👋, here is a recommended temple tour plan based on your preference:

🛕 Temple: {temple}
📍 Based on your interest in {preference} temples.
⏰ Darshan Timings: {darshan}
❤️ Safety Tips: {tips}

Have a peaceful and safe journey!
"""

        save_to_db(name, age, location, preference)
        temple_info, image_url = generate_recommendation(preference)

        return render_template("result.html", recommendation=recommendation + "\n\n" + temple_info, image_url=image_url)

    except Exception as e:
        return f"Error processing request: {e}", 500

# -------------------------
# Route: View All Users (Admin Panel)
# -------------------------
@app.route('/all-users')
def all_users():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)
    except ValueError:
        page, per_page = 1, 10

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM UserPlans")
    total_count = cursor.fetchone()[0]
    total_pages = (total_count + per_page - 1) // per_page
    offset = (page - 1) * per_page

    query = """
    SELECT id, name, age, location, preference, created_at
    FROM UserPlans
    ORDER BY created_at DESC
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    cursor.execute(query, (offset, per_page))
    rows = cursor.fetchall()
    conn.close()

    return render_template(
        'all_users.html',
        users=rows,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_count=total_count
    )

# -------------------------
# Route: Translate Using LibreTranslate API
# -------------------------
@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        lang = data.get('lang', 'en')

        if not text or not lang:
            return jsonify({'error': 'Missing text or language'}), 400

        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": "en",
            "target": lang,
            "format": "text"
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        translated_text = response.json().get('translatedText')

        return jsonify({'translation': translated_text})
    except Exception as e:
        return jsonify({'error': 'Translation failed', 'details': str(e)}), 500

# -------------------------
# Route: View Individual User
# -------------------------
@app.route('/user/<int:user_id>')
def user_detail(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM UserPlans WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return render_template('user_detail.html', user=user)
    else:
        return "User not found", 404

# -------------------------
# Route: Edit User Info
# -------------------------
@app.route('/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        location = request.form['location']
        preference = request.form['preference'].strip().lower()

        cursor.execute("""
            UPDATE UserPlans
            SET name = ?, age = ?, location = ?, preference = ?
            WHERE id = ?
        """, (name, age, location, preference, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('user_detail', user_id=user_id))

    cursor.execute("SELECT * FROM UserPlans WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    return render_template('edit_user.html', user=user)

# -------------------------
# Run Flask Server
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
