import os
from dotenv import load_dotenv
from fastapi import Request, APIRouter, HTTPException, BackgroundTasks, Depends
from ..models.meal import Meal
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse
import psycopg2
import asyncio
import json
import sys

load_dotenv()

router = APIRouter()

# Dictionary to store awaiting participants (key: participant_id, value: (meal_time, expiry_time,))
awaiting_participants = {}

# Dictionary to store connected clients
connected_clients = {}

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Database connection and table creation (Do this ONCE, at startup):
try:
    conn = psycopg2.connect(DATABASE_URL)
    with conn:
        with conn.cursor() as cursor:
            # Ensure schema exists before creating tables
            cursor.execute("CREATE SCHEMA IF NOT EXISTS food_tracker_schema")

            # Now create the table inside the schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS food_tracker_schema.meals (
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
async def serve_food(meal: Meal, background_tasks: BackgroundTasks, db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        last_four_digits = meal.participant_id
        full_participant_id = f"{last_four_digits.zfill(4)}"
        meal_time = meal.meal_time

        if not is_valid_participant_id(last_four_digits):
            raise HTTPException(status_code=400, detail="Invalid participant ID. Please enter 4 digits between 0000 and 0350.")

        try:
            with db:
                with db.cursor() as cursor:
                    cursor.execute("""
                        SELECT 1 FROM food_tracker_schema.meals 
                        WHERE participant_id = %s AND meal_time = %s AND date_served = %s
                    """, (full_participant_id, meal_time, datetime.now().date().isoformat()))

                    if cursor.fetchone():
                        return {"message": f"Participant {full_participant_id} has already been served {meal_time} today!"}

                    # Check if the participant is already awaiting service (AFTER checking the database)
                    if full_participant_id in awaiting_participants and awaiting_participants[full_participant_id][0] == meal_time:
                        if awaiting_participants[full_participant_id][1] > datetime.now():
                            return {
                                "message": f"Participant {full_participant_id} is already awaiting service for {meal_time}."
                            }

                    expiry_time = datetime.now() + timedelta(minutes=12)
                    awaiting_participants[full_participant_id] = (meal_time, expiry_time)  # Add to awaiting only if not already served
                    background_tasks.add_task(remove_from_awaiting, full_participant_id)

                    return {
                        "message": f"Participant {full_participant_id} is awaiting service for {meal_time}. Serving will be confirmed shortly."
                    }

        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/food_is_served")
async def food_is_served(meal: Meal, db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        last_four_digits = meal.participant_id
        full_participant_id = f"{last_four_digits.zfill(4)}" 
        meal_time = meal.meal_time

        # Check if the participant is awaiting service (using the consistent ID format)
        if full_participant_id not in awaiting_participants or awaiting_participants[full_participant_id][0] != meal_time:
            raise HTTPException(status_code=400, detail=f"Participant {full_participant_id} is not awaiting service for {meal_time}.")

        date_served = datetime.now().date().isoformat()
        time_served = datetime.now().time().strftime("%H:%M")

        try:
            with db:
                with db.cursor() as cursor:
                    cursor.execute("""
                        SELECT 1 FROM food_tracker_schema.meals
                        WHERE participant_id = %s AND meal_time = %s AND date_served = %s
                    """, (full_participant_id, meal_time, date_served))

                    if cursor.fetchone():
                        raise HTTPException(status_code=400, detail=f"{full_participant_id} has already been served {meal_time} today!")

                    cursor.execute("""
                        INSERT INTO food_tracker_schema.meals (participant_id, meal_time, date_served, time_served)
                        VALUES (%s, %s, %s, %s)
                    """, (full_participant_id, meal_time, date_served, time_served))

                    print(awaiting_participants)

                    del awaiting_participants[full_participant_id]

                    for queue in connected_clients.values():
                        await queue.put("update")

                    return {"message": f"{meal_time.capitalize()} served to {full_participant_id} at {time_served}."}

        except psycopg2.Error as e:
            print(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MSP has been served before!")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/awaiting_participants")
async def get_awaiting_participants(request: Request) -> StreamingResponse:
    """
    Stream updates for awaiting participants using Server-Sent Events (SSE).
    """
    participant_id = request.headers.get("X-Participant-ID")
    if participant_id not in connected_clients:
        connected_clients[participant_id] = asyncio.Queue()

    async def send_updates():
        while True:
            try:
                # Format awaiting participants for SSE updates
                formatted_awaiting = {
                    participant: {
                        "meal_time": meal_time,
                        "expiry_time": expiry_time.timestamp() * 1000,  # Convert to milliseconds
                    }
                    for participant, (meal_time, expiry_time,) in awaiting_participants.items()
                }
                yield f"data: {json.dumps(formatted_awaiting)}\n\n"
                await asyncio.sleep(0.2) 
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error sending SSE update: {str(e)}")
                break

    return StreamingResponse(send_updates(), media_type="text/event-stream")


async def remove_from_awaiting(participant_id: str) -> None:
    """
    Removes a participant from the awaiting list after 12 minutes.
    """
    await asyncio.sleep(12 * 60)
    if participant_id in awaiting_participants:
        del awaiting_participants[participant_id]
    

@router.delete("/connected_clients/{participant_id}")
async def remove_connected_client(participant_id: str) -> dict:
    """
    Removes a connected client from the list.
    """
    try:
        if participant_id in connected_clients:
            del connected_clients[participant_id]
            return {"message": f"Client {participant_id} removed."}
        return {"message": f"Client {participant_id} not found."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/meal_counts")
async def get_meal_counts(meal_time: str, db: psycopg2.extensions.connection = Depends(get_db)):
    date_served = datetime.now().date().isoformat()

    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM food_tracker_schema.meals 
                    WHERE meal_time = %s AND date_served = %s
                """, (meal_time, date_served))
                count = cursor.fetchone()[0]
                return {meal_time: f"{count} persons served"}

    except psycopg2.Error as e:
        return {meal_time: f"Error fetching meal counts: {str(e)}"}


@router.get("/participant_status/{participant_id}")
async def get_participant_status(participant_id: str, meal_time: str, db: psycopg2.extensions.connection = Depends(get_db)):
    """
    Get the current status of a participant for a specific meal time.
    """
    try:
        # Validate the participant ID
        if not is_valid_participant_id(participant_id):
            raise HTTPException(status_code=400, detail="Invalid participant ID. Please enter 4 digits between 0000 and 0350.")

        full_participant_id = f"msp_{participant_id.zfill(4)}"
        date_served = datetime.now().date().isoformat()

        if full_participant_id in awaiting_participants and awaiting_participants[full_participant_id][0] == meal_time:
            return {
                "status": "awaiting_service",
                "message": f"Participant {full_participant_id} is awaiting service for {meal_time}."
            }

        try:
            with db:
                with db.cursor() as cursor:
                    cursor.execute("""
                        SELECT 1 FROM food_tracker_schema.meals 
                        WHERE participant_id = %s AND meal_time = %s AND date_served = %s
                    """, (full_participant_id, meal_time, date_served))
                    if cursor.fetchone():
                        return {
                            "status": "served",
                            "message": f"Participant {full_participant_id} has already been served {meal_time} today."
                        }
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        # If not found in awaiting or served lists, the participant is not registered
        return {
            "status": "not_registered",
            "message": f"Participant {full_participant_id} is not registered for {meal_time}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/remaining_participants/{meal_time}")
async def get_remaining_participants(meal_time: str, db: psycopg2.extensions.connection = Depends(get_db)):
    """
    Endpoint to get a list of participant IDs who have not requested a meal at a given meal_time.
    """
    try:
        date_served = datetime.now().date().isoformat()

        try:
            with db:
                with db.cursor() as cursor:
                    cursor.execute("""
                        SELECT participant_id FROM food_tracker_schema.meals 
                        WHERE meal_time = %s AND date_served = %s
                    """, (meal_time, date_served))
                    served_participants = {f"msp_{str(row[0]).zfill(4)}" for row in cursor.fetchall()}

                    all_participants = {f"msp_{str(i).zfill(4)}" for i in range(1, 351)}
                    remaining_participants = list(all_participants - served_participants)
                    remaining_participants.sort()

                    return {"meal_time": meal_time, "remaining_participants": remaining_participants}

        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def is_valid_participant_id(participant_id: str) -> bool:
    """
    Validates participant ID to ensure it is a 4-digit number between 0000 and 0350.
    """
    if len(participant_id) != 4 or not participant_id.isdigit():
        return False
    num = int(participant_id)
    return 1 <= num <= 351
