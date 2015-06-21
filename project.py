from flask import Flask, render_template, request, redirect, url_for, \
    flash, jsonify, session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import random
import string

from database_setup import Genre, Movie, User

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

app = Flask(__name__)
session = None


def init_session():
    """Initialize database session
    """
    global session
    # an Engine, which the Session will use for connection
    # resources
    some_engine = create_engine('sqlite:///moviescatalog.db')

    # create a configured "Session" class
    Session = sessionmaker(bind=some_engine)

    # create a Session
    session = Session()


@app.route('/login')
def show_login():
    """Show login page
    """
    # Create a state token to prevent request forgery
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32)
    )
    # Store it in the session for later validation
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Login with Google
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200
        )
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # Store user data in the session
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    user_id = get_user_id(data['email'])
    if user_id is None:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    flash("Successfully logged in as %s" % login_session['username'])

    return render_template(
        'loggedin.html', username=login_session['username'],
        picture=login_session['picture']
    )


@app.route('/gdisconnect')
def gdisconnect():
    """Log out with Google
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """Log in with Facebook
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Strip expire tag from access token
    token = result.split("&")[0]

    # Get user data
    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly
    # logout, let's strip out the information before the equals sign in
    # our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # See if user exists
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    flash("Successfully logged in as %s" % login_session['username'])

    return render_template(
        'loggedin.html', username=login_session['username'],
        picture=login_session['picture']
    )


@app.route('/fbdisconnect')
def fbdisconnect():
    """Log out with Facebook
    """
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    url = 'https://graph.facebook.com/%s/permissions' % (
        facebook_id
    )
    h = httplib2.Http()
    h.request(url, 'DELETE')[1]


@app.route('/disconnect')
def disconnect():
    """Common endpoint to log out
    """
    if 'provider' in login_session:
        # If user logged in, log out using the correct
        # provider and clean session data
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been successfully logged out.")
    else:
        # User wasn't logged in, nothing to do
        flash("You were not logged in")
    return redirect(url_for('genres'))


def create_user(login_session):
    """Create a new user based on data stored in login_session
    Params: loggin_session object
    Returns: user_id
    """
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    """Get user info from the database
    Params: user_id - id of the user for which to fetch data
    Returns: user object
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    """Get user id based on the email
    Params: email - email of the user
    Returns: user_id if exists, else None
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/genres/json')
def genres_json():
    """API endpoint to get the full list of genres and movies
    """
    genres = session.query(Genre).all()
    results = {}
    for genre in genres:
        movies = session.query(Movie).filter_by(
            genre_id=genre.id
        )
        results[genre.name] = [movie.serialize for movie in movies]

    return jsonify(results)


@app.route('/genres/<int:genre_id>/json')
def genre_json(genre_id):
    """API endpoint to get the full list of genres and movies
    """
    try:
        genre = session.query(Genre).filter_by(id=genre_id).one()
    except:
        return jsonify({})
    movies = session.query(Movie).filter_by(
        genre_id=genre_id
    )
    print [movie.serialize for movie in movies]
    return jsonify({genre.name: [movie.serialize for movie in movies]})


@app.route('/genres/')
def genres():
    """Enddpoint to show all the genres and a list of latest movies
    """
    genres = session.query(Genre).all()
    movies = session.query(Movie).order_by(Movie.created_date.desc()).limit(4)
    new_movies = []
    for movie in movies:
        genre = session.query(Genre).filter_by(id=movie.genre_id).one()
        movie.genre_name = genre.name
        new_movies.append(movie)
    logged_in = 'username' in login_session
    return render_template(
        'genres.html', genres=genres, movies=new_movies, logged_in=logged_in
    )


@app.route('/genres/<int:genre_id>/')
def movie_list_for_genre(genre_id):
    """Endpoint to show all the movies for a given genre
    """
    genres = session.query(Genre).all()
    genre = session.query(Genre).filter_by(
        id=genre_id).one()
    movies = session.query(Movie).filter_by(
        genre_id=genre_id
    )
    logged_in = 'username' in login_session
    return render_template(
        'movie_list.html', genres=genres, genre=genre,
        movies=movies, logged_in=logged_in
    )


@app.route('/genres/<int:genre_id>/new/', methods=['GET', 'POST'])
def new_movie(genre_id):
    """Endpoint to create a new movie
    """
    if 'username' not in login_session:
        # If no user is logged in, redirect to the login page
        return redirect('/login')
    if request.method == 'POST':
        # Handle form submission
        movie = Movie(
            name=request.form['name'], genre_id=request.form['genre_id'],
            description=request.form['description'],
            year=request.form['year'], director=request.form['director'],
            user_id=login_session['user_id']
        )
        session.add(movie)
        session.commit()
        flash('Added %s movie', request.form['name'])
        return redirect(
            url_for('movie_list_for_genre', genre_id=request.form['genre_id'])
        )
    else:
        # Display adding new movie page
        genres = session.query(Genre).all()
        selected = genre_id
        years = range(1900, datetime.today().year+1)
        return render_template(
            'new.html', genres=genres, selected=selected, years=years
        )


@app.route('/genres/<int:genre_id>/<int:movie_id>/edit/',
           methods=['GET', 'POST'])
def edit_movie(genre_id, movie_id):
    """Endpoint to edit an existing movie
    """
    if 'username' not in login_session:
        # If no user is logged in, redirect to the login page
        return redirect('/login')
    movie = session.query(Movie).filter_by(id=movie_id).one()
    if movie.user_id != login_session['user_id']:
        # If logged in user is not the same as the author of the movie
        # return an error message
        return 'You are not allowed to access this content'
    if request.method == 'POST':
        # Handle form submission
        if 'name' in request.form:
            movie.name = request.form['name']
        if 'description' in request.form:
            movie.description = request.form['description']
        if 'year' in request.form:
            movie.year = request.form['year']
        if 'director' in request.form:
            movie.director = request.form['director']
        session.add(movie)
        session.commit()
        flash('Movie ' + movie.name + ' edited')
        return redirect(url_for('movie_list_for_genre', genre_id=genre_id))
    else:
        # Display editing movie page
        genres = session.query(Genre).all()
        genre = session.query(Genre).filter_by(id=genre_id).one()
        years = range(1900, datetime.today().year+1)
        selected = int(movie.year)
        return render_template(
            'edit.html', genres=genres, genre=genre, movie=movie,
            years=years, selected=selected
        )


@app.route('/genres/<int:genre_id>/<int:movie_id>/delete/',
           methods=['GET', 'POST'])
def delete_movie(genre_id, movie_id):
    """Endpoint to delete an existing movie
    """
    if 'username' not in login_session:
        # If no user is logged in, redirect to the login page
        return redirect('/login')
    movie = session.query(Movie).filter_by(id=movie_id).one()
    if movie.user_id != login_session['user_id']:
        # If logged in user is not the same as the author of the movie
        # return an error message
        return 'You are not allowed to access this content'
    if request.method == 'POST':
        # Handle form submission
        session.delete(movie)
        session.commit()
        flash('Movie ' + movie.name + ' deleted')
        return redirect(url_for('movie_list_for_genre', genre_id=genre_id))
    else:
        # Display editing movie page
        genre = session.query(Genre).filter_by(id=genre_id).one()
        return render_template(
            'delete.html', genre=genre, movie=movie
        )


@app.route('/genres/<int:genre_id>/<int:movie_id>/view/')
def show_movie(genre_id, movie_id):
    """Endpoint to view movie details
    """
    movie = session.query(Movie).filter_by(id=movie_id).one()
    own_content = 'user_id' in login_session \
        and movie.user_id == login_session['user_id']
    return render_template(
        'movie.html', genre_id=genre_id, movie=movie,
        own_content=own_content
    )

if __name__ == "__main__":
    init_session()
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
