from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Transaction
from app.routes.main import STANDARD_CATEGORIES

transactions_bp = Blueprint('transactions', __name__)

# -----------------------------------------------------------
# 1. ADD TRANSACTION ROUTE (POST)
# -----------------------------------------------------------
@transactions_bp.route('/add', methods=['POST'])
@login_required
def add_transaction():
    title = request.form.get('title', '').strip()
    amount_str = request.form.get('amount', '').strip()
    trans_type = request.form.get('type', 'expense')
    category = request.form.get('category', 'Other / UPI Transfer')
    date_str = request.form.get('date', '').strip()
    notes = request.form.get('notes', '').strip()

    # Input Validation
    if not title or not amount_str:
        flash('Title and Amount are required.', 'danger')
        return redirect(request.referrer or url_for('main.dashboard'))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(request.referrer or url_for('main.dashboard'))
    except ValueError:
        flash('Please enter a valid numeric amount.', 'danger')
        return redirect(request.referrer or url_for('main.dashboard'))

    # Date parsing
    if date_str:
        try:
            trans_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            trans_date = datetime.utcnow().date()
    else:
        trans_date = datetime.utcnow().date()

    # Create and commit new record linked to current_user
    new_tx = Transaction(
        user_id=current_user.id,
        title=title,
        amount=round(amount, 2),
        type=trans_type,
        category=category,
        date=trans_date,
        notes=notes
    )

    db.session.add(new_tx)
    db.session.commit()

    flash(f'Successfully added {trans_type.capitalize()}: "{title}" for ₹{amount:,.2f}!', 'success')
    return redirect(request.referrer or url_for('main.dashboard'))

# -----------------------------------------------------------
# 2. FULL TRANSACTIONS LIST WITH SEARCH & FILTER
# -----------------------------------------------------------
@transactions_bp.route('')
@transactions_bp.route('/')
@login_required
def list_transactions():
    trans_type = request.args.get('type', 'all')
    category = request.args.get('category', 'all')
    search = request.args.get('q', '').strip()

    query = Transaction.query.filter_by(user_id=current_user.id)

    if trans_type in ['income', 'expense']:
        query = query.filter_by(type=trans_type)

    if category != 'all' and category:
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            (Transaction.title.ilike(f'%{search}%')) |
            (Transaction.notes.ilike(f'%{search}%'))
        )

    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

    return render_template(
        'transactions.html',
        transactions=transactions,
        categories=STANDARD_CATEGORIES,
        current_type=trans_type,
        current_category=category,
        search_query=search
    )

# -----------------------------------------------------------
# 3. DELETE TRANSACTION ROUTE
# -----------------------------------------------------------
@transactions_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    # Security: Ensure transaction belongs to CURRENT user before deleting!
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    title = tx.title
    db.session.delete(tx)
    db.session.commit()

    flash(f'Transaction "{title}" was deleted.', 'info')
    return redirect(request.referrer or url_for('transactions.list_transactions'))

# -----------------------------------------------------------
# 4. RESET ALL TRANSACTIONS ROUTE
# -----------------------------------------------------------
@transactions_bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    deleted = Transaction.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash(f'Cleared {deleted} transactions. You now have a fresh ₹0.00 slate!', 'info')
    return redirect(url_for('main.dashboard'))
