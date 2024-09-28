from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from waitress import serve
 
app = Flask(__name__)
@app.route('/')

@app.route('/H2ABank/login')
def loginpg():
    return render_template('/H2ABank/login.html')

@app.route('/H2ABank/loggedin')
def loggedinpg():
    return render_template('/H2ABank/loggedin.html')

@app.route('/H2ABank/settings')
def settingspg():
    return render_template('/H2ABank/settings.html')

@app.route('/H2ABank/transactions')
def transactionspg():
    return render_template('/H2ABank/transactions.html')


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
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM logininfo WHERE Username = %s', (username,))
    account = cursor.fetchone()
        
        # Check if the account exists
    if account:
            # Compare the password with the stored password (assuming plaintext; consider hashing)
        if account['Password'] == password:
            print('successful' + password + username)
                # Successfully authenticated
            session['username'] = username
            return 'Logged in successfully!'
        else:
                return 'Incorrect password!'
    else:
        return 'Username not found!'
    return render_template('/H2ABank/loggedin.html')
    
    # At this point, check if the username is equal to something in SQL 
    # base and then verify that the password is equal, otherwise cause 
    # error message
    
    
    

if __name__ == "__main__":
    serve(app, host = "0.0.0.0", port = 8000)