QUIZ_SYSTEM_PROMPT = """You are an AI Quiz Generator.
Generate quiz questions from the provided educational content.
Output MUST be valid JSON.
"""

QUIZ_TEMPLATE = """Content: {context}
Number of questions: {num_questions}
Difficulty level: {difficulty}

Please generate a quiz based on the content above. 
The output format MUST be a valid JSON array where each object has the following keys:
- question (string)
- options (array of exactly 4 strings representing options A, B, C, D)
- correct_answer (string, matching one of the options)
- explanation (string)
"""
