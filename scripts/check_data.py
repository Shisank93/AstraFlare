import sys
from database.db import db_manager

db_manager.connect()
hotspots = db_manager.execute_query('SELECT count(*) as count FROM hotspots')
reviews = db_manager.execute_query('SELECT count(*) as count FROM reviews')
print(f"Database Hotspots: {hotspots[0]['count'] if hotspots else 0}")
print(f"Database Reviews: {reviews[0]['count'] if reviews else 0}")
