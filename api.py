from flask import Flask, request, jsonify, send_from_directory
import os
import csv
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import re

app = Flask(__name__)

# Define a regular expression pattern for a valid email address
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

def validate_email(email):
    return re.match(EMAIL_REGEX, email)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')

        if not (first_name and last_name and email and password):
            return jsonify({"message": "All fields are required."}), 400

        if not validate_email(email):
            return jsonify({"message": "Invalid email format."}), 400

        connection = mysql.connector.connect(
            host='localhost',
            database='product',  # Your database name
            user='your_username',
            password='your_password'
        )

        cursor = connection.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "Email is already registered."}), 400

        hashed_password = generate_password_hash(password)
        query = "INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)"
        values = (first_name, last_name, email, hashed_password)
        cursor.execute(query, values)

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "Registration successful!"}), 201

    except Error as e:
        print("Error:", e)
        return jsonify({"message": "Registration failed."}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not (email and password):
            return jsonify({"message": "Email and password are required."}), 400

        connection = mysql.connector.connect(
            host='localhost',
            database='product',  # Your database name
            user='your_username',
            password='your_password'
        )

        cursor = connection.cursor()

        cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            token = jwt.encode({'user_id': user[0]}, 'your_secret_key', algorithm='HS256')
            return jsonify({'token': token}), 200
        else:
            return jsonify({"message": "Invalid credentials."}), 401

        cursor.close()
        connection.close()

    except Error as e:
        print("Error:", e)
        return jsonify({"message": "Login failed."}), 500

# ... (Import statements and other code above)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Authorization token is missing."}), 401

        try:
            decoded_token = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token."}), 401

        # Check if the user is authorized (e.g., admin)
        # ... Implement your authorization logic ...

        if 'file' not in request.files:
            return jsonify({"message": "No file part."}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"message": "No selected file."}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Process the uploaded CSV file
            with open(file_path, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    try:
                        connection = mysql.connector.connect(
                            host='localhost',
                            database='product',  # Your database name
                            user='root',
                            password='sreeja1661'
                        )
                        cursor = connection.cursor()

                        query = "INSERT INTO products (name, barcode, brand, description, price, available) VALUES (%s, %s, %s, %s, %s, %s)"
                        values = (
                            row['name'],
                            row['barcode'],
                            row['brand'],
                            row['description'],
                            row['price'],
                            row['available']
                        )
                        cursor.execute(query, values)
                        connection.commit()
                        cursor.close()
                        connection.close()

                    except Error as e:
                        print("Error:", e)
                        # Handle the database insertion error as needed

            return jsonify({"message": "File uploaded and processed successfully."}), 201

    except Error as e:
        print("Error:", e)
        return jsonify({"message": "File upload failed."}), 500

# ... (Remaining code for review submission and product retrieval)


@app.route('/api/review', methods=['POST'])
def submit_review():
    try:
        data = request.json
        token = data.get('token')
        product_id = data.get('product_id')
        rating = data.get('rating')
        review_text = data.get('review_text')

        if not (token and product_id and rating and review_text):
            return jsonify({"message": "All fields are required."}), 400

        try:
            decoded_token = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token."}), 401

        connection = mysql.connector.connect(
            host='localhost',
            database="product",
            user='root',
            password='sreeja1661'
        )

        cursor = connection.cursor()

        query = "INSERT INTO product_reviews (user_id, product_id, rating, review_text) VALUES (%s, %s, %s, %s)"
        values = (decoded_token['user_id'], product_id, rating,        review_text)
        cursor.execute(query, values)

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "Review submitted successfully!"}), 201

    except Error as e:
        print("Error:", e)
        return jsonify({"message": "Review submission failed."}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        sort_by = request.args.get('sort_by', 'review')

        connection = mysql.connector.connect(
            host='localhost',
            database='product',  # Your database name
            user='your_username',
            password='your_password'
        )

        cursor = connection.cursor()

        offset = (page - 1) * per_page

        if sort_by == 'review':
            order_by = 'ORDER BY average_rating DESC'
        else:
            order_by = ''  # Add sorting logic for other criteria if needed

        query = f"SELECT p.*, AVG(pr.rating) AS average_rating FROM products p LEFT JOIN product_reviews pr ON p.id = pr.product_id GROUP BY p.id {order_by} LIMIT %s OFFSET %s"
        values = (per_page, offset)
        cursor.execute(query, values)
        products = cursor.fetchall()

        connection.commit()
        cursor.close()
        connection.close()

        product_list = []
        for product in products:
            product_data = {
                'id': product[0],
                'name': product[1],
                'barcode': product[2],
                'brand': product[3],
                'description': product[4],
                'price': product[5],
                'available': product[6],
                'average_rating': float(product[7]) if product[7] else None
            }
            product_list.append(product_data)

        return jsonify(product_list), 200

    except Error as e:
        print("Error:", e)
        return jsonify({"message": "Error fetching products."}), 500
    # ... Other route handlers ...

@app.route('/')
def root():
    return "Welcome to the API"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)

