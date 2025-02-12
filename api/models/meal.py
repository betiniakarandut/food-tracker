from pydantic import BaseModel

class Meal(BaseModel):
    meal_time: str
    participant_id: str