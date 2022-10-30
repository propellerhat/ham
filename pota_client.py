import requests
import time

class POTAClient:
	host = 'api.pota.app'
	cognito_host = 'parksontheair.auth.us-east-2.amazoncognito.com'
	spots_endpoint = '/spot/activator'
	us_states_hunted_endpoint = '/user/award/progress/hunter/usstates'
	login_endpoint = '/login'
	token_endpoint = '/oauth2/token'
	# Filthy constants needed for Amazon Cognito login
	xsrf_token = '018a8074-0847-4b89-9547-fef6e9acd7dd'
	code_challenge = 'KZioGvQiM97smdhulcVyOk2LKAVDtWXBgi2uZ2FCq2w'
	client_id = '7hluqct0n2nckib7i7sd5753oa'
	code_verifier = 'YfjOQj1sYtmXdnk4zd1TfYHjGGCHjcE2TUDa9IcrXrO3CuJxwEdoDGdoGSbUYzyx1zmUDUE6xGLGlVlNZf8mYm9DTck0zSRYAEGBVCVaGp4jbytlh8sUgBSBOywiUHX0'

	def __init__(self):
		self.spots = {}
		self.hunted_states = []
		self.username = None
		self.bearer_token = None

	def login(self, username, password):
		self.username = username
		# Two POST requests are needed to complete the login flow. Let's build the first POST request,
		# which retreives a 'code' that we then need to redeem for a bearer token.
		params = {'redirect_uri': 'https://pota.app/', 'response_type': 'code', 'client_id': self.client_id, 'identity_provider': 'COGNITO', 'code_challenge': self.code_challenge, 'code_challenge_method': 'S256'}
		post_payload = {'_csrf': self.xsrf_token, 'username': self.username, 'password': password}
		post_headers = {'Cookie': 'XSRF-TOKEN={}'.format(self.xsrf_token)}
		r = requests.post('https://{}{}'.format(self.cognito_host, self.login_endpoint), params=params, data=post_payload, headers=post_headers, allow_redirects=False)
		if r.status_code != 302:
			print('Something went wrong logging in at step 1 (retreive code)')
		code = r.headers['Location'].split('=')[1]

		# Now using the 'code' fetched from the first request, we need to redeem it for a bearer token.
		post_payload = {'grant_type': 'authorization_code', 'code': code, 'client_id': self.client_id, 'redirect_uri': 'https://pota.app/', 'code_verifier': self.code_verifier}
		r = requests.post('https://{}{}'.format(self.cognito_host, self.token_endpoint), data=post_payload)
		if r.status_code != 200:
			print('Something went wrong logging in at step 2 (redeeming code for bearer token)')
		self.bearer_token = r.json()['id_token']
		self.populate_hunted_states()

	def populate_hunted_states(self):
		my_headers = {'Authorization': self.bearer_token}
		r = requests.get('https://{}{}'.format(self.host, self.us_states_hunted_endpoint), headers=my_headers)
		if r.status_code != 200:
			print('Something went wrong populating hunted states.')
		for state in r.json():
			self.hunted_states.append(state['locationDesc'])

	def fetch_spots(self):
		r = requests.get('https://{}{}'.format(self.host, self.spots_endpoint))
		if r.status_code != 200:
			print('Something went wrong when pulling spots.')
		return r.json()