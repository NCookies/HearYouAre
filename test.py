from src import db

d = db.DBHandler('res/hear.db')
data = d.get_music_list()
print type(data)
print data[:1024]
