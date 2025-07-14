from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import user_service
import auth_service
# Remove: from models import Product


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

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        # Only allow if staff (not admin, not pending approval)
        if not (session.get('is_staff') == 1):
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
            session['is_staff'] = 1 if (user[9] == 1 and (user[10] if len(user) > 10 else 0) == 0) else 0
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


def render_admin_page(page):
    if not session.get('is_admin'):
        return render_template(f'{page}.html')
    return redirect('/dashboard')

@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    # Initialize cart in session if not present
    if 'cart' not in session:
        session['cart'] = []
    cart = session['cart']
    cart_total = sum(item['subtotal'] for item in cart)
    return render_admin_page('sales') if session.get('is_admin') else render_template('sales.html', cart=cart, cart_total=cart_total)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_search = request.form.get('product_search', '').strip()
    quantity = request.form.get('quantity', 1)
    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except ValueError:
        flash('Invalid quantity.', 'danger')
        return redirect(url_for('sales'))
    # Find product by name or SKU
    products = user_service.get_all_products()
    product = None
    for p in products:
        if product_search.lower() in p[1].lower() or product_search.lower() == p[2].lower():
            product = p
            break
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('sales'))
    if product[3] < quantity:
        flash('Not enough stock.', 'danger')
        return redirect(url_for('sales'))
    # Add to cart in session
    if 'cart' not in session:
        session['cart'] = []
    cart = session['cart']
    # Check if already in cart
    for item in cart:
        if item['id'] == product[0]:
            item['quantity'] += quantity
            item['subtotal'] = item['quantity'] * product[4]
            break
    else:
        cart.append({
            'id': product[0],
            'name': product[1],
            'quantity': quantity,
            'price': product[4],
            'subtotal': quantity * product[4]
        })
    session['cart'] = cart
    flash('Product added to cart.', 'success')
    return redirect(url_for('sales'))

@app.route('/inventory')
@login_required
def inventory():
    products = user_service.get_all_products()
    # Convert to list of dicts for template
    products = [
        {'id': p[0], 'name': p[1], 'sku': p[2], 'quantity': p[3], 'price': p[4]} for p in products
    ]
    return render_template('inventory.html', products=products)
# add route for activity_log.html
@app.route('/activity')
@login_required
def activity_log():
    # activities = user_service.get_activity_log()
    return render_template('activity_log.html')
@app.route('/customers')
@login_required
def customers():
    return render_admin_page('customers')

@app.route('/reports')
@login_required
def reports():
    return render_admin_page('reports')
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
@staff_required
def add_product():
    if request.method == 'POST':
        name = request.form['name'].strip()
        sku = request.form['sku'].strip()
        quantity = request.form['quantity'].strip()
        price = request.form['price'].strip()
        # Input validation and type conversion
        error = None
        try:
            if not name or not sku or not quantity or not price:
                error = 'All fields are required.'
            quantity_int = int(quantity)
            price_float = float(price)
            if quantity_int < 0 or price_float < 0:
                error = 'Quantity and price must be non-negative.'
        except ValueError:
            error = 'Quantity must be an integer and price must be a number.'
        if error:
            flash(error, 'danger')
            return render_template('add_product.html', product={'name': name, 'sku': sku, 'quantity': quantity, 'price': price})
        try:
            user_service.add_product(name, sku, quantity_int, price_float)
            flash('Product added successfully!', 'success')
            return redirect(url_for('inventory'))
        except Exception as e:
            import sqlite3
            if isinstance(e, sqlite3.IntegrityError) and 'UNIQUE constraint failed: product.sku' in str(e):
                flash('SKU already exists. Please use a unique SKU.', 'danger')
            else:
                flash('Error adding product: {}'.format(e), 'danger')
            # Optionally log the error for debugging
            import traceback
            print('Error adding product:', traceback.format_exc())
            return render_template('add_product.html', product={'name': name, 'sku': sku, 'quantity': quantity, 'price': price})
    return render_template('add_product.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@staff_required
def edit_product(product_id):
    product = user_service.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('inventory'))
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        quantity = request.form['quantity']
        price = request.form['price']
        try:
            user_service.update_product(product_id, name, sku, quantity, price)
            flash('Product updated successfully!', 'success')
            return redirect(url_for('inventory'))
        except Exception as e:
            flash('Error updating product: {}'.format(e), 'danger')
    # Convert to dict for template
    product_dict = {'id': product[0], 'name': product[1], 'sku': product[2], 'quantity': product[3], 'price': product[4]}
    return render_template('add_product.html', product=product_dict, edit=True)

@app.route('/delete_product', methods=['POST'])
@login_required
@admin_required
def delete_product():
    product_id = request.form['product_id']
    try:
        user_service.delete_product(product_id)
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting product: {}'.format(e), 'danger')
    return redirect(url_for('inventory'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = session.get('cart', [])
    if not cart:
        flash('Cart is empty.', 'danger')
        return redirect(url_for('sales'))
    total = sum(item['subtotal'] for item in cart)
    try:
        sale_id = user_service.record_sale(total)
        for item in cart:
            user_service.add_sale_item(sale_id, item['id'], item['quantity'], item['price'])
            user_service.update_product_stock(item['id'], item['quantity'])
        session['cart'] = []
        flash('Checkout successful! Sale recorded.', 'success')
    except Exception as e:
        flash(f'Error during checkout: {e}', 'danger')
    return redirect(url_for('sales'))

@app.route('/staff')
@admin_required
def staff_management():
    staff = user_service.get_all_staff()
    return render_template('add_staff.html', staff=staff)

if __name__ == '__main__':
    user_service.init_db()
    app.run(debug=True)