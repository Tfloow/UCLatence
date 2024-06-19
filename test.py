import sqlite3
from sqlite3 import Error
import json

# load the services.json

with open('services.json') as f:
    services = json.load(f)

service_list = list(services.keys())

# Connect to the SQLite database
conn = sqlite3.connect('data/outage.sqlite3')
cursor = conn.cursor()

# Function to create a table for a website
def create_table(website_name):
    table_name = website_name.replace('.', '_')  # Replace dots with underscores for table name
    table_name = table_name.replace('-', '_')  # Replace dashes with underscores for table name
    print(f"Creating table {table_name}...")
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            timestamp INTEGER,
            status INTEGER,
            user INTEGER
        )
    ''')
    print(f"Table {table_name} created successfully.")    
    
    
for service in service_list:
    create_table(service)
    
# Commit the changes and close the connection
conn.commit()
conn.close()