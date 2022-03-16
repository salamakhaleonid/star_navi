from test_task import app,db
from flask import request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import uuid # for public id
# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps
from test_task.models import User,Like,Post


# standart jwt aut wrap function
def token_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None
		# jwt is passed in the request header
		if 'x-access-token' in request.headers:
			token = request.headers['x-access-token']
		# return 401 if token is not passed
		if not token:
			return jsonify({'message' : 'Token is missing !!'}), 401

		try:
			# decoding the payload to fetch the stored details
			data = jwt.decode(token, app.config['SECRET_KEY'])
			current_user = User.query\
				.filter_by(public_id = data['public_id'])\
				.first()
		except:
			return jsonify({
				'message' : 'Token is invalid !!'
			}), 401
		# returns the current logged in users contex to the routes
		return f(current_user, *args, **kwargs)

	return decorated





# logging user with email and password
@app.route('/api/login', methods =['POST'])
def login():
	# creates dictionary of form data
	auth = request.form
	# print(auth.get('email'),auth.get('password'))
	if not auth or not auth.get('email') or not auth.get('password'):
		# returns 401 if any email or / and password is missing
		return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
		)

	user = User.query\
		.filter_by(email = auth.get('email'))\
		.first()

	if not user:
		# returns 401 if user does not exist
		return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
		)

	if check_password_hash(user.password, auth.get('password')):
		# generates the JWT Token
		token = jwt.encode({'public_id': user.public_id,'exp' : datetime.utcnow() + timedelta(minutes = 30)}, app.config['SECRET_KEY'])
		user.last_activity_time = datetime.now()
		user.last_login_time = datetime.now()
		db.session.commit()
		return make_response(jsonify({'token' : token.decode('UTF-8')}), 201)
	# returns 403 if password is wrong
	return make_response(
		'Could not verify',
		403,
		{'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
	)

# signup with name email and password
@app.route('/api/signup', methods =['POST'])
def signup():
	# creates a dictionary of the form data
	data = request.form

	# gets name, email and password
	name = data.get('name')
	email = data.get('email')
	password = data.get('password')
	user = User.query\
		.filter_by(email = email)\
		.first()
	if not user:
		# database ORM object
		# sign up is not treated as an activity vs the service, ie last_activity_time is not updated
		user = User(
			public_id=str(uuid.uuid4()),
			name = name,
			email = email,
			password = generate_password_hash(password),
			creation_time = datetime.now()
		)
		# insert user
		db.session.add(user)
		db.session.commit()

		return make_response('Successfully registered.', 201)
	else:
		# returns 202 if user already exists
		return make_response('User already exists. Please Log in.', 202)

# post creation based on post text and logined user pub id
@app.route('/api/post', methods =['POST'])
@token_required
def create_post(current_user):
	current_user.last_activity_time = datetime.now()
	db.session.commit()  #  even if unsuccessfull the activity is registered
	data = request.form
	text = data.get('text')
	if not text:
		return make_response('No text in post', 401)
	post_public_id=str(uuid.uuid4())
	post = Post(
			public_id=post_public_id,
			text=text,
		    user_public_id=current_user.public_id
	)
	db.session.add(post)
	db.session.commit()
	return make_response('Successfully posted. public_id is {}'.format(post_public_id), 201)

# creates like record based on logined user and the post pub id (if not already present)
@app.route('/api/like', methods =['POST'])
@token_required
def like_post(current_user):
	current_user.last_activity_time = datetime.now()
	db.session.commit()
	data = request.form
	post_public_id = data.get('post_public_id')
	if not post_public_id:
		return make_response('Post public_id is missing', 401)
	user_public_id = current_user.public_id
	post = Post.query.filter_by(public_id=post_public_id).first()
	if not post:
		return make_response('Post does not exist.', 401)
	like = Like.query.filter_by(post_public_id=post_public_id,user_public_id=user_public_id).first()
	if not like:
		like = Like(
			post_public_id = post_public_id,
		    user_public_id=current_user.public_id,
			creation_time=datetime.now()
		)
		db.session.add(like)
		db.session.commit()
		return make_response('Successfully liked.', 201)
	else:
		return make_response('You liked the post already', 202)

# revoves like record based on logined user pub id and the post pub id (if present)
@app.route('/api/unlike', methods =['POST'])
@token_required
def unlike_post(current_user):
	current_user.last_activity_time = datetime.now()
	db.session.commit()
	data = request.form
	post_public_id = data.get('post_public_id')
	if not post_public_id:
		return make_response('Post public_id is missing', 401)
	user_public_id = current_user.public_id
	post = Post.query.filter_by(public_id=post_public_id).first()
	if not post:
		return make_response('Post does not exist.', 401)
	like = Like.query.filter_by(post_public_id=post_public_id,user_public_id=user_public_id).first()
	if like:
		db.session.delete(like)
		db.session.commit()
		return make_response('Successfully unliked.', 201)
	else:
		return make_response('You never liked this stupid post', 202)

# if posts can not be removed we calculate the number of likes that had been created (and not removed with unlike)
# for all the existing posts based on date_from and date_to
@app.route('/api/analitics/', methods =['GET'])
def number_like_anal():
	date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
	date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
	like = Like.query.filter(Like.creation_time >= date_from, Like.creation_time <= date_to)
	n=0
	for l in like:
		n+=1
	out = {"num_like_from_to":n}
	return make_response(out, 201)

# display the analitics for the user based on its pub id
@app.route('/api/user_activity_analitics/', methods =['GET'])
def user_act_anal():
	user_public_id = request.args.get('user_public_id')
	user = User.query.filter_by(public_id=user_public_id).first()
	last_login_time = user.last_login_time
	last_activity_time = user.last_activity_time
	out = {"l_login_t":str(last_login_time),"l_request_t":str(last_activity_time)}
	return make_response(out, 201)