from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Budget
from app.routes.main import STANDARD_CATEGORIES

budgets_bp = Blueprint('budgets', __name__)

# -----------------------------------------------------------
# 1. LIST BUDGETS & CALCULATE PROGRESS
# -----------------------------------------------------------
@budgets_bp.route('')
@budgets_bp.route('/')
@login_required
def list_budgets():
    current_month_year = datetime.utcnow().strftime('%Y-%m')
    selected_month = request.args.get('month', current_month_year)

    user_budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month_year=selected_month
    ).all()

    budget_details = []
    total_budgeted = 0.0
    total_spent = 0.0

    for b in user_budgets:
        spent = b.get_spending()
        pct = b.get_percentage()
        remaining = round(b.monthly_limit - spent, 2)
        total_budgeted += b.monthly_limit
        total_spent += spent

        # Classify color status
        if pct >= 100:
            status = 'danger'
        elif pct >= 80:
            status = 'warning'
        else:
            status = 'success'

        budget_details.append({
            'id': b.id,
            'category': b.category,
            'monthly_limit': b.monthly_limit,
            'spent': spent,
            'pct': pct,
            'remaining': remaining,
            'status': status
        })

    return render_template(
        'budgets.html',
        budgets=budget_details,
        categories=[c for c in STANDARD_CATEGORIES if 'Salary' not in c],
        current_month=selected_month,
        total_budgeted=round(total_budgeted, 2),
        total_spent=round(total_spent, 2)
    )

# -----------------------------------------------------------
# 2. SET / UPDATE BUDGET (POST)
# -----------------------------------------------------------
@budgets_bp.route('/set', methods=['POST'])
@login_required
def set_budget():
    category = request.form.get('category', '').strip()
    limit_str = request.form.get('monthly_limit', '').strip()
    month_year = request.form.get('month_year', '').strip()

    if not month_year:
        month_year = datetime.utcnow().strftime('%Y-%m')

    if not category or not limit_str:
        flash('Category and Monthly Limit are required.', 'danger')
        return redirect(url_for('budgets.list_budgets'))

    try:
        limit = float(limit_str)
        if limit <= 0:
            flash('Budget limit must be greater than zero.', 'danger')
            return redirect(url_for('budgets.list_budgets'))
    except ValueError:
        flash('Invalid numeric limit entered.', 'danger')
        return redirect(url_for('budgets.list_budgets'))

    # If budget already exists for this category this month, update it
    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category=category,
        month_year=month_year
    ).first()

    if existing:
        existing.monthly_limit = round(limit, 2)
        flash(f'Budget for {category} updated to ₹{limit:,.2f} for {month_year}.', 'success')
    else:
        new_budget = Budget(
            user_id=current_user.id,
            category=category,
            monthly_limit=round(limit, 2),
            month_year=month_year
        )
        db.session.add(new_budget)
        flash(f'New budget of ₹{limit:,.2f} set for {category} ({month_year})!', 'success')

    db.session.commit()
    return redirect(url_for('budgets.list_budgets', month=month_year))

# -----------------------------------------------------------
# 3. DELETE BUDGET (POST)
# -----------------------------------------------------------
@budgets_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_budget(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    cat = budget.category
    db.session.delete(budget)
    db.session.commit()
    flash(f'Budget limit for "{cat}" was removed.', 'info')
    return redirect(request.referrer or url_for('budgets.list_budgets'))
