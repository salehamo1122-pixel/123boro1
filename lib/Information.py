from .library import *

admin_user_id = 8329942809 #<--- آیدی ادمین
api_id = 32600554 #<--- آی پی آی آیدی
api_hash = 'fc196ccdddc447849754a56edf0a11b1' #<--- ای پی آی هش
helper_username = 'Saleh4E12bot' #<--- یوزر ربات هلپر بدون @
bot_token = '8660335838:AAG1Ez_zNVQUObR2ktrDkZMFVOByLy4ZeyE' #<--- توکن ربات هلپر

client_id = '01e7dc6b41c3471b94efe87abeb05919'
client_secret = '4f5f93af1ced4b0d9ba8440606803639'

client = TelegramClient('TRself-MT', api_id, api_hash)
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
