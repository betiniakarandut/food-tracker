import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from ..models.meal import Meal
from datetime import datetime
import psycopg2
import sys

load_dotenv()

router = APIRouter()

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set.")

try:
    conn = psycopg2.connect(DATABASE_URL)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS food_tracker_schema")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meals(
                    id SERIAL PRIMARY KEY,
                    participant_id VARCHAR(255) NOT NULL,
                    meal_time VARCHAR(50) NOT NULL,
                    date_served DATE NOT NULL,
                    time_served TIME,
                    UNIQUE (participant_id, meal_time, date_served)
                )
            """)
            conn.commit()
except psycopg2.Error as e:
    print(f"Error creating/connecting to database: {e}")
    print("Exiting application due to database error.")
    sys.exit(1)

def get_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if hasattr(conn, 'close') and conn:
            conn.close()


@router.post("/serve_food")
async def serve_food(meal: Meal, db: psycopg2.extensions.connection = Depends(get_db)):
    last_four_digits = meal.participant_id
    full_participant_id = f"msp_{last_four_digits.zfill(4)}"
    meal_time = meal.meal_time

    if not is_valid_participant_id(last_four_digits):
        raise HTTPException(status_code=400, detail="Invalid participant ID.")

    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT 1 FROM meals
                    WHERE participant_id = %s AND meal_time = %s AND date_served = %s
                """, (full_participant_id, meal_time, datetime.now().date().isoformat()))

                if cursor.fetchone():
                    return {"message": f"Participant {full_participant_id} has already been served {meal_time} today!"}

                date_served = datetime.now().date().isoformat()
                time_served = datetime.now().time().strftime("%H:%M")

                cursor.execute("""
                    INSERT INTO meals(participant_id, meal_time, date_served, time_served)
                    VALUES (%s, %s, %s, %s)
                """, (full_participant_id, meal_time, date_served, time_served))
                return {"message": f"{meal_time.capitalize()} served to {full_participant_id} at {time_served}."}  # Immediately served

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/meal_counts")
async def get_meal_counts(meal_time: str, db: psycopg2.extensions.connection = Depends(get_db)):
    date_served = datetime.now().date().isoformat()

    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM meals
                    WHERE meal_time = %s AND date_served = %s
                """, (meal_time, date_served))
                count = cursor.fetchone()[0]
                return {meal_time: f"{count} persons served"}

    except psycopg2.Error as e:
        return {meal_time: f"Error fetching meal counts: {str(e)}"}


@router.get("/remaining_participants/{meal_time}")
async def get_remaining_participants(meal_time: str, db: psycopg2.extensions.connection = Depends(get_db)):
    date_served = datetime.now().date().isoformat()

    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT participant_id FROM meals
                    WHERE meal_time = %s AND date_served = %s
                """, (meal_time, date_served))
                served_participants = {str(row[0]) for row in cursor.fetchall()}  # Simplified set creation

                all_participants = {f"msp_{str(i).zfill(4)}" for i in range(1, 351)}
                remaining_participants = list(all_participants - served_participants)
                remaining_participants.sort()

                return {"meal_time": meal_time, "remaining_participants": remaining_participants}

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def is_valid_participant_id(participant_id: str) -> bool:
    if len(participant_id) != 4 or not participant_id.isdigit():
        return False
    num = int(participant_id)
    return 1 <= num <= 351