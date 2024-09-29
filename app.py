from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from waitress import serve
import MySQLdb.cursors
import os
 
app = Flask(__name__)
@app.route('/')

@app.route('/H2ABank/login')
def loginpg():
    return render_template('/H2ABank/login.html')

@app.route('/H2ABank/loggedin')
def loggedinpg():
    if 'transactions' in session:
        transactions = session['transactions']
    
    if request.referrer and (request.referrer.endswith('/H2ABank/login')  or request.referrer.endswith('/H2ABank/transactions')  or request.referrer.endswith('/H2ABank/settings')or (request.referrer.endswith('/H2ABank/loggedin'))):
        return render_template('/H2ABank/loggedin.html', transactions=transactions)
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

@app.route('/H2ABank/transactions')
def transactionspg():
    if request.method == 'POST':
            if 'username' in session:
                acc_num = session['acc_num']
                transactionAmt = request.form.get('transaction_amount')
                transactionTime = request.form.get('transaction_time')
                transactionRecipient = request.form.get('transaction_recipient')
                transactionLoc = request.form.get('transaction_location')
                transactionDate = request.form.get('recipient')
                print(f"{acc_num} {transactionAmt} {transactionTime} {transactionDate} {transactionRecipient} {transactionLoc}")
            #code to import it to SQL database
            #checkNewSus(acc_number, transaction_amt, transaction_time, transaction_recepient, transaction_loc):
            
        
    
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
            return redirect(url_for('loggedinpg'))
        else:
            flash('Incorrect password!', 'error')
    else:
        flash('Username not found!', 'error')
    return render_template('/H2ABank/login.html')
    
    
    

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    serve(app, host = "0.0.0.0", port = 8000)