# Import necessary modules
import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, flash, send_file, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import relationship
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, create_access_token
from flask_bcrypt import Bcrypt
from flask import abort


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.sqlite3'
app.config['SECRET_KEY'] = "random string"
# JWT configuration
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)  # Set the expiration time for token
app.config["JWT_ALGORITHM"] = "HS256"  # Set the algorithm
jwt = JWTManager(app)    # Initialize JWT 
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)


# Define the root route to serve the frontend
@app.route('/')
def index():
    frontend_folder = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_file(os.path.join(frontend_folder, 'index.html'))


# Books model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    year_published = db.Column(db.Integer, nullable=False)
    book_type = db.Column(db.Integer, CheckConstraint('book_type IN (1, 2, 3)'))
    image_url = db.Column(db.String(255), default='book.jpg')  # Add a default value for the image URL
    loans = relationship('Loan', backref='related_book', lazy=True, overlaps="loans,related_book")
    
    def __init__(self, name, author, year_published, book_type, image_url=None):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.book_type = book_type
        self.image_url = image_url or 'book.jpg'  # Set default value if image_url is not provided

# Define routes for managing books

@app.route('/books', methods=['GET', 'POST', 'OPTIONS'])
def books():
    if request.method == 'GET':
        books = Book.query.all()
        book_list = [{"id": book.id, "name": book.name, "author": book.author, "year_published": book.year_published, "book_type": book.book_type} for book in books]
        return jsonify(book_list), 200, {'Content-Type': 'application/json'}

    elif request.method == 'POST':
        request_data = request.get_json()
        name = request_data['name']
        author = request_data["author"]
        year_published = request_data["year_published"]
        book_type = request_data["book_type"]

        new_book = Book(name=name, author=author, year_published=year_published, book_type=book_type)
        db.session.add(new_book)
        db.session.commit()
        return "A new book was created", 200

    elif request.method == 'OPTIONS':
        # Handling preflight requests
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, DELETE, PUT',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

# Define route for deleting a book

@app.route('/books/del/<int:id>', methods=['DELETE', 'OPTIONS'])
def delete_book(id):
    if request.method == 'OPTIONS':
        # Handling preflight requests
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    del_book = Book.query.get(id)
    if del_book:
        db.session.delete(del_book)
        db.session.commit()
        return "A book was deleted", 200
    return "No such book....", 404

# Define route for updating a book

@app.route('/books/upd/<int:id>', methods=['PUT', 'OPTIONS'])
def update_book(id):
    if request.method == 'OPTIONS':
        # Handling preflight requests
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, DELETE, PUT',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    request_data = request.get_json()
    upd_book = Book.query.get(id)
    if upd_book:
        upd_book.name = request_data['name']
        upd_book.author = request_data["author"]
        upd_book.year_published = request_data["year_published"]
        upd_book.book_type = request_data["book_type"]
        db.session.commit()
        return "A book was updated", 200, {'Content-Type': 'application/json'}
    return "No such book....", 404, {'Content-Type': 'application/json'}

# Define route for searhing a book

@app.route('/books/search', methods=['POST'])
def search_books():
    search_term = request.get_json().get('search_term', '')

    # Perform a case-insensitive search on book names
    books = Book.query.filter(Book.name.ilike(f"%{search_term}%")).all()

    book_list = [
        {"id": book.id, "name": book.name, "author": book.author, "year_published": book.year_published,
         "book_type": book.book_type} for book in books
    ]

    return jsonify(book_list), 200, {'Content-Type': 'application/json'}

    
# Customers model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    loans = relationship('Loan', backref='related_customer', lazy=True, overlaps="loans,related_customer")
    
    def __init__(self, name, city, age):
        self.name = name
        self.city = city
        self.age = age

# Routes for Customer operations
@app.route('/customers')
def show_all_customers():
    customers = Customer.query.all()
    customer_list = [{"id": customer.id, "name": customer.name, "city": customer.city, "age": customer.age} for customer in customers]
    return jsonify(customer_list)

# Routes for adding a new  Customer 

@app.route('/customers/new', methods=['POST'])
def new_customer():
    request_data = request.get_json()
    name = request_data['name']
    city = request_data["city"]
    age = request_data["age"]

    new_customer = Customer(name=name, city=city, age=age)
    db.session.add(new_customer)
    db.session.commit()
    return "A new customer was created"

# Routes for deleting  Customer 

@app.route('/customers/del/<int:id>', methods=['DELETE'])
def delete_customer(id):
    del_customer = Customer.query.get(id)
    if del_customer:
        db.session.delete(del_customer)
        db.session.commit()
        return "A customer was deleted"
    return "No such customer...."

# Routes for updating  Customer

@app.route('/customers/upd/<int:id>', methods=['PUT'])
def update_customer(id):
    request_data = request.get_json()
    upd_customer = Customer.query.get(id)
    if upd_customer:
        upd_customer.name = request_data['name']
        upd_customer.city = request_data["city"]
        upd_customer.age = request_data["age"]
        db.session.commit()
        return "A customer was updated"
    return "No such customer...."

@app.route('/customers/search', methods=['POST'])
def search_customers():
    search_term = request.get_json().get('search_term', '')

    # Perform a case-insensitive search on customer names
    customers = Customer.query.filter(Customer.name.ilike(f"%{search_term}%")).all()

    customer_list = [
        {"id": customer.id, "name": customer.name, "city": customer.city, "age": customer.age} for customer in customers
    ]

    return jsonify(customer_list), 200, {'Content-Type': 'application/json'}

    

# Loan model
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    loan_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    is_late = db.Column(db.Boolean, default=False)  # New column
    loan_status = db.Column(db.String, default='Not returned')  # New column
    customer = relationship('Customer', backref='related_loans', overlaps="loans,related_customer")
    book = relationship('Book', backref='related_loans', overlaps="loans,related_book")

    def display_return_date(self):
        return self.return_date.strftime('%Y-%m-%d') if self.return_date else 'Not returned'

    def calculate_fine(self):
        if self.return_date and self.loan_status != 'Returned':
            current_date = datetime.now().date()
            if current_date > self.return_date:
                days_late = (current_date - self.return_date).days
                fine_rate_per_day = 0.5
                fine_amount = days_late * fine_rate_per_day
                return fine_amount
        return 0

    def __init__(self, cust_id, book_id, loan_date, return_date=None):
        self.cust_id = cust_id
        self.book_id = book_id
        self.loan_date = loan_date
        self.return_date = return_date
        self.is_late = self.return_date and self.return_date < datetime.now().date()
        self.update_loan_status()

    def update_loan_status(self):
        # Update the loan status based on the return date
        if self.return_date:
            self.loan_status = 'Returned'
        elif self.is_late:
            self.loan_status = 'Late'
        else:
            self.loan_status = 'Not returned'

    def update_late_status(self):
        # Update the is_late status based on the current date
        self.is_late = self.return_date and self.return_date < datetime.now().date()
        self.update_loan_status()

      
   # diplay loans    
        
@app.route('/loans', methods=['GET'])
def show_all_loans():
    loans = Loan.query.all()
    loans_data = []
    for loan in loans:
        loan.update_late_status()  # Update late status before displaying
        loans_data.append({
            'id': loan.id,
            'cust_id': loan.cust_id,
            'book_id': loan.book_id,
            'loan_date': loan.loan_date.strftime('%Y-%m-%d'),
            'return_date': loan.display_return_date(),
            'late': loan.is_late,
        })
    return jsonify(loans_data)

# route for creating new loan 

@app.route('/loans/new', methods=['POST'])
def new_loan():
    request_data = request.get_json()
    cust_id = request_data['cust_id']
    book_id = request_data["book_id"]
    loan_date_str = request_data["loan_date"]

    # Check if the book exists
    book = Book.query.get(book_id)
    if not book:
        return "Book not found", 404

    # Convert string representations to Python date objects
    loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()

    # Calculate return date based on book type
    if book.book_type == 1:
        return_date = loan_date + timedelta(days=10)
    elif book.book_type == 2:
        return_date = loan_date + timedelta(days=5)
    elif book.book_type == 3:
        return_date = loan_date + timedelta(days=2)
    else:
        return jsonify({"error": "Invalid book type"}), 400

    # Create a new loan instance
    new_loan = Loan(cust_id=cust_id, book_id=book_id, loan_date=loan_date, return_date=return_date)

    # Update loan status based on return date
    new_loan.update_late_status()
    new_loan.loan_status = 'Not returned' if not new_loan.is_late else 'Late'

    db.session.add(new_loan)
    db.session.commit()

    return "A new loan was created"


# route for updating a loan

@app.route('/loans/upd/<int:id>', methods=['PUT', 'OPTIONS'])
def update_loan(id):
    if request.method == 'OPTIONS':
        # Handling preflight requests
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, DELETE, PUT',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    request_data = request.get_json()
    upd_loan = Loan.query.get(id)
    if upd_loan:
        # Update loan details based on the form data
        upd_loan.cust_id = request_data['cust_id']
        upd_loan.book_id = request_data['book_id']

        # Convert loan_date string to datetime
        upd_loan.loan_date_str = request_data['loan_date']
        upd_loan.loan_date = datetime.strptime(request_data['loan_date'], '%Y-%m-%d').date()

        # Recalculate return_date based on the new loan_date and book_type
        book = Book.query.get(upd_loan.book_id)
        if book:
            if book.book_type == 1:
                upd_loan.return_date = upd_loan.loan_date + timedelta(days=10)
            elif book.book_type == 2:
                upd_loan.return_date = upd_loan.loan_date + timedelta(days=5)
            elif book.book_type == 3:
                upd_loan.return_date = upd_loan.loan_date + timedelta(days=2)
            else:
                return jsonify({"error": "Invalid book type"}), 400

        db.session.commit()
        return jsonify({"message": "A loan was updated", "loan_status": upd_loan.loan_status}), 200
    return jsonify({"error": "No such loan...."}), 404


@app.route('/loans/del/<int:id>', methods=['DELETE'])
def delete_loan(id):
    del_loan = Loan.query.get(id)
    if del_loan:
        db.session.delete(del_loan)
        db.session.commit()
        return "A loan was deleted"
    return "No such loan....", 404

#Defining Users Table
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    user_role = db.Column(db.String(50), default='user') 
    
    # route for registering new user
    
@app.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default to 'user' if role is not provided

    if not username or not password or not role:
        return jsonify({"error": "Missing required fields"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, password=hashed_password, user_role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

   ## User login and get JWT token

@app.route('/user/login', methods=['POST'])              
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.user_id)
    return jsonify(access_token=access_token), 200

# Define route for getting user profile with JWT authentication
@app.route('/user/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.user_role in ['customer', 'manager']:
        return jsonify(message="You have access to this protected route."), 200
    else:
        return jsonify(error="Unauthorized access."), 403

 ## Delete user profile with JWT authentication

@app.route('/user/delete/<int:user_id>', methods=['DELETE'])                       
@jwt_required()
def delete_user(user_id):
    current_user = User.query.get(int(user_id))  
    db.session.delete(current_user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 200

# Logout

@app.route("/logout")           
@jwt_required
def logout():
    return jsonify({"message": "You have been logged out."})
    
    
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)