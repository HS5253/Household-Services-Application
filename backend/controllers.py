from flask import Flask, render_template
from flask import request, url_for, redirect,send_file
from flask import current_app as app
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from .models import *
from sqlalchemy import or_
from flask import flash
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory,abort




ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods = ["POST", "GET"])
def signin():
    if request.method=="POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")
        user = User.query.filter_by(username = uname, password = pwd).first()
        if user and user.role == 0:
            return redirect(url_for("admin_dashboard", name = uname))
        elif user and user.role == 1:
            return redirect(url_for("customer_dashboard", name = uname)) 
        elif user and user.role == 2:
            return redirect(url_for("professional_dashboard", name = uname))
        else:
            return render_template("login.html", msg = "Invalid User credentials")
    return render_template("login.html", msg="")

@app.route("/logout")
def logout():
    return redirect(url_for('signin'))

@app.route("/register", methods=["POST", "GET"])
def customer_signup():
    if request.method == "POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")
        fullname = request.form.get("fullname")
        address=request.form.get("address")
        pincode=request.form.get("pincode")
        
        # Create new user and customer
        try:
            new_user = User(username=uname, password=pwd, role=1)
            db.session.add(new_user)
            db.session.commit()

            # Create new customer
            new_customer = Customer(
                user_id=new_user.id,
                email=uname,
                password=pwd,
                full_name=fullname,
                address=address,
                pincode=pincode
            )
            db.session.add(new_customer)
            db.session.commit()
            return render_template("login.html", msg="User registered succesfully")
        except(Exception) as e:
            db.session.rollback()
            db.session.delete(new_user)
            db.session.commit()
            print(f"Error: {e}")
    
    # Render the signup page if it's a GET request
    return render_template("customer_signup.html", msg="")

# Set up the upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join(os.getcwd(),'static', 'uploads', 'professional_documents')

# Create the upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/register/professional", methods=["POST", "GET"])
def service_professional_signup():
    services = get_allservices()  # Get list of services for the form dropdown
    if request.method == "POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")
        fullname = request.form.get("fullname")
        service_id = request.form.get("service_name")  # This will contain the service ID
        exp = request.form.get("experience")
        desc = request.form.get("description")
        price = request.form.get("price")
        service = get_service(service_id)
        if price < service.price:
            return render_template("service_professional_signup.html", services=services, msg=f"Price cannot be set lower than {service.price} for the service {service.name}")
        
        file = request.files.get('profile_documents')
        if file:
            filename = secure_filename(file.filename)  # Secure the filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)  # Full file path
            file.save(file_path)  # Save the file
        else:
            file_path = None  # If no file is uploaded, set file_path to None
            
        # Create new user and service professional
        try:
            new_user = User(username=uname, password=pwd, role=2)
            db.session.add(new_user)
            db.session.commit()

            # Create new service professional
            new_service_prof = ServiceProfessional(
                user_id=new_user.id,
                email=uname,
                password=pwd,
                full_name=fullname,
                service_id=service_id, 
                description=desc,
                experience=exp,
                price=price,
                verification="pending",
                profile_documents=file_path
            )
            db.session.add(new_service_prof)
            db.session.commit()
            return render_template("login.html", msg="User registered successfully")
        except Exception as e:
            db.session.rollback()
            db.session.delete(new_user)
            db.session.commit()
            print(f"Error: {e}")
    
    # Render the signup page if it's a GET request
    return render_template("service_professional_signup.html", services=services, msg="")



#Common route for admin dashboard
@app.route("/admin/<name>")
def admin_dashboard(name):
    services = get_allservices()
    professionals = get_professionals_pending()
    service_requests = ServiceRequest.query.all()
    return render_template("admin_dashboard.html", name= name, services = services, professionals=professionals,requests=service_requests)

@app.route('/admin/all_services/<name>',methods=["POST","GET"])
def admin_all_services(name):
    services = get_allservices() # Retrieve all services
    return render_template('admin_viewservices.html', services=services, name=name)

@app.route('/admin/all_professionals/<name>',methods=["POST","GET"])
def admin_all_professionals(name):
    professionals = ServiceProfessional.query.all()  # Retrieve all professionals
    return render_template('admin_viewprofessionals.html', professionals=professionals, name=name)

@app.route('/admin/all_customers/<name>',methods=["POST","GET"])
def admin_all_customers(name):
    customers = Customer.query.all()
    return render_template("admin_viewcustomers.html",name=name,customers=customers)

@app.route('/admin/all_requests/<name>',methods=["POST","GET"])
def admin_all_requests(name):
    requests = ServiceRequest.query.all()
    return render_template("admin_viewservicerequests.html",name=name,requests=requests)

#Blocking the customer
@app.route('/admin/block/<customer_id>/<name>',methods=["POST","GET"])
def admin_blockcustomer(customer_id,name):
    customer = get_customerbyid(customer_id)
    customer.profile_status = 1
    db.session.commit()

    customers = Customer.query.all()
    return render_template('admin_viewcustomers.html',name=name,customers=customers)

#Unblocking the customer
@app.route('/admin/unblock/<customer_id>/<name>',methods=["POST","GET"])
def admin_unblockcustomer(customer_id,name):
    customer = get_customerbyid(customer_id)
    customer.profile_status = 0
    db.session.commit()

    customers = Customer.query.all()
    return render_template('admin_viewcustomers.html',name=name,customers=customers)
    
#Blocking the service professional
@app.route('/admin/block/professional/<professional_id>/<name>',methods=["POST","GET"])
def admin_blockprofessional(professional_id,name):
    professional = get_service_prof(professional_id)
    professional.profile_status = 1
    db.session.commit()
    professionals = ServiceProfessional.query.all()
    return render_template('admin_viewprofessionals.html',name=name,professionals=professionals)

#Unblocking the service professional
@app.route('/admin/unblock/professional/<professional_id>/<name>',methods=["POST","GET"])
def admin_unblockprofessional(professional_id,name):
    professional = get_service_prof(professional_id)
    professional.profile_status = 0
    db.session.commit()

    professionals = ServiceProfessional.query.all()
    return render_template('admin_viewprofessionals.html',name=name,professionals=professionals)

@app.route("/admin/summary/<name>")
def admin_summary(name):
    data = generate_admin_summary_data()
    return render_template("admin_summary.html", data=data,name=name)

@app.route("/addservice/<name>", methods = ["POST", "GET"])
def add_service(name):
    if request.method=="POST":
        sname = request.form.get("service_name")
        sprice = request.form.get("service_price")
        stimereq = request.form.get("service_time_req")
        sdesc = request.form.get("service_description")
        new_service = Service(name =sname, price =sprice,time=stimereq,description=sdesc)
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for("admin_dashboard", name = name))
    return render_template("add_service.html", name = name)

@app.route("/edit_service/<id>/<name>", methods = ["POST","GET"])
def edit_service(id,name):
    s = get_service(id)
    if request.method == "POST":
        sname = request.form.get("service_name")
        sprice = request.form.get("service_price")
        stimereq = request.form.get("service_time_req")
        sdesc = request.form.get("service_description")
        s.name = sname
        s.price = sprice
        s.time = stimereq
        s.description = sdesc
        db.session.commit()
        return redirect(url_for("admin_dashboard",name=name))
    return render_template("admin_edit_service.html", service=s,name=name)

@app.route("/delete_service/<id>/<name>", methods = ["POST","GET"])
def delete_service(id,name):
    services = get_allservices()
    professionals = get_professionals_pending()
    s = get_service(id)
    service_reqs = get_servicerequests(id)
    for service_req in service_reqs:
        if service_req.service_status == "requested" or service_req.service_status == "confirmed":
            return render_template("admin_dashboard.html", 
                        name=name, 
                        msg="Service cannot be deleted as service requests are still open with this service")
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for("admin_dashboard",name=name,services=services,professionals=professionals))

@app.route("/service-professional/<id>/<name>", methods = ["POST","GET"])
def view_serviceprof_profile(id,name):
    professional = get_service_prof(id)
    return render_template("admin_professional_profile.html",professional = professional, name = name)

# Route to serve document files
@app.route('/uploads/professional_documents/<filename>',methods=["POST","GET"])
def serve_professional_document(filename):
    try:
        # Ensure the file path is correct and safe for the server
        document_directory = os.path.join(app.root_path, 'static', 'uploads', 'professional_documents')

        # Ensure that the filename is safe and does not have directory traversal characters
        filename = os.path.basename(filename)  # Sanitize filename to prevent path traversal

        file_path = os.path.join(document_directory, filename)

        # Check if the file exists
        if not os.path.isfile(file_path):
            abort(404)  # Return 404 if the file doesn't exist
        
        # Serve the file from the directory
        return send_from_directory(document_directory, filename)
    except Exception as e:
        abort(500)


@app.route("/approve-profile/<id>/<name>", methods = ["POST","GET"])
def approve_professional(id, name):
    service_professional = ServiceProfessional.query.filter_by(id=id).first()
    service_professional.verification = "approved"
    db.session.commit()
    return redirect(url_for("admin_dashboard",name=name))

@app.route("/reject-profile/<id>/<name>", methods = ["POST","GET"])
def reject_professional(id, name):
    service_professional = ServiceProfessional.query.filter_by(id=id).first()
    service_professional.verification = "rejected"
    db.session.commit()
    return redirect(url_for("admin_dashboard",name=name))

 #Common route for customer dashboard

@app.route("/customer/<name>",methods=["POST","GET"])
def customer_dashboard(name):
    services=get_allservices()
    return render_template("customer_dashboard.html", name=name, services=services)

@app.route("/customer/profile/<name>", methods=["POST","GET"])
def customer_profile(name):
    customer=get_customer(name)
    return render_template("customer_profile.html",customer=customer, name=name,msg="")

@app.route("/customer/profile/close_account/<customer_id>/<name>", methods=["POST", "GET"])
def customer_closeaccount(customer_id, name):
    customer = get_customerbyid(customer_id)
    if request.method == "POST":
        try:
            service_requests = get_requests_by_cid(customer.id)
            if service_requests:
                for service_req in service_requests:
                    professional = get_service_prof(service_req.professional_id)
                    professional.available_status = 1
                    db.session.commit()
            db.session.delete(customer)
            db.session.commit()
            return render_template("index.html")  # 'login' should match the name of your login route
        except Exception as e:
            print(e)
            db.session.rollback()
            return redirect(url_for('customer_profile',customer=customer,name=name,msg="Please try again later"))

@app.route("/customer/bookings/<name>", methods=["POST","GET"])
def customer_bookings(name):
    service_requests = get_customer_requests(name)
    return render_template("customer_bookings.html",service_requests=service_requests,name=name)

@app.route("/customer/book/<id>/<name>", methods=["POST","GET"])
def bookservice(id,name):
    service = get_service(id)
    professionals = get_service_allprof(id)
    customer = get_customerbyid(id)
    return render_template("customer_professionals_available.html", service=service, professionals=professionals, customer=customer,name=name)
   
@app.route("/customer/confirmbooking/<service_id>/<professional_id>/<name>",methods=["POST","GET"])
def confirmbooking(service_id, professional_id, name):
    service = get_service(service_id)
    professional = get_service_prof(professional_id)
    customer = get_customer(name)    
    if request.method == "POST":
        customer_id = customer.id
        date_of_request = request.form.get("date_time")
        #processing date/time
        date_of_request=datetime.strptime(date_of_request,"%Y-%m-%dT%H:%M")
        service_status = "requested"
        service_request = ServiceRequest(service_id=service_id, customer_id=customer_id, 
                            professional_id=professional_id,date_of_request=date_of_request,service_status=service_status)
        db.session.add(service_request)
        db.session.commit()
        customer = get_customerbyid(customer_id)
        service_requests = get_requests_by_cid(customer.id)
        return render_template("customer_bookings.html",service_requests=service_requests,name=name)
    return render_template("customer_book_service.html", customer=customer, name=name, service=service, professional=professional)

@app.route("/customer/editrequest/<request_id>/<name>", methods=["POST", "GET"])
def editrequest(request_id, name):
    service_request = get_request(request_id)
    
    if request.method == "POST":
        # Get and validate the date_time input
        date_of_request = request.form.get("date_time")
        if date_of_request:
            try:
                date_of_request = datetime.strptime(date_of_request, "%Y-%m-%dT%H:%M")
                service_request.date_of_request = date_of_request
                db.session.commit()
                # Redirect to bookings page with success message
                return redirect(url_for('customer_bookings', name=name))
            except ValueError:
                flash("Invalid date format. Please try again.", "danger")
        else:
            flash("Date and time are required.", "danger")

    # Render the edit form with the current service request
    return render_template("customer_edit_services.html", name=name, service_request=service_request)

@app.route("/customer/delete_request/<request_id>/<name>",methods=["POST","GET"])
def customer_deleterequest(request_id,name):
    service_request = get_request(request_id)
    professional = get_service_prof(service_request.professional_id)
    try:
        professional.available_status = 1
        db.session.commit()
        db.session.delete(service_request)
        db.session.commit()
        return render_template("customer_bookings.html",name=name)
    except Exception as e:
        db.session.rollback()
        return render_template("customer_bookings.html",name=name)
    
@app.route("/customer/feedback/<request_id>/<name>",methods=["POST","GET"])
def customer_feedback(request_id,name):
    service_request = get_request(request_id)
    service_requests = get_customer_requests(name)
    if request.method=="POST":
        remarks = request.form.get("remarks")
        reviews = request.form.get("reviews")
        service_request.remarks = remarks
        service_request.reviews = reviews
        db.session.commit()
        return render_template("customer_bookings.html",name=name,service_requests=service_requests)
    return render_template("customer_feedback_servicerequest.html",service_request=service_request,name=name)


@app.route("/customer/changeprofessional/<request_id>/<name>", methods=["POST","GET"])
def changeprofessional(request_id,name):
    service_request = get_request(request_id)
    professionals = get_service_allprof(service_request.service_id)
    return render_template("customer_change_professional.html", professionals = professionals, service_request=service_request,name=name)

@app.route("/customer/updateprofessional/<request_id>/<professional_id>/<name>",methods=["POST","GET"])
def update_request_professional(request_id,professional_id, name):
    service_request = get_request(request_id)
    current_professional = get_service_prof(service_request.professional_id)
    professional = get_service_prof(professional_id)
    service_requests = get_customer_requests(service_request.customer_id)
    if request.method=="POST":
        service_request.professional_id = professional.id
        date_of_request = request.form.get("date_time")
        date_of_request=datetime.strptime(date_of_request,"%Y-%m-%dT%H:%M")
        service_request.date_of_request=date_of_request
        service_request.service_status = "requested"
        db.session.commit()
        current_professional.available_status=1
        db.session.commit()
        return render_template("customer_bookings.html",service_requests=service_requests,name=name)
    return render_template("customer_update_service_request.html", service_request = service_request, professional=professional, name=name)

 #Common route for professional dashboard
@app.route("/professional/<name>", methods=["POST","GET"])
def professional_dashboard(name):
    return render_template("professional_dashboard.html", name = name)

@app.route("/professional/profile/<name>", methods=["POST","GET"])
def view_prof_profile(name):
    professional = get_professionals_name(name)
    service = get_service(professional.service_id)
    return render_template("professional_profile.html", name =name, professional=professional, service=service,msg="")

@app.route("/professional/profile/close_account/<professional_id>/<name>", methods=["POST", "GET"])
def professional_closeaccount(professional_id, name):
    professional = get_service_prof(professional_id)
    service = get_service(professional.service_id)
    print(service)
    if request.method == "POST":
        try:

            db.session.delete(professional)
            db.session.commit()
            return redirect(url_for('login',msg = "Account closed successfully"))  # 'login' should match the name of your login route
        except Exception as e:
            print(e)
            db.session.rollback()
            return redirect(url_for('professional_profile', name=name,professional=professional,service=service,msg="Please try again later"))

@app.route("/professional/closerequest/<request_id>/<name>", methods=["POST","GET"])
def closerequest_by_p(request_id,name):
    professional = get_professionals_name(name)
    service_request = get_request(request_id)
    service_request.date_of_completion = datetime.now()
    service_request.service_status = "completed"
    professional.available_status = 1
    db.session.commit()
    professional = get_professionals_name(name)
    requests = getrequestclosed_by_prof(professional.id)
    return render_template("professional_completedrequests.html",name=name,requests = requests)

@app.route("/professional/pendingrequests/<name>",methods=["POST","GET"])
def professional_view_requests(name):
    professional = get_professionals_name(name)
    requests = getrequestpending_by_prof(professional.id)
    return render_template("professional_pendingrequests.html",name=name, requests=requests)

@app.route("/professional/closed-requests/<name>",methods=["POST","GET"])
def professional_closedrequests(name):
    professional = get_professionals_name(name)
    requests = getrequestclosed_by_prof(professional.id)
    return render_template("professional_completedrequests.html",requests= requests,name=name)

@app.route("/professional/edit_profile/<professional_id>/<name>", methods=["POST","GET"])
def edit_profesionalprofile(professional_id,name):
    professional = get_service_prof(professional_id)
    user = get_user(professional.user_id)
    service = get_service(professional.service_id)
    if request.method=="POST":
        professional.full_name = request.form.get("full_name")
        professional.email = request.form.get("email")
        professional.experience = request.form.get("experience")
        professional.description = request.form.get("description")
        professional.verification = 'pending'
        user.username = request.form.get("email")
        db.session.commit()
        return render_template("professional_profile.html",name=name,professional=professional,service=service)
    return render_template("professional_editprofile.html", name=name,professional=professional)

@app.route("/professional/edit_services/<professional_id>/<name>",methods=["POST","GET"])
def edit_service_professional(professional_id,name):
    professional = get_service_prof(professional_id)
    services = get_allservices()
    if request.method=="POST":
        service_id = request.form.get("service_name")
        price = request.form.get("price")
        experience = request.form.get("experience")
        description = request.form.get("description")
        service = get_service(service_id)
        print(service)
        if price<service.price:
            return render_template("professional_editservice.html", services=services, professional=professional,name=name,
                                   msg=f"Price cannot be set lower then {service.price} for the service {service.name}")
        professional.service_id = service_id
        professional.price = price
        professional.experience = experience
        professional.description = description
        professional.verification = 'pending'
        db.session.commit()
        return render_template("professional_profile.html",name=name, professional=professional,service=service)
    return render_template("professional_editservice.html", name=name,professional=professional,services=services)

@app.route("/professional/accept-request/<request_id>/<name>")
def professional_acceptrequest(request_id,name):
    service_request = get_request(request_id)
    try:
        service_request.service_status = "confirmed"
        professional = get_service_prof(service_request.professional_id)
        professional.available_status = 0
        requests = getrequestpending_by_prof(service_request.professional_id)
        db.session.commit()
        return render_template("professional_pendingrequests.html",name=name, requests=requests)
    except Exception as e:
        db.session.rollback()
        requests = getrequestpending_by_prof(service_request.professional_id)
        return render_template("professional_pendingrequests.html",name=name, requests=requests)


@app.route("/professional/reject-request/<request_id>/<name>")
def professional_rejectrequest(request_id,name):
    service_request = get_request(request_id)
    try:
        service_request.service_status = "rejected"
        requests = getrequestpending_by_prof(service_request.professional_id)
        db.session.commit()
        return render_template("professional_pendingrequests.html",name=name, requests=requests)
    except Exception as e:
        db.session.rollback()
        requests = getrequestpending_by_prof(service_request.professional_id)
        return render_template("professional_pendingrequests.html",name=name, requests=requests)

@app.route("/professional/earnings/<name>")
def professional_earnings(name):
    professional = get_professionals_name(name)
    # Fetch completed service requests for the professional
    completed_services = getrequestclosed_by_prof(professional.id)  # List of completed services

    # Calculate total earnings
    total_earnings = professional.price * len(completed_services)  # Total earnings

    # Calculate monthly earnings
    monthly_earnings = {}
    for service_req in completed_services:
        month = service_req['date_of_completion'].strftime("%B %Y")  # Extract the month and year
        monthly_earnings[month] = monthly_earnings.get(month, 0) + service_req['amount']

    # Calculate average earnings per service
    average_earnings = total_earnings / len(completed_services) if completed_services else 0

    return render_template(
        "professional_earnings.html",
        name=name,
        total_earnings=total_earnings,
        average_earnings=average_earnings,
        monthly_earnings=monthly_earnings
    )


#Other supported functions
def get_user(id):
    user = User.query.filter_by(id=id).first()
    return user

def get_allservices():
    services = Service.query.all()
    return services

def get_professionals_pending():
    professsionals = ServiceProfessional.query.filter_by(verification="pending").all()
    return professsionals

def search_by_service(search_txt):
    services = Service.query.filter(Service.name.like(f"%{search_txt}%") |Service.price.like(f"%{search_txt}%") |Service.description.like(f"%{search_txt}%")).all()
    return services

def get_service(id):
    service = Service.query.filter_by(id=id).first()
    return service

#all requests
def get_servicerequests(id):
    service_requests = ServiceRequest.query.filter_by(service_id = id).all()
    return service_requests

def get_requests_by_cid(id):
    service_requests = ServiceRequest.query.filter_by(customer_id = id).all()
    return service_requests

def get_customer_requests(name):
    customer=get_customer(name)
    service_requests = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    return service_requests

#single request
def get_request(id):
    service_request = ServiceRequest.query.filter_by(id=id).first()
    return service_request

def get_service_allprof(id):
    professionals = ServiceProfessional.query.filter_by(service_id=id, verification="approved").all()
    return professionals

def get_service_prof(id):
    professional = ServiceProfessional.query.filter_by(id=id).first()
    return professional

def get_professionals_name(name):
    professional = ServiceProfessional.query.filter_by(email=name).first()
    return professional

def get_customerbyid(id):
    customer = Customer.query.filter_by(id=id).first()
    return customer

def get_customer(name):
    customer = Customer.query.filter_by(email=name).first()
    return customer

def getrequestpending_by_prof(professional_id):
    requests = ServiceRequest.query.filter(
    ServiceRequest.professional_id == professional_id,
    or_(
        ServiceRequest.service_status == "requested",
        ServiceRequest.service_status == "confirmed"
    )).all()
    return requests

def getrequestclosed_by_prof(professional_id):
    requests = ServiceRequest.query.filter_by(service_status="completed", professional_id=professional_id).all()
    return requests

def get_allrequests_by_prof(id):
    requests = ServiceRequest.query.filter_by(professional_id=id).all()
    return requests

def get_total_earnings(service_requests):
    total_earnings = 0
    for service_req in service_requests:
        total_earnings = total_earnings + service_req.professional.price
    return total_earnings

def generate_admin_summary_data():
    service_requests = ServiceRequest.query.all()

    # Data preparation
    status_counts = {"requested": 0, "confirmed": 0, "completed": 0}
    service_types = {}
    total_earnings = 0

    # Loop through each service request to calculate the data
    for req in service_requests:
        # Count statuses
        status_counts[req.service_status] = status_counts.get(req.service_status, 0) + 1

        # Count service types
        service_name = req.service.name
        service_types[service_name] = service_types.get(service_name, 0) + 1

        # Calculate total earnings
        if req.service_status == "completed":
            total_earnings += req.professional.price

    # Return the summary data
    return {
        "status_counts": status_counts,
        "service_types": service_types,
        "total_earnings": total_earnings,
    }
