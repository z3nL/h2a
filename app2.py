from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from waitress import serve
import MySQLdb.cursors
import openai
from dotenv import load_dotenv
import os
import ast

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
    if request.referrer and (request.referrer.endswith('/H2ABank/login')  or request.referrer.endswith('/H2ABank/transactions')  or request.referrer.endswith('/H2ABank/settings')or (request.referrer.endswith('/H2ABank/loggedin'))):
        return render_template('/H2ABank/loggedin.html')
    else:
        return redirect(url_for('loginpg'))  # Redirect to the login page

@app.route('/H2ABank/settings')
def settingspg():
    if request.referrer and (request.referrer.endswith('/H2ABank/loggedin') or request.referrer.endswith('/H2ABank/transactions') or (request.referrer.endswith('/H2ABank/login') ) or (request.referrer.endswith('/H2ABank/settings'))):
        return render_template('/H2ABank/settings.html')
    else:
        return redirect(url_for('loggedinpg')) 

@app.route('/H2ABank/transactions')
def transactionspg():
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
            acc_number = account['Acc Number']
            address = account['Address']
            print(checkSuspicious(acc_number))
            print(f'successful:  {password}  {username}  {acc_number}  {address}')
                # Successfully authenticated
            return render_template('/H2ABank/loggedin.html')
        else:
            flash('Incorrect password!', 'error')
    else:
        flash('Username not found!', 'error')
    return render_template('/H2ABank/login.html')

    
    # At this point, check if the username is equal to something in SQL 
    # base and then verify that the password is equal, otherwise cause 
    # error message
    
    
    #import the other dataset


    
    
def checkSuspicious(acc_number):
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
                            "Other instances of suspicious transactions include seemingly unknown recipients as well as odd times for transactions to take place. Keep in mind to only compare "
                            "patterns that share the same account number. Please only return transaction IDs.")
            },
            {
                "role": "user", 
                "content": (f"Given a dataset {transactions_str}, first provide an explanation of the suspicious transactions. Then, on a separate line, "
                            "return only a Python list of the suspicious transaction IDs. Ensure the list starts on a new line with no additional text.")
            }
        ]
    )
    currentTransactions = completion['choices'][0]['message']['content']
    explanation, list_str = currentTransactions.rsplit("\n", 1)
    suspicious_transactions = ast.literal_eval(list_str.strip())
    print("Explanation:")
    print(explanation)

    print("\nList of suspicious transactions:")
    print(suspicious_transactions)
    return currentTransactions
def checkNewSus(acc_num, transaction_amt, transaction_time, transaction_recepient, transaction_loc):
    tempCursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    tempCursor.execute('SELECT * FROM `transaction tables` WHERE `Account Number`  = %s', (acc_number,))
    currentTransactions = tempCursor.fetchall()
    transactions_str = str(currentTransactions)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": ("You are checking if the new transaction being added is considered suspicious. Suspicious entails far distance in location from other transactions, "
                            "significantly larger amounts being added or subtracted, or irregular transactions that oppose account patterns. "
                            "Other instances of suspicious transactions include seemingly unknown recipients as well as odd times for transactions to take place. Keep in mind to only compare "
                            "patterns that share the same account number. Please only return transaction IDs.")
            },
            {
                "role": "user", 
                "content": (f"Given a dataset {transactions_str}, as well as the information {acc_num}, {transaction_amt}, {transaction_time}, {transaction_recepient}, and {transaction_loc}, compare it to other transactions and determine if the transaction is suspicious. Only return a yes or no answer, followed by an explaination why.")
                           
            }
        ]
    )
    return completion

    
if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    serve(app, host = "0.0.0.0", port = 8000) 