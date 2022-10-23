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

	def __init__(self, username, password):
		self.spots = {}
		self.hunted_states = []
		self.username = username
		self.password = password
		self.bearer_token = None

		self.login()
		self.populate_hunted_states()

	def login(self):
		# Two POST requests are needed to complete the login flow. Let's build the first POST request,
		# which retreives a 'code' that we then need to redeem for a bearer token.
		params = {'redirect_uri': 'https://pota.app/', 'response_type': 'code', 'client_id': self.client_id, 'identity_provider': 'COGNITO', 'code_challenge': self.code_challenge, 'code_challenge_method': 'S256'}
		post_payload = {'_csrf': self.xsrf_token, 'username': self.username, 'password': self.password}
		post_headers = {'Cookie': 'XSRF-TOKEN={}'.format(self.xsrf_token)}
		r = requests.post('https://{}{}'.format(self.cognito_host, self.login_endpoint), params=params, data=post_payload, headers=post_headers, allow_redirects=False)
		if r.status_code != 302:
			print('Something went wrong logging in at step 1 (retreive code)')
			quit()
		code = r.headers['Location'].split('=')[1]

		# Now using the 'code' fetched from the first request, we need to redeem it for a bearer token.
		post_payload = {'grant_type': 'authorization_code', 'code': code, 'client_id': self.client_id, 'redirect_uri': 'https://pota.app/', 'code_verifier': self.code_verifier}
		r = requests.post('https://{}{}'.format(self.cognito_host, self.token_endpoint), data=post_payload)
		if r.status_code != 200:
			print('Something went wrong logging in at step 2 (redeeming code for bearer token)')
			quit()
		
		self.bearer_token = r.json()['id_token']

	def populate_hunted_states(self):
		my_headers = {'Authorization': self.bearer_token}
		r = requests.get('https://{}{}'.format(self.host, self.us_states_hunted_endpoint), headers=my_headers)
		if r.status_code != 200:
			print('Something went wrong populating hunted states.')
			quit()
		for state in r.json():
			self.hunted_states.append(state['locationDesc'])

	def refresh_spots(self):
		r = requests.get('https://{}{}'.format(self.host, self.spots_endpoint))
		if r.status_code != 200:
			print('Something went wrong when pulling spots.')
			quit()
		self.spots = r.json()

	def filtered_spots(self):
		self.refresh_spots()
		results = []
		for spot in self.spots:
			if spot['mode'] != 'CW':
				continue
			if not spot['locationDesc'].startswith('US'):
				continue
			for loc in spot['locationDesc'].split(','):
				if loc not in self.hunted_states:
					results.append(spot)
					break
		return results

if __name__ == '__main__':
	pota = POTAClient('', '')
	while True:
		for spot in pota.filtered_spots():
			# Gets UTC time
			utc = spot['spotTime'].split('T')[1]
			print('{} is on {} from {}({}) in {} {}'.format(spot['activator'], spot['frequency'], spot['name'], spot['reference'], spot['locationDesc'], utc))
		time.sleep(129)