from flask import Flask, render_template, request, redirect, url_for, session

import ibm_db

import sendgrid
import os
from sendgrid.helpers.mail import *

SENDGRID_Key = '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'

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=b1bc1829-6f45-4cd4-bef4-10cf081900bf.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32304;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=nkn33411;PWD=gkg3heE9dS3r0MMJ",'','')

app = Flask(__name__)
app.secret_key = 'a'


@app.route("/",methods=['GET'])
def home():
  if 'email' not in session:
    return redirect(url_for('login'))
  return render_template('home.html',name='Home')


@app.route("/about",methods=['GET'])
def about():
  return render_template('about.html')

@app.route("/register",methods=['GET','POST'])
def register():
  if request.method == 'POST':
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    if not email or not username or not password:
      return render_template('register.html',error='Please fill all fields')
    
    #hash=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

    query = "SELECT * FROM USERS WHERE Email=?"
    stmt = ibm_db.prepare(conn, query)
    ibm_db.bind_param(stmt,1,email)
    ibm_db.execute(stmt)
    isUser = ibm_db.fetch_assoc(stmt)
    
    if not isUser:
      insert_sql = "INSERT INTO Users(Name,email,PASSWORD) VALUES (?,?,?)"
      prep_stmt = ibm_db.prepare(conn, insert_sql)
      ibm_db.bind_param(prep_stmt, 1, username)
      ibm_db.bind_param(prep_stmt, 2, email)
      ibm_db.bind_param(prep_stmt, 3, password)
      ibm_db.execute(prep_stmt)
      return render_template('register.html',success="You can login")
    else:
      return render_template('register.html',error='Invalid Credentials')

  return render_template('register.html',name='Home')

@app.route("/login",methods=['GET','POST'])
def login():
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']

    if not email or not password:
      return render_template('login.html',error='Please fill all fields')
    query = "SELECT * FROM USERS WHERE Email=?"
    stmt = ibm_db.prepare(conn, query)
    ibm_db.bind_param(stmt,1,email)
    ibm_db.execute(stmt)
    isUser = ibm_db.fetch_assoc(stmt)
    print(isUser,password)

    if not isUser:
      return render_template('login.html',error='Invalid Credentials')
      
    #isPasswordMatch = bcrypt.checkpw(password.encode('utf-8'),isUser['PASSWORD'].encode('utf-8'))

    #if not isPasswordMatch:
    if(isUser['PASSWORD']!=password):
      return render_template('login.html',error='Invalid Credentials')

    session['email'] = isUser['EMAIL']
    return redirect(url_for('home'))

  return render_template('login.html',name='Home')


@app.route('/logout')
def logout():
  session.pop('email', None)
  return redirect(url_for('login'))


sg = sendgrid.SendGridAPIClient('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')
from_email = Email("plasmadonoribm@gmail.com")


@app.route('/request',methods=['GET','POST'])
def req():
  if request.method == 'GET':
    return render_template('request.html',name='request')
  email = request.form['email']
  name = request.form['Name']
  phone = request.form['phone']
  BloodGroupReq = request.form['BloodGroupReq']
  Address = request.form['Address']
  #to_email = To(email)
  print(email,name,phone,BloodGroupReq,Address)
  query = "SELECT * FROM DONORS WHERE BloodGroup=?"
  stmt = ibm_db.prepare(conn, query)
  ibm_db.bind_param(stmt,1,BloodGroupReq)
  ibm_db.execute(stmt)
  ll = ibm_db.fetch_assoc(stmt)
  if(ll):
    listt = []
    while(ll!=False):
      listt.append(ll)
      ll = ibm_db.fetch_assoc(stmt)
    print(listt)
    
    for i in listt:
      to_email = To(i['EMAIL'])
      subject = "REQUEST FOR BLOOD DONATION"
      content = Content("text/plain", "{} requests plasma donation and has the same blood group {} as you.\nIf you wish to really donate the blood, please contact them at the email {}.\nThank you.".format(name,BloodGroupReq,email))
      mail = Mail(from_email, to_email, subject, content)
      response = sg.client.mail.send.post(request_body=mail.get())
      print(response.status_code)
      print(response.body)
      print(response.headers)
    	
    return render_template('reqReplyS.html',name='reqReplyS',total=len(listt))
  else:  
    return render_template('reqReplyF.html',name='reqReplyF')


@app.route('/donate',methods=['GET','POST'])
def donate():
  if request.method == 'GET':
    return render_template('donate.html',name='donate')
  email = request.form['email']
  name = request.form['Name']
  phone = request.form['phone']
  BloodGroup = request.form['BloodGroup']
  Address = request.form['Address']
  print(email,name,phone,BloodGroup,Address)
  insert_sql = "INSERT INTO DONORS(Name,email,Number,BloodGroup,Address) VALUES (?,?,?,?,?)"
  prep_stmt = ibm_db.prepare(conn, insert_sql)
  ibm_db.bind_param(prep_stmt, 1, name)
  ibm_db.bind_param(prep_stmt, 2, email)
  ibm_db.bind_param(prep_stmt, 3, phone)
  ibm_db.bind_param(prep_stmt, 4, BloodGroup)
  ibm_db.bind_param(prep_stmt, 5, Address)
  ibm_db.execute(prep_stmt)
  return render_template('donSuccess.html',name='donSuccess')

@app.route('/stats',methods=['GET','POST'])
def stats():
  if request.method == 'GET':
    return render_template('stats.html',total=0,flag=1)
  email = request.form['email']
  query = "SELECT * FROM DONORS WHERE email=?"
  stmt = ibm_db.prepare(conn, query)
  ibm_db.bind_param(stmt,1,email)
  ibm_db.execute(stmt)
  ll = ibm_db.fetch_assoc(stmt)
  listt = []
  if(ll):
    while(ll!=False):
      listt.append(ll)
      ll = ibm_db.fetch_assoc(stmt)
    print(listt)
  return render_template('stats.html',total=len(listt),flag=0)
  
if __name__ == "__main__":
  app.run(host="0.0.0.0")
