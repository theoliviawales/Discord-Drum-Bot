"""
/where Tells you where an item is located
"""

import time
import discohook

import os.path

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class Instrument():
  def __init__(self, id, name, nickname, date, location):
    self.id = id
    self.name = name
    self.nickname = nickname
    self.date = date
    self.location = location
  
  def __str__(self):
    return f'ID: {self.id}\nName: {self.name}\nNickname: {self.nickname}\nLast Updated:{self.date}\nLocation: {self.location}'


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
TRACKER_SPREADSHEET_ID = "1_Gd9O8Ol8kmX0AWRUjEynt9l40JlwsYLWPF_Haim6b8"
SAMPLE_RANGE_NAME = "!A1:E50"

@discohook.command.slash(
    'where', 
	description = 'Get the location of an equipment item!', 
	guild_id = '1464453860805574760',
	options = [
		discohook.Option.string(
			name='instrument',
			description='Type of instrument (Bass, Snare, ...)',
			required=True),
		discohook.Option.string(
			name='id',
			description='ID of the equipment being queried',
			required=True)
		]
)
async def where_command(interaction, instrument, id):
	creds = service_account.Credentials.from_service_account_file(
		"credentials.json", scopes=SCOPES
  	)

	returned_instrument = None
	try:
		service = build("sheets", "v4", credentials=creds)
    	# Call the Sheets API
		sheet = service.spreadsheets()
		result = (
			sheet.values()
			.get(spreadsheetId=TRACKER_SPREADSHEET_ID, range=f'{instrument.upper() + SAMPLE_RANGE_NAME}', )
			.execute()
		)
		values = result.get("values", [])

		if not values:
			print("No data found.")
			return

		for row in values:
			print(row, id)
			if (row[0] == id):
				returned_instrument = Instrument(row[0], row[1], row[2], row[3], row[4])
				break
	except HttpError as err:
		print(err)
	if returned_instrument is None:
		text = "Instrument not found"
	else:
		text = str(returned_instrument)

	await interaction.response.send(text)