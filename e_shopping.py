#!/usr/bin/env python3

# import necessary modules
import socket, secrets
from validate_email import validate_email
from modules import flask_tb, connect_to_mongodb, reset_password_email
from flask import Flask, request, redirect, render_template, Markup, session
from flask_bcrypt import Bcrypt

# set up the server initial configuration
e_shopping=Flask(
    __name__,
    static_folder="images",
    static_url_path="/images",
    template_folder="webpages"
)

# set up the secret key to save session
e_shopping.secret_key='Your secret key'

# set up the bcrypt to hash password
bcrypt=Bcrypt(e_shopping)

# return home page
@e_shopping.route("/")
def home_page():    
    return render_template("home_page.html")

# show search results
@e_shopping.route("/search_results")
def search_results():
    search="%s"%request.args.get("search")
    if search!="" and not search.isspace():
        collection=connect_to_mongodb.get_collection("products")    
        query={
            "full_name":{
                "$regex":"[%s]"%search,
                "$options":"i"
            }
        }
        count_documents=collection.count_documents(query)    
        if count_documents!=0:
            documents, search_results=collection.find(query).sort("category"), ""
            for document in documents:
                search_results+="""
                <a href="/products/%s">
                    <img src="/images/%s.png" width="100" height="100" style="vertical-align: middle;" />%s
                </a><br /><br />
                """%(document["category"], document["category"], document["full_name"])
            search_results=Markup(search_results)
        else:
            search_results="Sorry, there are no any products about keyword: %s."%search
        return render_template("search_results.html", search_results=search_results, search=search)
    else:
        search_results="You must input something!"
        return render_template("search_results.html", search_results=search_results, search=search)

# return products page
@e_shopping.route("/products/<category>", methods=["GET", "POST"])
def products(category):        
    if request.method!="POST":
        return render_template("%s.html"%category)
    else: # save or update category, price, and quantity to mongodb
        query, collection={"category":"%s"%category}, connect_to_mongodb.get_collection("products")   
        document=collection.find_one(query)
        full_name, price, quantity=document["full_name"], document["price"], request.form["quantity"]
        if "username" not in session:
            col="cart"+str(socket.gethostbyaddr(request.remote_addr))
        else:        
            col="cart"+str(socket.gethostbyaddr(request.remote_addr))
            collection=connect_to_mongodb.get_collection(col)        
            document_count=collection.estimated_document_count()
            col="cart(%s)"%session["username"]
            if document_count!=0:                
                collection.rename(col, dropTarget=True)                    
        collection=connect_to_mongodb.get_collection(col)        
        subtotal="{:.2f}".format(float(price)*int(quantity))            
        newvalues={
            "$set":{
                "full_name":full_name,
                "price":price, 
                "quantity":quantity, 
                "subtotal":subtotal, 
                "last_modified":"0"
            }
        }
        collection.update_one(query, newvalues, upsert=True)            
        return render_template("%s.html"%category)

# show products that user add 
@e_shopping.route("/cart")
def cart():
    if "username" not in session:
        return redirect("/login")    
    else:
        col="cart"+str(socket.gethostbyaddr(request.remote_addr))
        collection=connect_to_mongodb.get_collection(col)        
        col="cart(%s)"%session["username"]
        if collection.estimated_document_count()!=0:            
            collection.rename(col, dropTarget=True)                
        collection=connect_to_mongodb.get_collection(col)
        document_count=collection.estimated_document_count()
        if document_count!=0:
            documents, items, total=collection.find().sort("category"), [], 0        
            for document in documents:                                
                category="""
                <a href="/products/%s">
                    <img src="/images/%s.png" width="100" height="100" style="vertical-align: middle;" />%s
                </a>
                """%(document["category"], document["category"], document["full_name"])
                quantity="""
                <form action="/cart_modify" method="POST">
                    <input type="hidden" name="category" value="%s" />
                    <select name="quantity" onchange="this.form.submit()">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                        <option value="6">6</option>
                        <option value="7">7</option>
                        <option value="8">8</option>
                        <option value="9">9</option>
                        <option value="10">10</option>
                    </select>
                </form>
                """.replace("<option value=\"%s\">"%document["quantity"], "<option value=\"%s\" selected>"%document["quantity"])%document["category"]
                delete="""
                <form action="/cart_delete" method="POST">
                    <input type="hidden" name="category" value="%s" />
                    <input type="image" src="/images/delete.png" alt="Delete" width="25" height="25" />
                </form>
                """%document["category"]
                if document["last_modified"]!="0":                
                    query, newvalue={"category":document["category"]}, {"$set":{"last_modified":"0"}}
                    collection.update_one(query, newvalue)
                    quantity=quantity.replace("<select name=\"quantity\" onchange=\"this.form.submit()\">", "<select name=\"quantity\" onchange=\"this.form.submit()\" autofocus>")                                          
                items.append(flask_tb.Item(Markup(category), document["price"], Markup(quantity), document["subtotal"], Markup(delete)))        
                total+=float(document["subtotal"])
            total="{:.2f}".format(total)                 
            items.append(flask_tb.Item("Total:", "", "", total, ""))        
            table=flask_tb.ItemTable(items)        
        else:
            collection.drop()        
            table="You have not added any products."
        return render_template("cart.html", table=table)

# modify selected product quantity
@e_shopping.route("/cart_modify", methods=["POST"])
def cart_modify():
    if "username" not in session:
        return redirect("/login")
    else:
        col="cart(%s)"%session["username"]
        collection=connect_to_mongodb.get_collection(col)    
        category, quantity="%s"%request.form["category"], "%s"%request.form["quantity"]    
        query={"category":category}
        document=collection.find_one(query)
        price=document["price"]
        subtotal="{:.2f}".format(float(price)*int(quantity))
        newvalues={
            "$set":{
                "quantity":quantity, 
                "subtotal":subtotal, 
                "last_modified":"1"
            }
        }
        collection.update_one(query, newvalues)    
        return redirect("/cart")

# delete selected product from mongodb
@e_shopping.route("/cart_delete", methods=["POST"])
def cart_delete():
    if "username" not in session:
        return redirect("/login")
    else:
        col="cart(%s)"%session["username"]
        collection=connect_to_mongodb.get_collection(col)
        category="%s"%request.form["category"]
        query={"category":category}
        collection.delete_one(query)
        return redirect("/cart")

# return login page
@e_shopping.route("/login", methods=["GET", "POST"])
def login():    
    if request.method!="POST" and "username" not in session:        
        return render_template("login.html")            
    elif request.method!="GET" and "username" not in session: # check username and password to login        
        username, password="%s".lower()%request.form["username"], "%s"%request.form["password"]
        collection, query=connect_to_mongodb.get_collection("accounts"), {"username":username}
        count_documents=collection.count_documents(query)
        if count_documents!=0:        
            document=collection.find_one(query)
            check_password=bcrypt.check_password_hash(document["password"], password)
            if check_password!=True:
                error="Error: wrong password!"
                return render_template("login.html", username=username, error=error)            
        else:
            error="Error: username: %s does not exist!"%username
            return render_template("login.html", username=username, error=error)
        session["username"]=username
        return render_template("action_successfully.html", action="Hello %s!Log in"%username)
    else:
        return redirect("/profile")

# return profile page
@e_shopping.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:    
        return redirect("/login")        
    elif request.method!="POST":
        return render_template("profile.html", username="%s"%session["username"])    
    else: # check password and new password to modify
        password="%s"%request.form["password"]
        query, collection={"username":"%s"%session["username"]}, connect_to_mongodb.get_collection("accounts")
        document=collection.find_one(query)
        check_password=bcrypt.check_password_hash(document["password"], password)
        if check_password!=True:
            error="Error: wrong password!"
            return render_template("profile.html", username="%s"%session["username"], error=error)                
        new_password, check_new_password="%s"%request.form["new_password"], "%s"%request.form["check_new_password"]
        if new_password!="" and " " not in new_password:
            if not(len(new_password)>=8 and len(new_password)<=16):
                error="Error: new password must contain 8-16 characters"
                return render_template("profile.html", username="%s"%session["username"], error=error)                
        else:
            error="Error: new password cannot contain space!"
            return render_template("profile.html", username="%s"%session["username"], error=error)                
        if check_new_password!=new_password:
            error="Error: check new password is not equal to new password!"
            return render_template("profile.html", username="%s"%session["username"], error=error)                
        else:
            new_password=bcrypt.generate_password_hash(new_password)
            newvalue={"$set":{"password":new_password}}            
            collection.update_one(query, newvalue)            
            return render_template("action_successfully.html", action="Modify password")

# let user log out
@e_shopping.route("/logout")
def logout():
    if "username" not in session:
        return redirect("/login")
    else:
        username=session["username"]
        session.pop("username", None)
        return render_template("action_successfully.html", action="Bye bye %s!Log out"%username)

# return forgotten password page
@e_shopping.route("/forgotten_password", methods=["GET", "POST"])
def forgotten_password():    
    if request.method!="POST" and "username" not in session:        
        return render_template("forgotten_password.html")        
    elif request.method!="GET" and "username" not in session: # check email to reset password
        email="%s".lower()%request.form["email"]
        collection, query=connect_to_mongodb.get_collection("accounts"), {"email":email}
        count_documents=collection.count_documents(query)
        if count_documents!=0:
            document=collection.find_one(query)
            username, urlsafe=document["username"], secrets.token_urlsafe()            
            newvalue={"$set":{"urlsafe":urlsafe}}
            collection.update_one(query, newvalue)
            url="http://127.0.0.1/reset_password/%s/%s"%(username, urlsafe) 
            reset_password_email.send(email, url)
            return render_template("action_successfully.html", action="Send reset password e-mail")
        else:
            error="Error: e-mail: %s does not exist!"%email
            return render_template("forgotten_password.html", email=email, error=error)
    else:
        return redirect("/profile")

# return reset password page
@e_shopping.route("/reset_password/<username>/<urlsafe>", methods=["GET", "POST"])
def reset_password(username, urlsafe):    
    if request.method!="POST":        
        collection=connect_to_mongodb.get_collection("accounts")
        query={
            "username":"%s".lower()%username,
            "urlsafe":"%s"%urlsafe
        }
        count_documents=collection.count_documents(query)
        if count_documents!=0:        
            return render_template("reset_password.html", username="%s"%username, urlsafe="%s"%urlsafe)
        else:
            return redirect("/")
    else: # check password to reset
        password, check_password="%s"%request.form["password"], "%s"%request.form["check_password"]
        if password!="" and " " not in password:
            if not(len(password)>=8 and len(password)<=16):
                error="Error: password must contain 8-16 characters"
                return render_template("reset_password.html", username="%s"%username, urlsafe="%s"%urlsafe, error=error)            
        else:
            error="Error: password cannot contain space!"
            return render_template("reset_password.html", username="%s"%username, urlsafe="%s"%urlsafe, error=error)        
        if check_password!=password:
            error="Error: check password is not equal to password!"
            return render_template("reset_password.html", username="%s"%username, urlsafe="%s"%urlsafe, error=error)        
        else:
            password=bcrypt.generate_password_hash(password)
            query={
                "username":username,
                "urlsafe":urlsafe
            }            
            newvalues={
                "$set":{
                    "password":password,
                    "urlsafe":"0"
                }
            }
            collection=connect_to_mongodb.get_collection("accounts")
            collection.update_one(query, newvalues)            
            return render_template("action_successfully.html", action="Reset password")

# return create account page
@e_shopping.route("/create_account", methods=["GET", "POST"])
def create_account():        
    if request.method!="POST" and "username" not in session:
        return render_template("create_account.html")
    elif request.method!="GET" and "username" not in session: # check username, password, and email to create account
        username, password, check_password, email="%s".lower()%request.form["username"], "%s"%request.form["password"], "%s"%request.form["check_password"], "%s".lower()%request.form["email"]
        collection, query=connect_to_mongodb.get_collection("accounts"), {"username":username}
        if username.isalnum()!=True:
            error="Error: username can only contain alphanumeric!"
            return render_template("create_account.html", username=username, email=email, error=error)        
        elif not(len(username)>=6 and len(username)<=30):
            error="Error: username must contain 6-30 characters!"
            return render_template("create_account.html", username=username, email=email, error=error)        
        elif collection.count_documents(query)!=0:        
            error="Error: username: %s has been used!"%username
            return render_template("create_account.html", username=username, email=email, error=error)                
        if password!="" and " " not in password:
            if not(len(password)>=8 and len(password)<=16):
                error="Error: password must contain 8-16 characters"
                return render_template("create_account.html", username=username, email=email, error=error)        
        else:
            error="Error: password cannot contain space!"
            return render_template("create_account.html", username=username, email=email, error=error)        
        if check_password!=password:
            error="Error: check password is not equal to password!"
            return render_template("create_account.html", username=username, email=email, error=error)        
        email_valid=validate_email(email_address=email, check_format=True, check_blacklist=True, check_dns=True, dns_timeout=1, check_smtp=True, smtp_timeout=1, smtp_helo_host=None, smtp_from_address=None, smtp_debug=False)
        if email_valid!=False:
            query={"email":email}
            count_documents=collection.count_documents(query)            
            if count_documents!=0:
                error="Error: e-mail: %s has been used!"%email
                return render_template("create_account.html", username=username, email=email, error=error)
            else:
                password=bcrypt.generate_password_hash(password)
                document={
                "username":username,
                "password":password,
                "email":email,
                "urlsafe":"0"
                }
                collection.insert_one(document)                
                return render_template("action_successfully.html", action="Create account")
        else:
            error="Error: invalid e-mail!"
            return render_template("create_account.html", username=username, email=email, error=error)
    else:
        return redirect("/profile")    
# run the server
e_shopping.run()
