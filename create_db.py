from project.app import db

# Create the database and the db table
db.create_all()

# Commit the changes
db.session.commit()
