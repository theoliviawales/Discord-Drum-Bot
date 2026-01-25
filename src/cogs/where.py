"""
/where Tells you where an item is located
"""

import time
import discohook
from datetime import datetime
from zoneinfo import ZoneInfo

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
	def __init__(self, id, name, nickname, date, location, row_index, row_data):
		self.id = id
		self.name = name
		self.nickname = nickname
		self.date = date
		self.location = location
		self.row_index = row_index
		self.row_data = row_data
	
	def update_location(self, location):
		self.location = location
		self.row_data[5] = location
	
	def update_date(self, date):
		self.date = date
		self.row_data[4] = date

	def __str__(self):
		return f'ID: {self.id}\nName: {self.name}\nNickname: {self.nickname}\nLast Updated:{self.date}\nLocation: {self.location}'

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
TRACKER_SPREADSHEET_ID = "1_Gd9O8Ol8kmX0AWRUjEynt9l40JlwsYLWPF_Haim6b8"
SAMPLE_RANGE_NAME = "!A1:H50"

def query_sheet(category):
	creds = service_account.Credentials.from_service_account_file(
		"credentials.json", scopes=SCOPES
  	)

	service = build("sheets", "v4", credentials=creds)
	# Call the Sheets API
	sheet = service.spreadsheets()
	
	values = None
	try:
		result = (
			sheet.values()
			.get(spreadsheetId=TRACKER_SPREADSHEET_ID, range=f'{category.upper() + SAMPLE_RANGE_NAME}', )
			.execute()
		)
		values = result.get("values", [])
	except HttpError as err:
		print(err)
		values = None
	
	return values

def update_sheet(category, values):
	creds = service_account.Credentials.from_service_account_file(
		"credentials.json", scopes=SCOPES
  	)

	service = build("sheets", "v4", credentials=creds)
	# Call the Sheets API
	sheet = service.spreadsheets()
	
	try:
		result = (
			sheet.values()
			.update(
				spreadsheetId=TRACKER_SPREADSHEET_ID, 
				range=f'{category.upper() + SAMPLE_RANGE_NAME}',
				valueInputOption='USER_ENTERED',
				body={'values': values})
			.execute()
		)
	except HttpError as err:
		print(err)
		return None
	
	return result

def build_equipment_list(category, type):
	values = query_sheet(category)

	equipment_list = []
	for row_index,row in enumerate(values):
		if row[0] == type:
			equipment_list.append(Equipment(
				id=row[1],
				name=row[2],
				nickname=row[3],
				date=row[4],
				location=row[5],
				row_index=row_index,
				row_data=row
			))
	
	return equipment_list

@discohook.command.slash(
    'where', 
	description = 'Get the location of an equipment item', 
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
	equipment_list = build_equipment_list(category, type)

	if len(equipment_list) == 0:
		text = "No equipment found."
	else:
		text = '\n'.join([f'ID [{x.id}]: {x.name} - {x.nickname} - {x.location}' for i,x in enumerate(equipment_list)])

	await interaction.response.send(text)

@discohook.command.slash(
    'assign', 
	description = 'Assign the location of an equipment item', 
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
		discohook.Option.string(
			name='id',
			description='ID of the equipment being assigned',
			required=True,
		),
		discohook.Option.string(
			name='location',
			description='New location of the equipment',
			required=True,
		),
		discohook.Option.string(
			name='date',
			description='Date when it was assigned, defaults to current day if left blank',
			required=False,
		),
	]
)
async def assign_command(interaction, category, type, id, location, date):
	equipment_list = build_equipment_list(category, type)	
	assigned_equipment = None
	for e in equipment_list:
		if e.id == id:
			assigned_equipment = e
			break
	if assigned_equipment == None:
		await interaction.response.send("No valid equipment found.")
		return
	
	if date is None:
		pst_datetime = datetime.now(ZoneInfo("America/Los_Angeles"))
		date = pst_datetime.strftime("%m/%d/%y")

	assigned_equipment.update_location(location)
	assigned_equipment.update_date(date)

	values = query_sheet(category)
	for row_index,row in enumerate(values):
		if row_index == assigned_equipment.row_index:
			values[row_index] = assigned_equipment.row_data
		
	
	result = update_sheet(category, values)

	if result is None:
		text = "Failed to update tracker sheet."
	else:
		text = "Successfully updated tracker sheet."
			
	await interaction.response.send(text)
	