from flask import Flask, render_template, request, redirect, jsonify, url_for,\
                  flash, make_response
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import session as login_session
from database_setup import BASE, Categories, CategoryItems, Users
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc, exc
import requests
import json
import httplib2
import random
import string
import datetime

app = Flask(__name__)

# The create_engine() function let's our program know which database engine we
# want to communicate with.
ENGINE = create_engine(
    'postgresql+psycopg2://nikitas:nikitas@localhost/itemcatalog')

# Bind the engine to the base class. This command makes the connections between
# our class definitions and the corresponding tables within our database.
BASE.metadata.bind = ENGINE

# Create a sessionmaker object, to establish a link of communication between
# our code executions and the engine we just created.
DB_SESSION = sessionmaker(bind=ENGINE)

# Create an instance of a DB_SESSION to make changes to the database via its
# methods.
session = DB_SESSION()

# Create an instanse of the class with the name of the running application.
app = Flask(__name__)

# Google+ Client-ID.
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Declare the application's name.
APPLICATION_NAME = "Item Catalog Project"


# Create an anti-forgery state token to protect the security of our users by
# preventing anti-forgery request attacks. Each time we refresh, we generate
# a new state variable that we'll be passing on to the client.
@app.route('/login')
@app.route('/login/')
def login():
    if 'username' in login_session:
        flash('You are already logged in')
        return redirect('/home')
    else:
        # State will be 32 characters long and a mix of Uppercase letters and
        # digits. This state is the unique session token.
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        # Store state in the login_session object under the name state.
        login_session['state'] = state
        return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token,  by confirming that the token that the client sends
    # to the server matches the token that the server sent to the client. This
    # round-trip verification helps ensure that the user is making the request
    # not a malicious script. Using the request.args.get() method, we examine
    # the state token passed in by the ajax request and copmpare with the state
    # of the login_session. If these 2 do NOT match, we create a response of an
    # invalid state token and return this message to the client.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # If the states do match we can proceed and obtain the one-time
    # authorization code from the server with the request.data function.
    code = request.data

    # Next we'll try and use the one-time code and exchange it for a
    # credentials object, which will contain the access token for our server.
    try:
        # Create OAuth flow object and add the client's secret key info to it.
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        # Here we specify with postmessage that this is the one-time code
        # our server will be sending off.
        oauth_flow.redirect_uri = 'postmessage'
        # Initiate the exchange with the step2_exchange function by exchanging
        # the authorization code(the one-time code we pass as input) for a
        # credentails object.
        credentials = oauth_flow.step2_exchange(code)
    # If an error happens along the way, we throw a FlowExchangeError and send
    # the response as a JSON object.
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token inside the credentials object is valid.
    access_token = credentials.access_token
    # By appending this token to the following google URL, the Google API
    # server can verify that this is a valid token for use.
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # In the following 2 lines we create a JSON GET request containing the
    # URL and access token.
    http = httplib2.Http()
    result = json.loads(http.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        # Send a 500 internal error to the client.
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    # Grab the ID of the token from the credentials object.
    gplus_id = credentials.id_token['sub']
    # Compare it to the ID returned by the Google API server. If these IDs
    # do not match then we do not have the correct token and should return
    # an error.
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    # If the client-IDs do not match our app is trying is trying to use
    # an ID that does not belong to it, so we don't allow that.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token\'s client ID does not match app\'s.")
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if a user is already logged in.
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    # If the user is logged in, we'll return a 200 success without resetting
    # all of the login session variables again.
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # Store only the data we are interested in.
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # See if user exists in our database, if they don't make a new one.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser()
    login_session['user_id'] = user_id

    # Create the response.
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "class="profile-picture"> '
    # Add a flash message to let the user know they are logged in.
    flash("You are now logged in as %s" % login_session['username'])
    print("Done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    # Grab the access_token from the login_session object.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    http = httplib2.Http()
    result = http.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for'
                                            'given use. Response: %s'
                                            % result['status']))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print("Access token received %s " % access_token)

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_excha'\
          + 'nge_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
              app_id, app_secret, access_token)
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]

    '''
    Due to the formatting of the results from the server, we have to split
    the token first on commas and select the first index which gives us the
    'key : value' pair for the server access token, then we split it on
    colons to pull out the actual token value and replace the remaining
    quotes with nothing so that it can be used directly in the graph api
    calls, in order to token exchange.
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    # Use the token to get user's info from the API.
    url = 'https://graph.facebook.com/v2.8/me?access_token=' \
          + token + '&fields=name,id,email'
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=' \
          + token + '&redirect=0&height=200&width=200'
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser()
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " class="profile-picture"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
        % (facebook_id, access_token)
    http = httplib2.Http()
    result = http.request(url, 'DELETE')[1]
    return "You have been logged out: " + result


# Logout based on provider.
@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
    else:
        flash("You were not logged in")
    return redirect(url_for('home'))


# Create new user.
def createUser():
    newUser = Users(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(Users).filter_by(email=login_session['email']).one()
    return user.id


# Get a specific user.
def getUserInfo(user_id):
    user = session.query(Users).filter_by(id=user_id).one()
    return user


# Get a user's ID.
def getUserID(email):
    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except exc.SQLAlchemyError:
        return None


# Get home page.
@app.route('/')
@app.route('/home')
@app.route('/home/')
def home():
    # Get the names of all the categories.
    categories = session.query(Categories.name).all()
    # Get the 5 latest entries to the categories.
    latestItems = session.query(CategoryItems).\
        order_by(desc(CategoryItems.date_time)).limit(5).all()
    # Render the template.
    return render_template('home.html', categories=categories,
                           items=latestItems)


# Get a category's item catalog.
@app.route('/home/<category_name>')
@app.route('/home/<category_name>/')
@app.route('/home/<category_name>/items')
@app.route('/home/<category_name>/items/')
def categoryItems(category_name):
    # Get the names of all the categories.
    categories = session.query(Categories.name).all()
    # Get the category the user navigated to.
    selectedCategory = session.query(Categories) \
        .filter_by(name=category_name).one()
    # Get the items that belong to that category.
    items = session.query(CategoryItems) \
        .filter_by(category_id=selectedCategory.id).all()
    # Get the number of all the items in that category.
    totalItems = session.query(CategoryItems) \
        .filter_by(category_id=selectedCategory.id).count()
    # Render the template.
    return render_template('catalogItems.html', categories=categories,
                           selectedCategory=selectedCategory, items=items,
                           totalItems=totalItems)


# Get information about a specific item. The item's ID is included
# in the URL so that we fetch the right item in case of duplicates.
@app.route('/home/<category_name>/<item_name>/<item_id>')
@app.route('/home/<category_name>/<item_name>/<item_id>/')
def viewItem(category_name, item_name, item_id):
    # Get the item that was selected.
    item = session.query(CategoryItems).filter_by(id=item_id).one()
    # Get this item's creator.
    creator = getUserInfo(item.user_id)
    # Check whether the user viewing this item is it's creator or not.
    if 'username' not in login_session or creator.id \
            != login_session['user_id']:
        # Render template for users that have not created this item.
        return render_template('viewPublicItem.html', item=item,
                               creator=creator)
    else:
        # Render template for the user that has created this item.
        return render_template('viewItem.html', category_name=category_name,
                               item=item, creator=creator)


# Create a new item for any category.
@app.route('/home/create', methods=['GET', 'POST'])
@app.route('/home/create/', methods=['GET', 'POST'])
def createItem():
    # We don't need to check which user is trying to access the page because
    # any user should be able to create an item.
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # Check if the user has filled all the required fields.
        if request.form['name'] and request.form['content'] and request \
                .form['category']:
            # Get the category based on the selected name in the form.
            category = session.query(Categories) \
                .filter_by(name=request.form['category']).one()
            # Get the user's ID in order to determine which user created the
            # object.
            userID = getUserID(login_session['email'])
            # Create a new item in the database.
            newItem = CategoryItems(name=request.form['name'],
                                    content=request.form['content'],
                                    category_id=category.id, user_id=userID,
                                    date_time=datetime.datetime.now())
            session.add(newItem)
            session.commit()
            flash('New Item Successfully Created:' + newItem.name)
            return redirect(url_for('home'))
        else:
            flash('You need to fill out all the fields to create a new item.')
            return render_template('createItem.html')
    else:
        return render_template('createItem.html')


# Create a new item for a specific category.
@app.route('/home/<category_name>/create', methods=['GET', 'POST'])
@app.route('/home/<category_name>/create/', methods=['GET', 'POST'])
def createCategoryItem(category_name):
    # We don't need to check which user is trying to access the page because
    # any user should be able to create an item.
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # Check if the user has filled all the required fields.
        if request.form['name'] and request.form['content']:
            # Get the category based on which category page the user is
            # currently on.
            category = session.query(Categories) \
                .filter_by(name=category_name).one()
            # Get the user's ID in order to determine which user created the
            # object.
            userID = getUserID(login_session['email'])
            # Create a new item in the database.
            newItem = CategoryItems(name=request.form['name'],
                                    content=request.form['content'],
                                    category_id=category.id, user_id=userID,
                                    date_time=datetime.datetime.now())
            session.add(newItem)
            session.commit()
            flash('New Item for ' + category_name + 'Successfully Created: %s'
                  % newItem.name)
            return redirect(url_for('home'))
        else:
            flash('You need to fill out all the the fields to create a'
                  'new item.')
            return render_template('createCategoryItem.html',
                                   category_name=category_name)
    else:
        return render_template('createCategoryItem.html',
                               category_name=category_name)


# Edit an item. The item's ID is contained in the URL to make sure we request
# the right item in case of duplicate items.
@app.route('/home/<category_name>/<item_name>/<item_id>/edit',
           methods=['GET', 'POST'])
@app.route('/home/<category_name>/<item_name>/<item_id>/edit/',
           methods=['GET', 'POST'])
def editItem(category_name, item_name, item_id):
    # Check if the user is logged in.
    if 'username' not in login_session:
        return redirect('/login')
    # If the user is logged in, check if they are the creator of the item.
    # If the user is indeed the item's creator, get the item to be edited.
    editItem = session.query(CategoryItems).filter_by(id=item_id).one()
    if login_session['user_id'] != editItem.user_id:
        flash('Nice try, but you are not allowed to go there.')
        return redirect('/home')
    # Handle requests.
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['content']:
            editItem.content = request.form['content']
        if request.form['category']:
            newCategoryName = request.form['category']
            newCategory = session.query(Categories) \
                .filter_by(name=newCategoryName).one()
            editItem.category_id = newCategory.id
            # Also update the items date-time.
            editItem.date_time = datetime.datetime.now()
        session.add(editItem)
        session.commit()
        flash(' Item Successfully Edited: ' + editItem.name)
        return redirect(url_for('home'))
    else:
        return render_template('editItem.html', editItem=editItem)


# Delete an item.
@app.route('/home/<category_name>/<item_name>/<item_id>/delete',
           methods=['GET', 'POST'])
@app.route('/home/<category_name>/<item_name>/<item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name, item_id):
    # Check if the user is logged in.
    if 'username' not in login_session:
        return redirect('/login')
    # If the user is logged in, check if they are the creator of the item.
    # If the user is indeed the item's creator, get the item to be deleted.
    itemToDelete = session.query(CategoryItems).filter_by(id=item_id).one()
    if login_session['user_id'] != itemToDelete.user_id:
        flash('Nice try, but you are not allowed to go there.')
        return redirect('/home')
    # Handle requests.
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted : ' + itemToDelete.name)
        return redirect(url_for('home'))
    else:
        return render_template('deleteItem.html', itemToDelete=itemToDelete)


# JSON endpoint

# Get all user data.
@app.route('/users/JSON')
@app.route('/users/JSON/')
def users_json():
    users = session.query(Users).all()
    return jsonify(Users=[i.serialize for i in users])


# Get specific user data (If the username contains spaces use the URL encoding
# for space, which is %20).
@app.route('/users/<user_name>/JSON')
@app.route('/users/<user_name>/JSON/')
def user_json(user_name):
    user = session.query(Users).filter_by(name=user_name).one()
    return jsonify(User=user.serialize)


# Get all category data.
@app.route('/categories/JSON')
@app.route('/categories/JSON/')
def categories_json():
    categories = session.query(Categories).all()
    return jsonify(Categories=[i.serialize for i in categories])


# Get specific category data.
@app.route('/categories/<category_name>/JSON')
@app.route('/categories/<category_name>/JSON/')
def category_json(category_name):
    category = session.query(Categories).filter_by(name=category_name).one()
    return jsonify(Category=category.serialize)


# Get all item data.
@app.route('/items/JSON')
@app.route('/items/JSON/')
def items_json():
    items = session.query(CategoryItems).all()
    return jsonify(Items=[i.serialize for i in items])


# Get specific item data.
@app.route('/items/<item_name>/<item_id>/JSON')
@app.route('/items/<item_name>/<item_id>/JSON/')
def item_json(item_id):
    item = session.query(CategoryItems).filter_by(name=item_id).one()
    return jsonify(Item=item.serialize)


# This if statement makes sure the server only runs if the sript is executed
# directly from the Python interpeter and not used as an imported module.
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    # Run the local server with our application.
    app.run(host='0.0.0.0', port=5000)
