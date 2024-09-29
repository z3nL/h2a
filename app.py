from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from waitress import serve
import MySQLdb.cursors
import os
import openai
from dotenv import load_dotenv
import ast
import datetime

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key
app = Flask(__name__)
@app.route('/')

@app.route('/H2ABank/login')
def loginpg():
    return render_template('/H2ABank/login.html')

@app.route('/H2ABank/loggedin')
def loggedinpg():
    if 'transactions' in session:
        transactions = session['transactions']
        acc_num = session['acc_num']
        suspicious_transactions = checkSuspicious(acc_num)
    
    if request.referrer and (request.referrer.endswith('/H2ABank/login')  or request.referrer.endswith('/H2ABank/transactions')  or request.referrer.endswith('/H2ABank/settings')or (request.referrer.endswith('/H2ABank/loggedin'))):
        return render_template('/H2ABank/loggedin.html', transactions=transactions,  suspicious_transactions=suspicious_transactions)
    else:
        return redirect(url_for('loginpg'))  # Redirect to the login page

@app.route('/H2ABank/settings')
def settingspg():
    if 'username' in session:
        username = session['username']
        acc_num = session['acc_num']
        address = session['address']
        
    if request.referrer and (request.referrer.endswith('/H2ABank/loggedin') or request.referrer.endswith('/H2ABank/transactions') or (request.referrer.endswith('/H2ABank/login') ) or (request.referrer.endswith('/H2ABank/settings'))):
        return render_template('/H2ABank/settings.html', username=username, acc_num=acc_num, address=address)
    else:
        return redirect(url_for('loggedinpg')) 

@app.route('/H2ABank/transactions', methods=['GET', 'POST'])
def transactionspg():
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
                insCursor.execute("SELECT MAX(`Transaction Amount`) FROM `transaction tables`")
                maxID = insCursor.fetchone()['MAX(`Transaction Amount`)']
                insCursor.execute (
                    "INSERT INTO `transaction tables` (`Account Number`, `Transaction Amount`, `Time of Transaction`, `Date Of Transaction`, `Transaction Recipient`, `Transaction Location`, `id`) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (acc_num, transactionAmt, transactionTime, transactionDate, transactionRecipient, transactionLoc, maxID+1,)
                )
                mysql.connection.commit()
                #checkNewSus(acc_num, transactionAmt, transactionTime, transactionDate, transactionRecipient, transactionLoc):
        
    
    if request.referrer and (request.referrer.endswith('/H2ABank/loggedin') or request.referrer.endswith('/H2ABank/settings') or (request.referrer.endswith('/H2ABank/login') )or (request.referrer.endswith('/H2ABank/transactions'))):
        return render_template('/H2ABank/transactions.html')
    else:
        return redirect(url_for('loggedinpg'))


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'userid'
mysql = MySQL(app)


# Get the variables for the the the the login
@app.route('/H2ABank/login',methods=['POST'])
def signIn():
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
            cursor.execute('Select * FROM `transaction tables` WHERE `Account Number` = %s', (acc_num,))
            transactions = cursor.fetchall()
            session['transactions'] = transactions
            print(checkSuspicious(acc_num))
            return redirect(url_for('loggedinpg'))
        else:
            flash('Incorrect password!', 'error')
    else:
        flash('Username not found!', 'error')
    return render_template('/H2ABank/login.html')
    

def checkSuspicious(acc_number):
    tempCursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    tempCursor.execute('SELECT * FROM `transaction tables` WHERE `Account Number` = %s', (acc_number,))
    currentTransactions = tempCursor.fetchall()
    transactions_str = str(currentTransactions)

    # Call OpenAI's API for detecting suspicious transactions
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are looking for suspicious transactions. Suspicious entails far distance in location from other transactions, "
                    "significantly larger amounts being added or subtracted, or irregular transactions that oppose account patterns. "
                    "Other instances of suspicious transactions include seemingly unknown recipients as well as odd times for transactions to take place. "
                    "Keep in mind to only compare patterns that share the same account number. There are also possibilities to travel and leave the original account location. "
                    "These can be recognized by consistent transactions at similar locations. "
                    "Keep in mind that even though those transactions might have similar locations, large numbers are still suspicious. "
                    "For example, if an average transaction is for less than 1000 dollars, anything much more than the average can be seen as suspicious, "
                    "excluding outliers from the average. Similarly, if a transaction is only made one time at a far away location, "
                    "it can be seen as suspicious. Please only return transaction IDs."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Given a dataset {transactions_str}, first provide an explanation of the suspicious transactions. Then, on a separate line, "
                    "return only a Python list of the suspicious transaction IDs. Ensure the list starts on a new line with no additional text."
                )
            }
        ]
    )

    # Extracting the response content
    response_content = completion['choices'][0]['message']['content']

    # Attempt to split based on a specific marker for separating explanation from list
    try:
        explanation, list_str = response_content.rsplit("\n", 1)  # Split by the last newline
        suspicious_transactions = ast.literal_eval(list_str.strip())  # Convert the string to a Python list
    except (ValueError, SyntaxError) as e:
        print("Error in parsing suspicious transactions:", e)
        suspicious_transactions = []

    print("Explanation:")
    print(explanation)

    print("\nList of suspicious transactions:")
    print(suspicious_transactions)

    return suspicious_transactions


def checkNewSus(acc_number, transaction_amt, transaction_time, transaction_recepient, transaction_loc):
    tempCursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    tempCursor.execute('SELECT * FROM `transaction tables` WHERE `Account Number`  = %s', (acc_number,))
    currentTransactions = tempCursor.fetchall()
    transactions_str = str(currentTransactions)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": ("You are looking for suspicious transactions. Suspicious entails far distance in location from other transactions, "
                            "significantly larger amounts being added or subtracted, or irregular transactions that oppose account patterns. "
                            "Other instances of suspicious transactions include seemingly unknown recipients as well as odd times for transactions "
                            "to take place. Keep in mind to only compare "
                            "patterns that share the same account number. There are also possibilities to travel, and leave the original account location. "
                            "These can be recognized by consistent transactions at similar locations."
                            "Keep in mind that even though those transactions might have similar locations, large numbers are still suspicious."
                            "For example, if an average transaction is for less than 1000 dollars, anything much more than the average can be seen as suspicios"
                            "excluding outliers from the average. Similarly, if a transaction is only made one time at a far away location"
                            "it can be seen as suspicious. Please only return transaction IDs.")
            },
            {
                "role": "user", 
                "content": (f"Given a dataset {transactions_str}, as well as the information {acc_number}, {transaction_amt}, {transaction_time}, {transaction_recepient}, and {transaction_loc}, compare it to other transactions and determine if the transaction is suspicious. Only return a yes or no answer, followed by an explaination why.")
                           
            }
        ]
    )
    return completion
    

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    serve(app, host = "0.0.0.0", port = 8000)