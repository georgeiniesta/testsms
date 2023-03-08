from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import mysql.connector
from twilio.rest import Client
import time
import os

app = Flask(__name__)

# MySQL database configuration
db_config = {
    'user': 'your_mysql_username',
    'password': 'your_mysql_password',
    'host': 'your_mysql_host',
    'database': 'your_mysql_database'
}


# Retrieve Twilio account information from environment variables
account_sid = os.environ['twilio_account_sid']
auth_token = os.environ['twilio_auth_token']
phone_number = os.environ['twilio_phone_number']
to_number = os.environ['twilio_to_phone_number']

# Create Twilio client
#client = Client(account_sid, auth_token)
# Twilio configuration
#twilio_account_sid = 'your_twilio_account_sid'
#twilio_auth_token = 'your_twilio_auth_token'
#twilio_phone_number = 'your_twilio_phone_number'
# Function to send an SMS message using Twilio

def send_sms(to_number, message):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message,
        from_=phone_number,
        to=to_number
    )
    print(f'Sent SMS to {to_number}: {message.sid}')

# Function to update the order status in the database
def update_order_status(order_number, status):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        update_query = "UPDATE orders SET status = %s WHERE order_number = %s"
        cursor.execute(update_query, (status, order_number))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f'Error updating order status: {e}')
        return False

# Function to handle incoming SMS messages
def handle_sms():
    from_number = request.form['From']
    body = None
    start_time = time.time()
    resp = MessagingResponse()

    # Wait for a message from the client, or abort after 50 seconds
    while not body and time.time() - start_time < 50:
        body = request.form.get('Body')
        time.sleep(1)

    if not body:
        resp.message('No response received')
        return str(resp)

    # Check if the message is in the correct format for updating an order status
    if body.startswith('UPDATE ORDER ') and ' TO ' in body:
        order_number = body.split(' ')[2]
        new_status = body.split('TO ')[1]
        if update_order_status(order_number, new_status):
            # If the order status was successfully updated, send an SMS message
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            select_query = "SELECT phone_number FROM orders WHERE order_number = %s"
            cursor.execute(select_query, (order_number,))
            row = cursor.fetchone()
            if row:
                to_number = row[0]
                message = f'Your order {order_number} has been updated to {new_status}'
                send_sms(to_number, message)
            cursor.close()
            conn.close()
            resp.message('Order status updated successfully')
        else:
            resp.message('Error updating order status')
    else:
        resp.message('Invalid message format')

    return str(resp)

# Route to handle incoming SMS messages
@app.route('/sms', methods=['POST'])
def receive_sms():
    return handle_sms()

if __name__ == '__main__':
    app.run(debug=True)