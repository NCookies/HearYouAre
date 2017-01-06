from src import db

d = db.DBHandler('res/hear.db')
data = d.get_music_list()
