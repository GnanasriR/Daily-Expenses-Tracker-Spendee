from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date
import re
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

# --- App Initialization and Configuration ---
app = Flask(__name__)
# IMPORTANT: Change this to a strong, random key in production!
app.config['SECRET_KEY'] = 'your_super_secret_key_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Where to send users who are not logged in
login_manager.login_message_category = 'info' # Category for flash messages when login is required

@login_manager.user_loader
def load_user(user_id):
    """Callback to reload the user object from the user ID stored in the session."""
    return User.query.get(int(user_id))

# --- Database Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False) # Hashed password
    full_name = db.Column(db.String(120), nullable=True)
    dob = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    occupation = db.Column(db.String(80), nullable=True)
    income = db.Column(db.String(50), nullable=True)
    monthly_expenses = db.Column(db.String(50), nullable=True)
    savings_goal = db.Column(db.String(50), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    financial_goal = db.Column(db.String(80), nullable=True)
    expenses = db.relationship('Expense', backref='owner', lazy=True, cascade="all, delete-orphan") # Added cascade

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # ISO date string (YYYY-MM-DD) for day-wise grouping
    date = db.Column(db.String(10), nullable=False, default=lambda: date.today().isoformat())

    def __repr__(self):
        return f"Expense('{self.name}', '{self.amount}')"

# --- Routes ---

# Root URL now directs to login (or index if already logged in)
@app.route('/')
def home():
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # If already logged in, go to index

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email') # Allow login by username or email
        password = request.form.get('password')

        # Try to find user by username or email
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            # Flash message after successful login
            flash(f'Welcome back, {user.username}!', 'success')
            # Get the 'next' parameter if available (for redirected users)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index')) # Redirect to next page or index
        else:
            flash('Login Failed. Please check your username/email and password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # If already logged in, go to index

    if request.method == 'POST':
        # Validate username and password constraints
        username_val = (request.form.get('username') or '').strip()
        email_val = (request.form.get('email') or '').strip()
        password_val = (request.form.get('password') or '')

        if not re.fullmatch(r'^[A-Za-z0-9_]+$', username_val):
            flash('Username can contain only letters, numbers, and underscores.', 'danger')
            return redirect(url_for('signup'))

        if not re.fullmatch(r'^(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$', password_val):
            flash('Password must be at least 8 characters, include a digit and a special character.', 'danger')
            return redirect(url_for('signup'))

        # Validate email format
        try:
            local_part, domain_part = email_val.split('@', 1)
            if '.' not in domain_part or re.search(r"\d", domain_part):
                raise ValueError
        except Exception:
            flash('Email must include @ and . and contain no digits in the domain.', 'danger')
            return redirect(url_for('signup'))

        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username_val) | (User.email == email_val)).first()
        if existing_user:
            flash('Username or email already exists. Please choose another.', 'warning') # Changed to warning
            return redirect(url_for('signup'))
            
        hashed_password = bcrypt.generate_password_hash(password_val).decode('utf-8')
        new_user = User(
            username=username_val, 
            email=email_val, 
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user) # Log the user in immediately after signup
        flash('Your account has been created! Please fill in your details to get started.', 'success')
        return redirect(url_for('userdetails')) # Redirect to userdetails

    return render_template('signup.html')

@app.route('/userdetails', methods=['GET', 'POST'])
@login_required
def userdetails():
    if request.method == 'POST':
        # --- Validation ---
        full_name = (request.form.get('fullName') or '').strip()
        email_val = (request.form.get('email') or current_user.email or '').strip()
        dob_str = (request.form.get('dob') or '').strip()
        phone_val = (request.form.get('phone') or '').strip()
        occupation_val = (request.form.get('occupation') or '').strip()
        income_val = (request.form.get('income') or '').strip()
        expenses_val = (request.form.get('expenses') or '').strip()
        savings_goal_val = (request.form.get('savingsGoal') or '').strip()
        currency_val = (request.form.get('currency') or '').strip()
        financial_goal_val = (request.form.get('financialGoal') or '').strip()

        # Full name: letters and spaces only
        if full_name and not re.fullmatch(r"[A-Za-z ]+", full_name):
            flash('Full name should contain letters and spaces only.', 'danger')
            return redirect(url_for('userdetails'))

        # Email: must contain @ and . ; no digits after @ (domain)
        try:
            local_part, domain_part = email_val.split('@', 1)
            if '.' not in domain_part or re.search(r"\d", domain_part):
                raise ValueError
        except Exception:
            flash('Email must include @ and . and contain no digits in the domain.', 'danger')
            return redirect(url_for('userdetails'))

        # Phone: digits only, at least 10 digits
        if phone_val and (not phone_val.isdigit() or len(phone_val) < 10):
            flash('Phone number must be at least 10 digits and digits only.', 'danger')
            return redirect(url_for('userdetails'))

        # DOB: at least 12 years old
        if dob_str:
            try:
                y, m, d = map(int, dob_str.split('-'))
                dob_date = date(y, m, d)
                today_d = date.today()
                age = today_d.year - dob_date.year - ((today_d.month, today_d.day) < (dob_date.month, dob_date.day))
                if age < 12:
                    flash('You must be at least 12 years old.', 'danger')
                    return redirect(url_for('userdetails'))
            except Exception:
                flash('Invalid date of birth.', 'danger')
                return redirect(url_for('userdetails'))

        # Savings goal must not exceed monthly income
        try:
            inc = float(income_val) if income_val else 0.0
            goal = float(savings_goal_val) if savings_goal_val else 0.0
            if goal > inc and inc > 0:
                flash('Savings goal cannot exceed monthly income.', 'danger')
                return redirect(url_for('userdetails'))
        except ValueError:
            flash('Income and Savings Goal must be numbers.', 'danger')
            return redirect(url_for('userdetails'))

        # --- Save after validation ---
        user_to_update = current_user
        user_to_update.full_name = full_name or None
        user_to_update.dob = dob_str or None
        user_to_update.phone = phone_val or None
        user_to_update.occupation = occupation_val or None
        user_to_update.income = income_val or None
        user_to_update.monthly_expenses = expenses_val or None
        user_to_update.savings_goal = savings_goal_val or None
        user_to_update.currency = currency_val or None
        user_to_update.financial_goal = financial_goal_val or None

        db.session.commit()
        flash('Your details have been saved successfully!', 'success')
        return redirect(url_for('index')) # Redirect to the main app page

    # Pre-populate form if user details already exist
    return render_template('userdetails.html', user=current_user)

@app.route('/logout')
@login_required # Only allow logged in users to logout
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- Protected Application Pages (Require Login) ---

@app.route('/index')
def index():
    # Show user's expenses if logged in; otherwise show an empty view
    if current_user.is_authenticated:
        today_str = date.today().isoformat()
        # Today's entries for the list
        todays_expenses = Expense.query.filter_by(user_id=current_user.id, date=today_str).order_by(Expense.id.desc()).all()
        # All-time total
        total_amount = db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0.0)).filter_by(user_id=current_user.id).scalar() or 0.0
        total_today = db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0.0)).filter_by(user_id=current_user.id, date=today_str).scalar() or 0.0
        savings_goal = current_user.savings_goal
    else:
        todays_expenses = []
        total_amount = 0.0
        total_today = 0.0
        savings_goal = None
    return render_template('index.html', expenses=todays_expenses, total_amount=total_amount, total_today=total_today, today=date.today().strftime('%A, %B %d, %Y'), savings_goal=savings_goal)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    expense_name = request.form.get('expense-name')
    expense_amount = request.form.get('expense-amount')

    if not expense_name or not expense_amount:
        flash('Expense name and amount are required.', 'danger')
        return redirect(url_for('index'))

    try:
        amount = float(expense_amount)
        if amount <= 0:
            flash('Amount must be positive.', 'danger')
            return redirect(url_for('index'))

        new_expense = Expense(name=expense_name, amount=amount, owner=current_user, date=date.today().isoformat())
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
    except ValueError:
        flash('Invalid amount. Please enter a number.', 'danger')
    
    return redirect(url_for('index'))

@app.route('/delete_expense/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.owner == current_user: # Ensure user owns the expense
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    else:
        flash('You are not authorized to delete this expense.', 'danger')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Aggregate across all dates and group by expense name
    grouped = (
        db.session.query(Expense.name, db.func.coalesce(db.func.sum(Expense.amount), 0.0))
        .filter(Expense.user_id == current_user.id)
        .group_by(Expense.name)
        .order_by(Expense.name.asc())
        .all()
    )
    labels = [row[0] for row in grouped]
    amounts = [float(row[1]) for row in grouped]
    # Compute current month's savings percentage if income is set
    month_prefix = date.today().isoformat()[:7]  # YYYY-MM
    month_spent = db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0.0)).\
        filter(Expense.user_id == current_user.id, Expense.date.like(f"{month_prefix}-%")).scalar() or 0.0
    try:
        income_val = float(current_user.income) if current_user.income is not None else 0.0
    except ValueError:
        income_val = 0.0
    savings_pct = None
    monthly_savings_amount = None
    if income_val > 0:
        monthly_savings_amount = max(0.0, income_val - float(month_spent))
        savings_pct = round((monthly_savings_amount / income_val) * 100, 2)
    return render_template(
        'dashboard.html',
        user=current_user,
        labels=labels,
        amounts=amounts,
        month_spent=float(month_spent),
        income_val=income_val,
        savings_pct=savings_pct,
        monthly_savings_amount=monthly_savings_amount,
    )

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)

# --- Edit Details ---
@app.route('/edit_details', methods=['GET', 'POST'])
@login_required
def edit_details():
    if request.method == 'POST':
        # Extract
        full_name = (request.form.get('full_name') or '').strip()
        email_val = current_user.email or ''
        dob_str = (request.form.get('dob') or '').strip()
        phone_val = (request.form.get('phone') or '').strip()
        occupation_val = (request.form.get('occupation') or '').strip()
        income_val = (request.form.get('income') or '').strip()
        monthly_expenses_val = (request.form.get('monthly_expenses') or '').strip()
        currency_val = (request.form.get('currency') or '').strip()
        savings_goal_val = (request.form.get('savings_goal') or '').strip()
        financial_goal_val = (request.form.get('financial_goal') or '').strip()

        # Validate (same rules)
        if full_name and not re.fullmatch(r"[A-Za-z ]+", full_name):
            flash('Full name should contain letters and spaces only.', 'danger')
            return redirect(url_for('edit_details'))

        try:
            local_part, domain_part = email_val.split('@', 1)
            if '.' not in domain_part or re.search(r"\d", domain_part):
                raise ValueError
        except Exception:
            flash('Email must include @ and . and contain no digits in the domain.', 'danger')
            return redirect(url_for('edit_details'))

        if phone_val and (not phone_val.isdigit() or len(phone_val) < 10):
            flash('Phone number must be at least 10 digits and digits only.', 'danger')
            return redirect(url_for('edit_details'))

        if dob_str:
            try:
                y, m, d = map(int, dob_str.split('-'))
                dob_date = date(y, m, d)
                today_d = date.today()
                age = today_d.year - dob_date.year - ((today_d.month, today_d.day) < (dob_date.month, dob_date.day))
                if age < 12:
                    flash('You must be at least 12 years old.', 'danger')
                    return redirect(url_for('edit_details'))
            except Exception:
                flash('Invalid date of birth.', 'danger')
                return redirect(url_for('edit_details'))

        try:
            inc = float(income_val) if income_val else 0.0
            goal = float(savings_goal_val) if savings_goal_val else 0.0
            if goal > inc and inc > 0:
                flash('Savings goal cannot exceed monthly income.', 'danger')
                return redirect(url_for('edit_details'))
        except ValueError:
            flash('Income and Savings Goal must be numbers.', 'danger')
            return redirect(url_for('edit_details'))

        # Save
        user_to_update = current_user
        user_to_update.full_name = full_name or None
        user_to_update.dob = dob_str or None
        user_to_update.phone = phone_val or None
        user_to_update.occupation = occupation_val or None
        user_to_update.income = income_val or None
        user_to_update.monthly_expenses = monthly_expenses_val or None
        user_to_update.currency = currency_val or None
        user_to_update.savings_goal = savings_goal_val or None
        user_to_update.financial_goal = financial_goal_val or None
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('settings'))

    return render_template('edit_details.html', user=current_user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables if they don't exist
        # Lightweight migration: add 'date' column if missing
        try:
            insp = db.session.execute(db.text("PRAGMA table_info(expense)"))
            cols = [row[1] for row in insp]
            if 'date' not in cols:
                db.session.execute(db.text("ALTER TABLE expense ADD COLUMN date TEXT"))
                db.session.commit()
        except Exception:
            db.session.rollback()
    app.run(debug=True)