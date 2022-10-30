import requests
import time

class DXSummitClient:
	host = 'www.dxsummit.fi'
	spots_endpoint = '/api/v1/spots'

	def __init__(self):
		pass

	def fetch_spots(self):
		r = requests.get('http://{}{}'.format(self.host, self.spots_endpoint))
		if r.status_code != 200:
			print('Something went wrong fetching spots.')
		return r.json()