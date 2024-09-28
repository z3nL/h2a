from flask import Flask,render_template, request
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

# Get the variables for the the the the login
@app.route('/H2ABank/login',methods=['POST'])
def signIn():
    username = request.form['username']
    password = request.form['password']
    print(f"Username: {username}, Password: {password}")
    
    
    # At this point, check if the username is equal to something in SQL 
    # base and then verify that the password is equal, otherwise cause 
    # error message
    
    
    

'''

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask'

mysql = MySQL(app)
 
#Creating a connection cursor
cursor = mysql.connection.cursor()
 
#Executing SQL Statements
cursor.execute(CREATE TABLE table_name(field1, field2...) )
cursor.execute( INSERT INTO table_name VALUES(v1,v2...) )
cursor.execute( DELETE FROM table_name WHERE condition )
 
#Saving the Actions performed on the DB
mysql.connection.commit()
 
#Closing the cursor
cursor.close()
'''

if __name__ == "__main__":
    serve(app, host = "0.0.0.0", port = 8000)