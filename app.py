from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import user_service
import auth_service
from models import Product  


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Decorators for login and admin checks
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        birthday = request.form['birthday']
        age = request.form['age']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        try:
            user_service.create_user(first_name, middle_name, last_name, birthday, age, address, email, password)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Email already registered.', 'danger')
    return render_template('register.html')

@app.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        birthday = request.form['birthday']
        age = request.form['age']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        try:
            user_service.create_user(first_name, middle_name, last_name, birthday, age, address, email, password)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('Email already registered.', 'danger')
    return render_template('add_staff.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = auth_service.authenticate_user(email, password)
        if user == 'not_approved':
            flash('Your account is pending approval by an admin.', 'warning')
        elif user:
            session['user_id'] = user[0]
            session['first_name'] = user[1]
            session['is_admin'] = user[10] if len(user) > 10 else 0
            if session['is_admin']:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if session.get('is_admin'):
        return redirect(url_for('dashboard'))
    return render_template('user_dashboard.html', first_name=session.get('first_name'))

@app.route('/dashboard')
@admin_required
def dashboard():
    users = user_service.get_all_users()
    pending_users = [u for u in users if u[8] == 0]  
    return render_template('dashboard.html', first_name=session.get('first_name'), users=users, pending_users=pending_users)

@app.route('/approve_user/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    user_service.set_user_approved(user_id, True)
    flash('User approved successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def update_user(user_id):
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        birthday = request.form['birthday']
        age = request.form['age']
        address = request.form['address']
        email = request.form['email']
        try:
            user_service.update_user(user_id, first_name, middle_name, last_name, birthday, age, address, email)
            flash('User updated successfully.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('Email already registered.', 'danger')
    user = user_service.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('update_user.html', user=user)

@app.route('/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    user_service.delete_user(user_id)
    flash('User deleted successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/activity', methods=['GET'])
@login_required
def activity_log():
    return render_template('activity_log.html')

def render_admin_page(page):
    if not session.get('is_admin'):
        return render_template(f'{page}.html')
    return redirect('/dashboard')

@app.route('/sales')
@login_required
def sales():
    return render_admin_page('sales')

@app.route('/inventory')
@login_required
def inventory():
    return render_admin_page('inventory')

@app.route('/customers')
@login_required
def customers():
    return render_admin_page('customers')

@app.route('/reports')
@login_required
def reports():
    return render_admin_page('reports')
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        quantity = request.form['quantity']
        price = request.form['price']
        
        new_product = Product(name=name, sku=sku, quantity=quantity, price=price)
        db.session.add(new_product) 
        db.session.commit()        
        return redirect(url_for('inventory'))  
    return render_template('add_product.html')

if __name__ == '__main__':
    user_service.init_db()
    app.run(debug=True)