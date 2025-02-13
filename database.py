import os
from dotenv import load_dotenv
from databases import Database
import sqlalchemy

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Check if DATABASE_URL is set
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Create a Database instance
database = Database(DATABASE_URL)

# SQLAlchemy metadata for table definitions
metadata = sqlalchemy.MetaData()

# Define meals table
meals = sqlalchemy.Table(
    "meals",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("participant_id", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("meal_time", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("date_served", sqlalchemy.Date, nullable=False),
    sqlalchemy.Column("time_served", sqlalchemy.Time),
    sqlalchemy.UniqueConstraint("participant_id", "meal_time", "date_served", name="uq_meal_serving")
)

# Create an engine
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)  # Creates tables if they don't exist
