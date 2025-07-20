from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import user_service
import auth_service

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'

# Decorators for role-based access control
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
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['admin', 'seller']:
            flash('Access denied. Seller privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'customer':
            flash('Access denied. Customer privileges required.', 'danger')
            return redirect(url_for('dashboard'))
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
            user_service.create_user(first_name, middle_name, last_name, birthday, age, address, email, password, 'customer')
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Email already registered.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = auth_service.authenticate_user(email, password)
        
        if user == 'locked':
            flash('Account is locked due to too many failed login attempts. Please contact administrator.', 'danger')
        elif user:
            session['user_id'] = user[0]
            session['first_name'] = user[1]
            session['last_name'] = user[3]
            session['email'] = user[7]
            session['role'] = user[9]  # role is at index 9
            
            # Redirect based on role
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif session['role'] == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:  # customer
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = user_service.get_all_users()
    products = user_service.get_all_products()
    sales = user_service.get_sales_history()
    return render_template('admin/dashboard.html', 
                         users=users, 
                         products=products, 
                         sales=sales,
                         user_count=len(users),
                         product_count=len(products),
                         sales_count=len(sales))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = user_service.get_all_users()
    return render_template('admin/users.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        birthday = request.form['birthday']
        age = request.form['age']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        try:
            user_service.create_user(first_name, middle_name, last_name, birthday, age, address, email, password, role)
            flash('User created successfully!', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            flash('Email already registered.', 'danger')
    return render_template('admin/add_user.html')

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        birthday = request.form['birthday']
        age = request.form['age']
        address = request.form['address']
        email = request.form['email']
        role = request.form['role']
        
        try:
            user_service.update_user(user_id, first_name, middle_name, last_name, birthday, age, address, email, role)
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            flash('Error updating user.', 'danger')
    
    user = user_service.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def admin_delete_user(user_id):
    try:
        user_service.delete_user(user_id)
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting user.', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = user_service.get_all_products()
    return render_template('admin/products.html', products=products)

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form['name'].strip()
        sku = request.form['sku'].strip()
        quantity = request.form['quantity'].strip()
        price = request.form['price'].strip()
        
        try:
            quantity_int = int(quantity)
            price_float = float(price)
            if quantity_int < 0 or price_float < 0:
                raise ValueError
        except ValueError:
            flash('Invalid quantity or price.', 'danger')
            return render_template('admin/add_product.html')
        
        try:
            user_service.add_product(name, sku, quantity_int, price_float)
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash('Error adding product. SKU might already exist.', 'danger')
    
    return render_template('admin/add_product.html')

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    if request.method == 'POST':
        name = request.form['name'].strip()
        sku = request.form['sku'].strip()
        quantity = request.form['quantity'].strip()
        price = request.form['price'].strip()
        
        try:
            quantity_int = int(quantity)
            price_float = float(price)
            if quantity_int < 0 or price_float < 0:
                raise ValueError
        except ValueError:
            flash('Invalid quantity or price.', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))
        
        try:
            user_service.update_product(product_id, name, sku, quantity_int, price_float)
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash('Error updating product.', 'danger')
    
    product = user_service.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/delete_product/<int:product_id>')
@login_required
@admin_required
def admin_delete_product(product_id):
    try:
        user_service.delete_product(product_id)
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting product.', 'danger')
    return redirect(url_for('admin_products'))

@app.route('/admin/transactions')
@login_required
@admin_required
def admin_transactions():
    sales = user_service.get_sales_history()
    return render_template('admin/transactions.html', sales=sales)

@app.route('/admin/transaction/<int:sale_id>')
@login_required
@admin_required
def admin_transaction_detail(sale_id):
    sale = user_service.get_sale_by_id(sale_id)
    items = user_service.get_sale_details(sale_id)
    return render_template('admin/transaction_detail.html', sale=sale, items=items)

# Seller Routes
@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if session.get('role') not in ['admin', 'seller']:
        return redirect(url_for('dashboard'))
    
    products = user_service.get_all_products()
    sales = user_service.get_sales_history()
    return render_template('seller/dashboard.html', 
                         products=products, 
                         sales=sales,
                         product_count=len(products),
                         sales_count=len(sales))

@app.route('/seller/products')
@login_required
@seller_required
def seller_products():
    products = user_service.get_all_products()
    return render_template('seller/products.html', products=products)

@app.route('/seller/add_product', methods=['GET', 'POST'])
@login_required
@seller_required
def seller_add_product():
    if request.method == 'POST':
        name = request.form['name'].strip()
        sku = request.form['sku'].strip()
        quantity = request.form['quantity'].strip()
        price = request.form['price'].strip()
        
        try:
            quantity_int = int(quantity)
            price_float = float(price)
            if quantity_int < 0 or price_float < 0:
                raise ValueError
        except ValueError:
            flash('Invalid quantity or price.', 'danger')
            return render_template('seller/add_product.html')
        
        try:
            user_service.add_product(name, sku, quantity_int, price_float)
            flash('Product added successfully!', 'success')
            return redirect(url_for('seller_products'))
        except Exception as e:
            flash('Error adding product. SKU might already exist.', 'danger')
    
    return render_template('seller/add_product.html')

@app.route('/seller/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@seller_required
def seller_edit_product(product_id):
    if request.method == 'POST':
        name = request.form['name'].strip()
        sku = request.form['sku'].strip()
        quantity = request.form['quantity'].strip()
        price = request.form['price'].strip()
        
        try:
            quantity_int = int(quantity)
            price_float = float(price)
            if quantity_int < 0 or price_float < 0:
                raise ValueError
        except ValueError:
            flash('Invalid quantity or price.', 'danger')
            return redirect(url_for('seller_edit_product', product_id=product_id))
        
        try:
            user_service.update_product(product_id, name, sku, quantity_int, price_float)
            flash('Product updated successfully!', 'success')
            return redirect(url_for('seller_products'))
        except Exception as e:
            flash('Error updating product.', 'danger')
    
    product = user_service.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('seller_products'))
    
    return render_template('seller/edit_product.html', product=product)

@app.route('/seller/delete_product/<int:product_id>')
@login_required
@seller_required
def seller_delete_product(product_id):
    try:
        user_service.delete_product(product_id)
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting product.', 'danger')
    return redirect(url_for('seller_products'))

@app.route('/seller/transactions')
@login_required
@seller_required
def seller_transactions():
    sales = user_service.get_sales_history()
    return render_template('seller/transactions.html', sales=sales)

@app.route('/seller/transaction/<int:sale_id>')
@login_required
@seller_required
def seller_transaction_detail(sale_id):
    sale = user_service.get_sale_by_id(sale_id)
    items = user_service.get_sale_details(sale_id)
    return render_template('seller/transaction_detail.html', sale=sale, items=items)

# Customer Routes
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if session.get('role') != 'customer':
        return redirect(url_for('dashboard'))
    
    products = user_service.get_all_products()
    sales = user_service.get_sales_history('customer', session.get('user_id'))
    return render_template('customer/dashboard.html', 
                         products=products, 
                         sales=sales,
                         product_count=len(products),
                         sales_count=len(sales))

@app.route('/customer/products')
@login_required
@customer_required
def customer_products():
    products = user_service.get_all_products()
    return render_template('customer/products.html', products=products)

@app.route('/customer/purchase', methods=['GET', 'POST'])
@login_required
@customer_required
def customer_purchase():
    if request.method == 'POST':
        selected_products = request.form.getlist('products')
        quantities = {}
        
        for product_id in selected_products:
            quantity = request.form.get(f'quantity_{product_id}', 1)
            try:
                quantities[int(product_id)] = int(quantity)
            except ValueError:
                flash('Invalid quantity.', 'danger')
                return redirect(url_for('customer_purchase'))
        
        if not quantities:
            flash('Please select at least one product.', 'danger')
            return redirect(url_for('customer_purchase'))
        
        # Process the purchase
        try:
            total = 0
            items_to_purchase = []
            
            for product_id, quantity in quantities.items():
                product = user_service.get_product_by_id(product_id)
                if not product:
                    flash(f'Product not found.', 'danger')
                    return redirect(url_for('customer_purchase'))
                
                if product[3] < quantity:  # product[3] is quantity
                    flash(f'Not enough stock for {product[1]}.', 'danger')
                    return redirect(url_for('customer_purchase'))
                
                subtotal = product[4] * quantity  # product[4] is price
                total += subtotal
                items_to_purchase.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': product[4],
                    'subtotal': subtotal
                })
            
            # Record the sale
            customer_name = f"{session.get('first_name')} {session.get('last_name')}"
            sale_id = user_service.record_sale(total, customer_name, session.get('email'), session.get('user_id'))
            
            # Add sale items and update stock
            for item in items_to_purchase:
                user_service.add_sale_item(sale_id, item['product_id'], item['quantity'], item['price'])
                user_service.update_product_stock(item['product_id'], item['quantity'])
            
            flash('Purchase completed successfully!', 'success')
            return redirect(url_for('customer_transaction_detail', sale_id=sale_id))
            
        except Exception as e:
            flash(f'Error processing purchase: {e}', 'danger')
            return redirect(url_for('customer_purchase'))
    
    products = user_service.get_all_products()
    return render_template('customer/purchase.html', products=products)

@app.route('/customer/transactions')
@login_required
@customer_required
def customer_transactions():
    sales = user_service.get_sales_history('customer', session.get('user_id'))
    return render_template('customer/transactions.html', sales=sales)

@app.route('/customer/transaction/<int:sale_id>')
@login_required
@customer_required
def customer_transaction_detail(sale_id):
    sale = user_service.get_sale_by_id(sale_id)
    items = user_service.get_sale_details(sale_id)
    
    # Verify customer can only see their own transactions
    if sale[3] != session.get('email'):  # sale[3] is customer_email
        flash('Access denied.', 'danger')
        return redirect(url_for('customer_transactions'))
    
    return render_template('customer/transaction_detail.html', sale=sale, items=items)

# General dashboard redirect
@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'seller':
        return redirect(url_for('seller_dashboard'))
    else:
        return redirect(url_for('customer_dashboard'))

if __name__ == '__main__':
    user_service.init_db()
    app.run(debug=True)