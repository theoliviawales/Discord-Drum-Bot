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

EQUIPMENT_TYPES = set(
	[
		'Instrument',
		'Harness',
		'Stand',
		'Pad'
	]
)

class Equipment():
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
SAMPLE_RANGE_NAME = "!A1:H50"

@discohook.command.slash(
    'where', 
	description = 'Get the location of an equipment item!', 
	guild_id = '1464453860805574760',
	options = [
		discohook.Option.string(
			name='category',
			description='Instrument category',
			required=True,
			choices=[
                discohook.Choice(name="Snare", value="Snare"),
                discohook.Choice(name="Bass", value="Bass"),
                discohook.Choice(name="Tenors", value="Tenors"),
				discohook.Choice(name="Cymbals", value="Cymbals"),
            ],),
		discohook.Option.string(
			name='type',
			description='Equipment type  (Instrument, Harness, Stand, Pad)',
			required=True,
			choices=[
				discohook.Choice(name="Instrument", value="Instrument"),
				discohook.Choice(name="Harness", value="Harness"),
				discohook.Choice(name="Stand", value="Stand"),
				discohook.Choice(name="Pad", value="Pad"),
			],),
		]
)
async def where_command(interaction, category, type):
	creds = service_account.Credentials.from_service_account_file(
		"credentials.json", scopes=SCOPES
  	)

	equipment_list = []
	try:
		service = build("sheets", "v4", credentials=creds)
    	# Call the Sheets API
		sheet = service.spreadsheets()
		result = (
			sheet.values()
			.get(spreadsheetId=TRACKER_SPREADSHEET_ID, range=f'{category.upper() + SAMPLE_RANGE_NAME}', )
			.execute()
		)
		values = result.get("values", [])

		if not values:
			print("No data found.")
			return

		for row in values:
			if row[0] == type:
				equipment_list.append(Equipment(
					id=row[1],
					name=row[2],
					nickname=row[3],
					date=row[4],
					location=row[5]
				))

	except HttpError as err:
		print(err)
	if len(equipment_list) == 0:
		text = "No equipment found."
	else:
		text = '\n'.join([f'[{i}]: {x.id} - {x.name}' for i,x in enumerate(equipment_list)])

	await interaction.response.send(text)