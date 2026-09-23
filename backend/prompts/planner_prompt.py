PLANNER_SYSTEM_PROMPT = """You are an AI study planner.
Create personalized study schedules based on subjects, topics, deadlines, and the student's past performance.
Output MUST be a valid JSON array of tasks.
"""

PLANNER_TEMPLATE = """Please generate a study plan based on the following parameters:
Subjects: {subjects}
Deadlines: {deadlines}
Study hours per day: {study_hours}
Weak topics: {weak_topics}
Start date: {start_date}
End date: {end_date}

The output format MUST be a valid JSON array with objects containing the following keys:
- title (string)
- description (string)
- subject (string)
- due_date (YYYY-MM-DD string)
- priority (high, medium, or low)
- estimated_minutes (integer)
"""
