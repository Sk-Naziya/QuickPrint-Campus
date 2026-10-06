ALLOWED_EXTENSIONS = {
    'pdf',
    'doc',
    'docx',
    'jpg',
    'jpeg',
    'png',
}

ORDER_STATUSES = [
    'Received',
    'Payment Confirmed',
    'Printing',
    'Ready for Pickup',
    'Collected',
    'Cancelled',
]

PAYMENT_STATUSES = ['Pending', 'Paid', 'Failed', 'Cancelled']

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
