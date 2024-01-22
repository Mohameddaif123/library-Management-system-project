from datetime import date
from app import app, db, Book, Customer, Loan

def insert_test_data():
    with app.app_context():
        # Insert test books
        book1 = Book(name="lord of the rings", author="edward the third", year_published=2023, book_type=1, )
        book2 = Book(name="this is rome", author="philps", year_published=1920, book_type=2, )
        book3 = Book(name="the dark house", author="picaso", year_published=2017, book_type=3, )
        
        db.session.add_all([book1, book2, book3])
        db.session.commit()

        # Insert test customers
        customer1 = Customer(name="mahmod", city="yafo", age=27)
        customer2 = Customer(name="moshe", city="tel aviv ", age=30)
        
        db.session.add_all([customer1, customer2])
        db.session.commit()

        # Insert test loans
        loan1 = Loan(cust_id=1, book_id=1, loan_date=date(2023, 1, 5), return_date=date(2023, 1, 7))
        loan2 = Loan(cust_id=2, book_id=2, loan_date=date(2022, 5, 7), return_date=date(2022, 5, 17))
        
        db.session.add_all([loan1, loan2])
        db.session.commit()

if __name__ == "__main__":
    insert_test_data()
