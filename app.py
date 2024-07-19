from flask import Flask, render_template, redirect, url_for, request,jsonify, flash
from pymongo import MongoClient
import os
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bson import ObjectId
from datetime import datetime
from flask_mail import Mail 
from flask_mail import Message


mail= Mail()
app = Flask(__name__)
mail.init_app(app)
app.config['SECRET_KEY'] = 'your_secret_key'
client = MongoClient('mongodb://127.0.0.1:27017')

app.config['DEBUG'] = True
db = client['Solvathon']
app.config['UPLOAD_FOLDER'] = 'static/docs'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc','docx'}
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'shaikhminhazuddingcsj@gmail.com'
app.config['MAIL_PASSWORD'] = 'Minhaz07'
app.config['MAIL_DEFAULT_SENDER'] = 'shaikhminhazuddingcsj@gmail.com'
app.config['MAIL_DEBUG'] = True

# app.config['MAIL_SUPPRESS_SEND'] = False  # Set to True to suppress emails in development

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.password = user_data['password']
        self.role = user_data['role']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

@app.route('/')
def home():
    print(current_user.is_authenticated)
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('teacher_dashboard'))
        if current_user.role == 'student':
            return redirect(url_for('studentDashboard'))
        if current_user.role == 'warden':
            return "Warden Dashboard"
        if current_user.role == 'maintenance':
            return redirect(url_for("maintenanceDept"))
        return f'Hello, {current_user.username}!'

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)
        user_data = db.users.find_one({'username': username, 'password': password})
        print(user_data)
        if user_data:
            user = User(user_data)
            print(user)
            print(current_user.is_authenticated)
            login_user(user)
            print(current_user.is_authenticated)
            return redirect(url_for('home'))

    return render_template('index.html')

@app.route('/FacultyDashboard')
@login_required
def teacher_dashboard():
    return render_template("teacher_dashboard.html")

@app.route('/FacultyNotice')
@login_required
def teacher_notice():
    notice = db.notice.find()
    notice_list = list(notice)
    
    for notices in notice_list:
        notices['_id'] = str(notices['_id'])
    print(notice_list)

    return render_template('teacher_notice.html', notice_list= notice_list)

@app.route('/newNotice')
def newNotice():
    return render_template('create_notice.html')

@app.route("/updateNotice",methods= ['POST'])
def updateNotice():
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    notice = db.notice

    file  = request.files['myfile']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    notice_data = {
        'title' : request.form.get('title'),
        'desc' : request.form.get('desc'),
        'uploadTime' : current_datetime_str,
        'facultyName': current_user.username,
        'targetAudience': request.form.get('program'),
        'docName': filename,
    }
    notice.insert_one(notice_data)
    return redirect(url_for('teacher_notice'))
@app.route('/deleteItem/<itemName>')
def deleteItem(itemName):
    notice = db.notice
    deleteItem = notice.delete_one({'title' : itemName})
    if deleteItem:
        print("Deleted")
    else:
        print("Not Deleted")
    return redirect(url_for('teacher_notice'))
#---------------------------------Student Part-----------------------------------------
@app.route('/studentDashboard', methods = ['GET', 'POST'])
def studentDashboard():
    return render_template('student_dashboard.html')

@app.route('/studentNotice', methods=['GET'])
def student_notice():
    notice = db.notice.find()
    notice_list = list(notice)
    
    for notices in notice_list:
        notices['_id'] = str(notices['_id'])

    return render_template('student_notice.html', notice_list= notice_list)

@app.route("/studentComplain",methods=['POST','GET'])
def studentComplain():
    complains = db.complain.find({'name': current_user.username})
    complains_list = list(complains)
    print(complains_list)
    for comp in complains_list:
        comp['_id'] = str(comp['_id'])
    # print(jsonify(complains_list))
    return render_template('student_complain.html',complains = complains_list)

@app.route('/reportComplain', methods = ['GET','POST'])
def reportComplain():
    if request.method == 'POST':
        complain = db.complain
        current_datetime = datetime.now()
        current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        complainData = {
            "name" : current_user.username,
            "hostelName" : request.form.get('hostelname'),
            "DateTime": current_datetime_str,
            "roomNo" : request.form.get('roomno'),
            "problem" : request.form.get('problem'),
            "category" : request.form.get('catagory'),
            "status": "Not Resolved",
        }
        complain.insert_one(complainData)
        return redirect(url_for('studentComplain'))
    return render_template('student_create_complain.html')

#--------------------------------Maintenance-------------------------------------------
@app.route("/maintenanceDept")
def maintenanceDept():
    # print(jsonify(complains_list))
    # return render_template('student_complain.html',complains = complains_list)
    return render_template("Maintainance_dashboard.html")


@app.route("/carpenterData")
def carpenterData():
    complains = db.complain.find({'category': "carpenter"})
    complains_list = list(complains)
    print(complains_list)
    for comp in complains_list:
        comp['_id'] = str(comp['_id'])
    return render_template("carpenter_complain.html",complains = complains_list)

@app.route("/electricianData")
def electricianData():
    complains = db.complain.find({'category': "electrician"})
    complains_list = list(complains)
    print(complains_list)
    for comp in complains_list:
        comp['_id'] = str(comp['_id'])
    return render_template("electrician_complain.html",complains = complains_list)

@app.route("/plumberData")
def plumberData():
    complains = db.complain.find({'category': "plumber"})
    complains_list = list(complains)
    print(complains_list)
    for comp in complains_list:
        comp['_id'] = str(comp['_id'])
    return render_template("plumber_complain.html",complains = complains_list)

@app.route('/solveComplain/<itemName>')
def solveComplain(itemName):
    complain = db.complain
    c = complain.update_one({'problem':itemName},{ '$set' : {'status': "Resolved"}})
    # deleteItem = notice.delete_one({'title' : itemName})
    # itemTitle = complain.find_one({'problem':itemName})
    # recipient_email = "21cse454.skzahirhossain@giet.edu"
    # if recipient_email:
    #     subject = "Problem Resolved"
    #     body = "Problem solved {itemname}, kindly check your ERP and Confirm the same"
    #     send_email_helper(recipient_email, subject, body)
    #     flash('Email sent successfully!', 'success')
    # else:
    #     flash('User does not have an email address.', 'error')
    if c:
        print("Updated")
    else:
        print("Not Updated")
    return redirect(url_for('maintenanceDept'))

# def send_email_helper(recipient, subject, body):
#     msg = Message(subject, recipients=[recipient])
#     msg.body = body
#     mail.send(msg)

#---------------------------------Logout-----------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
