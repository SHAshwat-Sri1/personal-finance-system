from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------------------------------------
# 1. USER TABLE: Stores registered accounts
# -----------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships: If a user is deleted, all their transactions & budgets get deleted too
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.username}>"


# -----------------------------------------------------------
# 2. TRANSACTION TABLE: Stores daily incomes and expenses
# -----------------------------------------------------------
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Links to User
    title = db.Column(db.String(100), nullable=False)                          # e.g. "Petrol"
    amount = db.Column(db.Float, nullable=False)                               # e.g. 500.00
    type = db.Column(db.String(10), nullable=False)                            # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)                        # e.g. "Transportation"
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.title}: {self.type} ₹{self.amount}>"


# -----------------------------------------------------------
# 3. BUDGET TABLE: Stores monthly spending limits
# -----------------------------------------------------------
class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Links to User
    category = db.Column(db.String(50), nullable=False)                        # e.g. "Food"
    monthly_limit = db.Column(db.Float, nullable=False)                        # e.g. 5000.00
    month_year = db.Column(db.String(7), nullable=False)                       # e.g. "2026-09"

    def get_spending(self):
        """Calculates total expenses in this category for this month"""
        from sqlalchemy import extract
        year, month = map(int, self.month_year.split('-'))
        total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.category == self.category,
            Transaction.type == 'expense',
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        ).scalar()
        return round(total or 0.0, 2)

    def get_percentage(self):
        """Calculates percentage of budget consumed (e.g. 80%)"""
        if self.monthly_limit <= 0:
            return 0.0
        spent = self.get_spending()
        return round((spent / self.monthly_limit) * 100, 1)

    def __repr__(self):
        return f"<Budget {self.category}: ₹{self.monthly_limit}>"
    