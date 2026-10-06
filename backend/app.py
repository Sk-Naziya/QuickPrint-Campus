import os
import re
import uuid
from datetime import datetime
from pathlib import Path

import qrcode
from flask import Flask, jsonify, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import get_db_connection, init_db
from models import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE, ORDER_STATUSES, PAYMENT_STATUSES

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / 'backend' / 'uploads'
QR_DIR = BASE_DIR / 'backend' / 'generated_qr'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'quickprint-campus-demo-secret')


def iso_now():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')


def error_response(message, status_code=400):
    return jsonify({'error': message}), status_code


def normalize_text(value, field_name):
    if value is None:
        return ''
    text = str(value).strip()
    if not text:
        raise ValueError(f'{field_name} is required.')
    return text


def parse_int(value, field_name, minimum=1):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} must be a valid number.')
    if number < minimum:
        raise ValueError(f'{field_name} must be at least {minimum}.')
    return number


def number_of_pages_for_range(page_range, fallback=1):
    if page_range is None:
        return fallback
    text = str(page_range).strip()
    if not text:
        return fallback
    parts = [part.strip() for part in text.split(',') if part.strip()]
    pages = 0
    for part in parts:
        if '-' in part:
            start_text, end_text = part.split('-', 1)
            try:
                start = int(start_text)
                end = int(end_text)
            except ValueError:
                continue
            if end < start:
                start, end = end, start
            pages += max(0, end - start + 1)
        else:
            try:
                pages += int(part)
            except ValueError:
                continue
    return pages if pages > 0 else fallback


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user:
        return None
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'phone': user['phone'],
        'role': user['role'],
        'created_at': user['created_at'],
    }


def ensure_demo_admin():
    email = os.getenv('QUICKPRINT_ADMIN_EMAIL', 'admin@quickprintcampus.com')
    password = os.getenv('QUICKPRINT_ADMIN_PASSWORD', 'admin123')
    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if not existing:
        conn.execute(
            'INSERT INTO users (name, email, phone, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            ('QuickPrint Campus Admin', email, '9999999999', generate_password_hash(password), 'admin', iso_now()),
        )
        conn.commit()
    conn.close()


@app.before_request
def ensure_database_ready():
    init_db()


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'QuickPrint Campus API is running.'})


@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json(silent=True) or request.form
    try:
        name = normalize_text(data.get('name'), 'Full Name')
        email = normalize_text(data.get('email'), 'Email')
        phone = normalize_text(data.get('phone'), 'Phone number')
        password = normalize_text(data.get('password'), 'Password')
    except ValueError as exc:
        return error_response(str(exc), 400)

    if '@' not in email or '.' not in email:
        return error_response('Please enter a valid email address.', 400)
    if len(password) < 6:
        return error_response('Password must be at least 6 characters.', 400)

    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email.lower(),)).fetchone()
    if existing:
        conn.close()
        return error_response('An account with this email already exists.', 409)

    user_id = conn.execute(
        'INSERT INTO users (name, email, phone, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (name, email.lower(), phone, generate_password_hash(password), 'student', iso_now()),
    ).lastrowid
    conn.commit()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    session['user_id'] = user['id']
    session['role'] = user['role']
    session['user_name'] = user['name']
    return jsonify({
        'success': True,
        'message': 'Registration successful.',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone'],
            'role': user['role'],
        },
    })


@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json(silent=True) or request.form
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', '')).strip()

    if not email or not password:
        return error_response('Email and password are required.', 400)

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return error_response('Invalid email or password.', 401)

    session['user_id'] = user['id']
    session['role'] = user['role']
    session['user_name'] = user['name']
    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone'],
            'role': user['role'],
        },
    })


@app.route('/api/logout', methods=['POST'])
def logout_user():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


@app.route('/api/session', methods=['GET'])
def get_session():
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False})
    return jsonify({'authenticated': True, 'user': user})


@app.route('/api/interest', methods=['POST'])
def create_interest():
    data = request.get_json(silent=True) or request.form
    try:
        name = normalize_text(data.get('name'), 'Full Name')
        email = normalize_text(data.get('email'), 'Email')
        phone = normalize_text(data.get('phone'), 'Phone')
    except ValueError as exc:
        return error_response(str(exc), 400)

    if '@' not in email or '.' not in email:
        return error_response('Please enter a valid email address.', 400)

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO interest_list (name, email, phone, created_at) VALUES (?, ?, ?, ?)',
        (name, email.lower(), phone, iso_now()),
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Your interest has been recorded.'})


@app.route('/api/orders', methods=['POST'])
def create_order():
    user = get_current_user()
    if not user:
        return error_response('You must log in before placing an order.', 401)
    if user['role'] != 'student':
        return error_response('Only students can place orders.', 403)

    form_data = request.form
    file = request.files.get('file')
    if not file or file.filename == '':
        return error_response('Please upload a document.', 400)

    filename = secure_filename(file.filename)
    if not filename:
        return error_response('Please upload a valid document.', 400)

    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension not in ALLOWED_EXTENSIONS:
        return error_response('Unsupported file type. Please upload PDF, DOC, DOCX, JPG, JPEG, or PNG.', 400)

    if file.content_length and file.content_length > MAX_UPLOAD_SIZE:
        return error_response('File is too large. Please upload a file smaller than 10MB.', 400)

    try:
        copies = parse_int(form_data.get('copies'), 'Copies', 1)
        color_mode = normalize_text(form_data.get('color_mode'), 'Print type')
        page_range = form_data.get('page_range', '')
        paper_size = normalize_text(form_data.get('paper_size'), 'Paper size')
        pickup_date = normalize_text(form_data.get('pickup_date'), 'Pickup date')
        pickup_time = normalize_text(form_data.get('pickup_time'), 'Pickup time')
    except ValueError as exc:
        return error_response(str(exc), 400)

    page_count = number_of_pages_for_range(page_range, fallback=parse_int(form_data.get('page_count', '1'), 'Page count', 1))
    price_per_page = 5 if color_mode.lower() in ('color', 'colour') else 2
    total_amount = page_count * copies * price_per_page

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_path = UPLOAD_DIR / unique_name
    file.save(upload_path)

    order_number = f"QPC-{uuid.uuid4().hex[:6].upper()}"
    qr_token = uuid.uuid4().hex
    qr = qrcode.make(qr_token)
    qr_path = QR_DIR / f'{qr_token}.png'
    qr.save(qr_path)

    conn = get_db_connection()
    order_id = conn.execute(
        '''
        INSERT INTO orders
        (user_id, order_number, file_name, file_path, copies, color_mode, page_range, paper_size,
         pickup_date, pickup_time, total_amount, payment_status, order_status, qr_token, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            user['id'],
            order_number,
            filename,
            str(upload_path),
            copies,
            color_mode,
            page_range,
            paper_size,
            pickup_date,
            pickup_time,
            total_amount,
            'Pending',
            'Received',
            qr_token,
            iso_now(),
            iso_now(),
        ),
    ).lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Order created successfully.',
        'order': {
            'id': order_id,
            'order_number': order_number,
            'total_amount': total_amount,
            'payment_status': 'Pending',
            'order_status': 'Received',
            'qr_token': qr_token,
            'pickup_time': f'{pickup_date} {pickup_time}',
            'file_name': filename,
        },
    })


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    user = get_current_user()
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    if not order:
        return error_response('Order not found.', 404)
    if user and (user['role'] == 'admin' or order['user_id'] == user['id']):
        return jsonify({'order': dict(order)})
    return error_response('You do not have access to this order.', 403)


@app.route('/api/orders/user/<int:user_id>', methods=['GET'])
def get_orders_for_user(user_id):
    user = get_current_user()
    if not user:
        return error_response('Authentication required.', 401)
    if user['role'] != 'admin' and user['id'] != user_id:
        return error_response('You do not have access to these orders.', 403)

    conn = get_db_connection()
    rows = conn.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify({'orders': [dict(row) for row in rows]})


@app.route('/api/orders/<int:order_id>/pay', methods=['POST'])
def pay_for_order(order_id):
    user = get_current_user()
    if not user:
        return error_response('Authentication required.', 401)
    if user['role'] != 'student':
        return error_response('Only students can pay for orders.', 403)

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return error_response('Order not found.', 404)
    if order['user_id'] != user['id']:
        conn.close()
        return error_response('You do not have access to this order.', 403)
    if order['order_status'] == 'Cancelled':
        conn.close()
        return error_response('Cancelled orders cannot be paid.', 409)

    if order['payment_status'] != 'Paid':
        order_status = 'Payment Confirmed' if order['order_status'] == 'Received' else order['order_status']
        conn.execute(
            'UPDATE orders SET payment_status = ?, order_status = ?, updated_at = ? WHERE id = ?',
            ('Paid', order_status, iso_now(), order_id),
        )
        conn.commit()

    updated_order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    return jsonify({'success': True, 'order': dict(updated_order)})


@app.route('/api/admin/orders', methods=['GET'])
def get_all_orders_for_admin():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return error_response('Admin access required.', 403)

    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT o.*, u.name AS student_name, u.email AS student_email, u.phone AS student_phone
        FROM orders o
        LEFT JOIN users u ON u.id = o.user_id
        ORDER BY o.created_at DESC
        ''',
    ).fetchall()
    conn.close()
    return jsonify({'orders': [dict(row) for row in rows]})


@app.route('/api/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return error_response('Admin access required.', 403)

    data = request.get_json(silent=True) or request.form
    if not data:
        return error_response('No update data supplied.', 400)

    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not existing:
        conn.close()
        return error_response('Order not found.', 404)

    payment_status = data.get('payment_status', existing['payment_status'])
    order_status = data.get('order_status', existing['order_status'])

    if payment_status not in PAYMENT_STATUSES:
        conn.close()
        return error_response('Invalid payment status.', 400)
    if order_status not in ORDER_STATUSES:
        conn.close()
        return error_response('Invalid order status.', 400)

    if payment_status == 'Paid' and order_status == 'Received':
        order_status = 'Payment Confirmed'

    conn.execute(
        'UPDATE orders SET payment_status = ?, order_status = ?, updated_at = ? WHERE id = ?',
        (payment_status, order_status, iso_now(), order_id),
    )
    conn.commit()
    row = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    return jsonify({'success': True, 'order': dict(row)})


@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    user = get_current_user()
    if not user:
        return error_response('Authentication required.', 401)

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return error_response('Order not found.', 404)
    if user['role'] != 'admin' and order['user_id'] != user['id']:
        conn.close()
        return error_response('You do not have access to this order.', 403)

    conn.execute(
        'UPDATE orders SET payment_status = ?, order_status = ?, updated_at = ? WHERE id = ?',
        ('Cancelled', 'Cancelled', iso_now(), order_id),
    )
    conn.commit()
    updated = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    return jsonify({'success': True, 'order': dict(updated)})


@app.route('/api/orders/<int:order_id>/qr', methods=['GET'])
def get_order_qr(order_id):
    user = get_current_user()
    if not user:
        return error_response('Authentication required.', 401)

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    if not order:
        return error_response('Order not found.', 404)

    if user['role'] != 'admin' and order['user_id'] != user['id']:
        return error_response('You do not have access to this QR code.', 403)

    qr_file = QR_DIR / f"{order['qr_token']}.png"
    if not qr_file.exists():
        return error_response('QR code is unavailable for this order.', 404)
    return send_file(qr_file, mimetype='image/png')


@app.route('/')
def index_page():
    return send_file(BASE_DIR / 'index.html')


@app.route('/index.html')
def index_html():
    return send_file(BASE_DIR / 'index.html')


@app.route('/interest.html')
def interest_html():
    return send_file(BASE_DIR / 'interest.html')


@app.route('/success.html')
def success_html():
    return send_file(BASE_DIR / 'success.html')


@app.route('/login.html')
def login_html():
    return send_file(BASE_DIR / 'login.html')


@app.route('/register.html')
def register_html():
    return send_file(BASE_DIR / 'register.html')


@app.route('/order.html')
def order_html():
    return send_file(BASE_DIR / 'order.html')


@app.route('/student-dashboard.html')
def student_dashboard_html():
    return send_file(BASE_DIR / 'student-dashboard.html')


@app.route('/admin-dashboard.html')
def admin_dashboard_html():
    return send_file(BASE_DIR / 'admin-dashboard.html')


init_db()
ensure_demo_admin()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
