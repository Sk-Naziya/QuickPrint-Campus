# QuickPrint Campus

QuickPrint Campus is a working prototype for a campus print-order platform. The frontend keeps the original landing-page design, and the backend adds student login, document upload, order creation, payment simulation, QR generation, and an admin dashboard.

## Features

- Landing page with the existing QuickPrint Campus branding
- Student registration and login
- Document upload with file validation and local storage
- Order pricing and pickup scheduling
- Simulated payment flow with demo payment label
- QR code generation for pickup
- Admin dashboard to update order status
- Interest-list submission saved in SQLite

## Requirements

- Python 3.10+
- Flask
- qrcode
- Pillow

## Setup

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Then install dependencies:

```bash
pip install -r backend/requirements.txt
```

Start the app:

```bash
python backend/app.py
```

The app runs at:

- http://localhost:5000/
- http://localhost:5000/index.html

## Default Admin Account

A demo admin account is created automatically if it does not exist.

- Email: admin@quickprintcampus.com
- Password: admin123

This is intended for local demo use only. For a production-style setup, set your own password using environment variables:

```bash
set QUICKPRINT_ADMIN_EMAIL=admin@quickprintcampus.com
set QUICKPRINT_ADMIN_PASSWORD=your_secure_password
python backend/app.py
```

## How to test the flow

1. Open http://localhost:5000/register.html
2. Create a student account
3. Log in and open http://localhost:5000/order.html
4. Upload a file, choose settings, and place the order
5. Click Demo Payment to mark the order as paid
6. View the generated QR code from the student dashboard
7. Log in as admin at http://localhost:5000/admin-dashboard.html
8. Update order status from Received to Printing, Ready for Pickup, or Collected

## Technical notes

- The database is SQLite and lives in `backend/quickprint.db`
- Uploaded files are stored in `backend/uploads/`
- QR codes are stored in `backend/generated_qr/`
- The front end communicates with the backend using `fetch()` and REST endpoints
- Sensitive user information is not stored in the QR code
