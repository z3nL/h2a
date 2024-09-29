from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from waitress import serve
import MySQLdb.cursors
import os
import openai
from dotenv import load_dotenv
import ast
import asyncio
import datetime

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key
app = Flask(__name__)

@app.route('/')
def home():
    return redirect(url_for('loginpg'))

@app.route('/H2ABank/login')
def loginpg():
    return render_template('/H2ABank/login.html')

@app.route('/H2ABank/loggedin')
async def loggedinpg():
    if 'transactions' in session:
        transactions = session['transactions']
        acc_num = session['acc_num']
        suspicious_transactions = session['suspicious_transactions']
        explanation = session['explanation']
    
    if request.referrer and (request.referrer.endswith('/H2ABank/login')  or request.referrer.endswith('/H2ABank/transactions')  or request.referrer.endswith('/H2ABank/settings')or (request.referrer.endswith('/H2ABank/loggedin'))):
        return render_template('/H2ABank/loggedin.html', transactions=transactions, suspicious_transactions=list(suspicious_transactions), explanation=explanation)
    else:
        return redirect(url_for('loginpg'))  # Redirect to the login page

@app.route('/H2ABank/settings')
async def settingspg():
    if 'username' in session:
        username = session['username']
        acc_num = session['acc_num']
        address = session['address']
        
    if request.referrer and (request.referrer.endswith('/H2ABank/loggedin') or request.referrer.endswith('/H2ABank/transactions') or (request.referrer.endswith('/H2ABank/login')) or (request.referrer.endswith('/H2ABank/settings'))):
        return render_template('/H2ABank/settings.html', username=username, acc_num=acc_num, address=address)
    else:
        return redirect(url_for('loggedinpg')) 

@app.route('/H2ABank/transactions', methods=['GET', 'POST'])
@app.route('/H2ABank/transactions', methods=['GET', 'POST'])
async def transactionspg():
    if request.method == 'POST':
        if 'username' in session:
            acc_num = session['acc_num']
            transactionAmt = request.form.get('transaction_amount')
            current_time = datetime.datetime.now()
            transactionTime = f"{current_time.hour:02}:{current_time.minute:02}"
            transactionDate = f"{current_time.year}-{current_time.month}-{current_time.day}"
            transactionRecipient = request.form.get('transaction_recipient')
            transactionLoc = request.form.get('transaction_location')
            print(f"---\nHELLO : {acc_num} {transactionAmt} {transactionTime} {transactionDate} {transactionRecipient} {transactionLoc}\n---\n")
            
            insCursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            insCursor.execute("SELECT MAX(`id`) FROM `transaction tables`")
            maxID = insCursor.fetchone()['MAX(`id`)']
            
            insCursor.execute(
                "INSERT INTO `transaction tables` (`Account Number`, `Transaction Amount`, `Time of Transaction`, `Date Of Transaction`, `Transaction Recipient`, `Transaction Location`, `id`) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (acc_num, transactionAmt, transactionTime, transactionDate, transactionRecipient, transactionLoc, maxID + 1,)
            )
            mysql.connection.commit()
            
            insCursor.execute('Select * FROM `transaction tables` WHERE `Account Number` = %s ORDER BY `Date Of Transaction` DESC, `Time of Transaction` DESC', (acc_num,))
            session['transactions'] = insCursor.fetchall()
            
            # Add the suspicious_transactions or [] check here
            explanation, suspicious_transactions = await checkSuspicious(acc_num)
            session['suspicious_transactions'] = suspicious_transactions or []  # Ensure it's always a list

    if request.referrer and (request.referrer.endswith('/H2ABank/loggedin') or request.referrer.endswith('/H2ABank/settings') or (request.referrer.endswith('/H2ABank/login')) or (request.referrer.endswith('/H2ABank/transactions'))):
        return render_template('/H2ABank/transactions.html')
    else:
        return redirect(url_for('loggedinpg'))

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'userid'
mysql = MySQL(app)

# Get the variables for the login
@app.route('/H2ABank/login', methods=['POST'])
@app.route('/H2ABank/login', methods=['POST'])
async def signIn():
    username = request.form['username']
    password = request.form['password']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM logininfo WHERE Username = %s', (username,))
    account = cursor.fetchone()

    # Check if the account exists
    if account:
        # Compare the password with the stored password (assuming plaintext; consider hashing)
        if account['Password'] == password:
            session['username'] = username
            acc_num = account['Acc Number']
            session['acc_num'] = acc_num
            session['address'] = account['Address']
            
            cursor.execute('Select * FROM `transaction tables` WHERE `Account Number` = %s ORDER BY `Date Of Transaction` DESC, `Time of Transaction` DESC', (acc_num,))
            transactions = cursor.fetchall()
            session['transactions'] = transactions
            
            # Add the suspicious_transactions or [] check here
            explanation, suspicious_transactions = await checkSuspicious(acc_num)
            session['explanation'] = explanation
            session['suspicious_transactions'] = suspicious_transactions or []  # Ensure it's always a list
            
            return redirect(url_for('loggedinpg'))
        else:
            flash('Incorrect password!', 'error')
    else:
        flash('Username not found!', 'error')
    
    return render_template('/H2ABank/login.html')


async def checkSuspicious(acc_number):
    tempCursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    tempCursor.execute('SELECT * FROM `transaction tables` WHERE `Account Number` = %s', (acc_number,))
    currentTransactions = tempCursor.fetchall()
    transactions_str = str(currentTransactions)

    # Call OpenAI's API asynchronously
    completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are checking if the new transaction being added is considered suspicious. Suspicious transactions include instances where the transaction is over 10000 dollars, significantly above or below the average (200%), in a far away location from other transactions, irregular from account patterns, or completely out of line with typical market price. "
                    "Ensure that comparisons are made only between transactions within the same account number."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Given a dataset {transactions_str}, first provide an explanation of the suspicious transactions. Then, on a separate line, "
                    "return only a Python list of the suspicious transaction IDs in this format: [1, 2, 3]. Ensure that the list is printed on one line, not one integer per line."
                )
            }
        ]
    )

    response_content = completion['choices'][0]['message']['content']

    # Debugging: Print the raw response from OpenAI
    print("Raw OpenAI Response:", response_content)

    # Process the response carefully to extract the list of suspicious transactions
    try:
        # Look for the last occurrence of "List of suspicious transactions:"
        list_start = response_content.rfind("[")
        list_end = response_content.rfind("]") + 1
        list_str = response_content[list_start:list_end].strip()

        print(f"Extracted list string: {list_str}")

        # Ensure we got a valid list, then evaluate
        if list_start != -1 and list_end != -1:
            suspicious_transactions = ast.literal_eval(list_str)
        else:
            suspicious_transactions = []

        # Ensure the result is always a list, even if it's a single transaction or none
        if not isinstance(suspicious_transactions, list):
            suspicious_transactions = [suspicious_transactions]

    except (ValueError, SyntaxError) as e:
        print("Error in parsing suspicious transactions:", e)
        suspicious_transactions = []

    # Final list of suspicious transactions
    print("\nList of suspicious transactions:")
    print(suspicious_transactions)

    return response_content, suspicious_transactions

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    serve(app, host="0.0.0.0", port=8000)
