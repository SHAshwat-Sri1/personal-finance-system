from datetime import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app import db
from app.models import Transaction, Budget

main_bp = Blueprint('main', __name__)

# Standard Indian expense categories
STANDARD_CATEGORIES = [
    'Food & Dining / Groceries',
    'Rent & Housing',
    'Utilities & Bills (Electricity, Wifi)',
    'Transportation / Petrol / Metro',
    'Shopping',
    'Entertainment & OTT',
    'Healthcare & Medical',
    'Salary & Income',
    'Investments & SIP / Mutual Funds',
    'Other / UPI Transfer'
]

# -----------------------------------------------------------
# 1. LANDING PAGE (Public)
# -----------------------------------------------------------
@main_bp.route('/')
def index():
    return render_template('index.html')

# -----------------------------------------------------------
# 2. DASHBOARD PAGE (Private - Requires Login)
# -----------------------------------------------------------
@main_bp.route('/dashboard')
@login_required
def dashboard():
    today = datetime.utcnow()
    current_month_year = today.strftime('%Y-%m')

    # Query 1: All-time Total Income
    all_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income'
    ).scalar() or 0.0

    # Query 2: All-time Total Expenses
    all_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense'
    ).scalar() or 0.0

    # Formula: Net Balance = Total Income - Total Expenses
    total_balance = all_income - all_expense

    # Query 3: Income for the current calendar month
    month_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        extract('year', Transaction.date) == today.year,
        extract('month', Transaction.date) == today.month
    ).scalar() or 0.0

    # Query 4: Expenses for the current calendar month
    month_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('year', Transaction.date) == today.year,
        extract('month', Transaction.date) == today.month
    ).scalar() or 0.0

    # Query 5: Fetch the 5 most recent transactions
    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(5).all()

    # Query 6: Check for any budget warning alerts
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month_year=current_month_year
    ).all()

    budget_alerts = []
    for b in budgets:
        pct = b.get_percentage()
        if pct >= 100:
            budget_alerts.append({
                'category': b.category,
                'type': 'danger',
                'msg': f'You have exceeded your {b.category} budget! (Spent ₹{b.get_spending():,.2f} of ₹{b.monthly_limit:,.2f})'
            })
        elif pct >= 80:
            budget_alerts.append({
                'category': b.category,
                'type': 'warning',
                'msg': f'Warning: You have used {pct:.0f}% of your {b.category} budget.'
            })

    return render_template(
        'dashboard.html',
        user=current_user,
        total_balance=round(total_balance, 2),
        all_income=round(all_income, 2),
        all_expense=round(all_expense, 2),
        month_income=round(month_income, 2),
        month_expense=round(month_expense, 2),
        recent_transactions=recent_transactions,
        budget_alerts=budget_alerts,
        categories=STANDARD_CATEGORIES,
        today_date=today.strftime('%Y-%m-%d')
    )