#!/usr/bin/env python3

import requests, xml.etree.ElementTree as ET, base64, math
from sys import argv

API = 'http://192.168.0.1/api'
USERNAME = 'admin'
PASSWORD = 'admin'

def xml_convert(json):
	header = '<?xml version="1.0" encoding="UTF-8" ?>'
	request = '<request>'

	for key in json:
		request += '<{0}>{1}</{0}>'.format(key, json[key])
	
	request += '</request>'
	return header + request

def xml_parse(xml):
	data = ET.fromstring(xml)
	json = {}

	for child in data:
		json[child.tag] = child.text

	if len(json):
		return json
	else:
		return data.text

def get(endpoint):
	try:
		return xml_parse(
			requests.get(API + endpoint).text
		)
	except:
		print("[!] Error getting data from " + endpoint)
		return None

def post(endpoint, data):
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
	}

	try:
		headers['__RequestVerificationToken'] = get('/webserver/token')['token']

		return xml_parse(requests.post(
			API + endpoint,
			data = xml_convert(data),
			headers = headers).text
		)
	except:
		print("[!] Error posting data to " + endpoint)
		return None

def mb_convert(val):
	return str(round(int(val) / (1024 * 1024), 2)) + ' MB'

def kb_convert(val):
	return str(round(int(val) / 1024, 2)) + ' KB'

def time_convert(val):
	val = int(val)

	hours = math.floor(val / (3600))
	minutes = math.floor((val % (3600)) / 60)
	secs = math.floor((val % (3600)) % 60)

	return '{0}:{1}:{2}'.format(hours, str(minutes).zfill(2), str(secs).zfill(2))

# -----------------------------------
def login(username, password):
	credentials = {
		'Username': username,
		'Password': base64.b64encode(password.encode()).decode()
	}

	post('/user/login', credentials)

def logout():
	print(post('/user/logout', { 'Logout': 1 }))

def monitor():
	month_stats = get('/monitoring/month_statistics')
	traffic_stats = get('/monitoring/traffic-statistics')
	connection = get('/dialup/mobile-dataswitch')

	if connection['dataswitch']:
		print("Connection Status: CONNECTED\n")
	else:
		print("Connection Status: DISCONNECTED\n")
	print('Connection Time: {0}\nReceived / Sent: {1} / {2}\nDownload Rate: {3}\nUpload Rate: {4}'.format(
		time_convert(traffic_stats['CurrentConnectTime']),
		mb_convert(traffic_stats['CurrentDownload']),
		mb_convert(traffic_stats['CurrentUpload']),
		kb_convert(traffic_stats['CurrentDownloadRate']),
		kb_convert(traffic_stats['CurrentUploadRate'])
	))
	print('\nMonthly Download: {0}\nMonthly Upload: {1}'.format(
		mb_convert(month_stats['CurrentMonthDownload']),
		mb_convert(month_stats['CurrentMonthUpload'])
	))

def toggle_dataswitch(switch):
	login(USERNAME, PASSWORD)
	
	if post('/dialup/mobile-dataswitch', { 'dataswitch': switch }) == 'OK':
		if switch:
			print("Connecting to network")
		else:
			print("Network disconnected")
	else:
		print("Failed to toggle data")

def reboot():
	login(USERNAME, PASSWORD)

	if post('/device/control', { 'Control': 1 }) == 'OK':
		print("Rebooting device")

# -----------------------------------

MONITORING = 'monitor'
CONNECT = 'connect'
DISCONNECT = 'disconnect'
REBOOT = 'reboot'

if len(argv) < 2:
	print("No arguments specified")
else:
	cmd = argv[1]

	if   cmd == MONITORING:
		monitor()
	elif cmd == CONNECT:
		toggle_dataswitch(1)
	elif cmd == DISCONNECT:
		toggle_dataswitch(0)
	elif cmd == REBOOT:
		reboot()
	else:
		print("Unsupported action")