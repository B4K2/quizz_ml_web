import pandas as pd
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import requests
from flask_cors import CORS
import random
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from routes.admin import admin_bp # Import your admin blueprint
import os
from models import db, Question  # Import the Question model from models.py
  

app = Flask(__name__)
app.config.from_object('config.Config')
CORS(app)

# Initialize the database
db.init_app(app)

# Register the admin blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')



def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj

# Define the Question model to match your SQL table


# Define UserPerformance model for tracking performance data
class UserPerformance(db.Model):
    __tablename__ = 'user_performance'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Auto-incremented user ID
    username = db.Column(db.String(80), nullable=False, default='anonymous')
    score = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    incorrect_answers = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)  # Corrected to 'streak'



# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/')
def landing_page():
    return render_template('landing.html')

@app.route('/start')
def index():
    question = Question.query.first()
    if not question:
        return jsonify({"error": "No question found"}), 404

    print(f"Fetched question: {question.question_text}")
    return render_template('index.html', question_text=question.question_text)

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    data = request.get_json()
    username = data.get('username', 'anonymous')  # Default to 'anonymous' if no username is provided

    # Check if user already exists
    existing_user = UserPerformance.query.filter_by(username=username).first()
    if existing_user:
        existing_user.score = 0
        existing_user.correct_answers = 0
        existing_user.incorrect_answers = 0
        existing_user.streak = 0

        # Commit the reset stats to the database
        db.session.commit()

        user_id = existing_user.id
    else:
        # Create a new user if it doesn't exist
        new_user = UserPerformance(username=username)
        db.session.add(new_user)
        db.session.commit()
        user_id = new_user.id

    return jsonify({'user_id': user_id, 'message': 'New quiz started'})



@app.route('/next_question', methods=['POST'])
def next_question():
    user_data = request.json
    print("Received user data:", [user_data])  # Wrap user_data in a list

    # Ensure user_data is not empty and contains necessary fields
    if not user_data or not isinstance(user_data, dict):
        return jsonify({"error": "Invalid user data format"}), 400

    previous_questions = user_data.get('previous_questions', [])  # Get list of previously asked questions

    # Wrap user_data in a list as required by the ML API
    ml_api_url = 'https://quizz-ml.onrender.com/next'
    try:
        response = requests.post(ml_api_url, json=[user_data])  # Send as list of dicts

        if response.status_code == 200:
            predicted_difficulty = response.json().get("Prediction", [None])[0]
            print(f"Predicted difficulty: {predicted_difficulty}")
            
            # Validate predicted difficulty
            if predicted_difficulty is None:
                return jsonify({"error": "Prediction failed"}), 500

            # Fetch questions based on predicted difficulty, excluding previous ones
            questions = Question.query.filter(
                Question.difficulty == predicted_difficulty,
                Question.id.notin_(previous_questions)
            ).all()

            if questions:
                # Randomly select a question from remaining questions
                selected_question = random.choice(questions)
                return jsonify({
                    "question_text": selected_question.question_text,
                    "options": [
                        selected_question.option1,
                        selected_question.option2,
                        selected_question.option3,
                        selected_question.option4,
                    ],
                    "correct_answer": selected_question.correct_answer,  # Send the correct answer
                    "question_id": selected_question.id,
                    "predicted_difficulty": predicted_difficulty,  # Return predicted difficulty
                })
            else:
                # Fallback to "medium" difficulty if no questions are found for predicted difficulty
                fallback_questions = Question.query.filter(
                    Question.difficulty == "medium",
                    Question.id.notin_(previous_questions)
                ).all()

                if fallback_questions:
                    # Randomly select a question from remaining "medium" difficulty questions
                    selected_question = random.choice(fallback_questions)
                    return jsonify({
                        "question_text": selected_question.question_text,
                        "options": [
                            selected_question.option1,
                            selected_question.option2,
                            selected_question.option3,
                            selected_question.option4,
                        ],
                        "correct_answer": selected_question.correct_answer,
                        "question_id": selected_question.id,
                        "predicted_difficulty": "medium",  # Return fallback difficulty
                    })
                else:
                    # Fallback to "easy" if no medium questions are found
                    easy_questions = Question.query.filter(
                        Question.difficulty == "easy",
                        Question.id.notin_(previous_questions)
                    ).all()

                    if easy_questions:
                        selected_question = random.choice(easy_questions)
                        return jsonify({
                            "question_text": selected_question.question_text,
                            "options": [
                                selected_question.option1,
                                selected_question.option2,
                                selected_question.option3,
                                selected_question.option4,
                            ],
                            "correct_answer": selected_question.correct_answer,
                            "question_id": selected_question.id,
                            "predicted_difficulty": "easy",  # Return fallback difficulty
                        })
                    else:
                        return jsonify({"error": "No question found for any difficulty level"}), 404
        else:
            return jsonify({"error": "Error fetching next difficulty"}), 500
    except Exception as e:
        print("Error during ML API request:", str(e))
        return jsonify({"error": "Error during ML API request"}), 500


# Handle user answer submission
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    selected_answer = data.get('selected_answer')
    correct_answer = data.get('correct_answer')
    user_id = data.get('user_id')
    is_correct = data.get('is_correct')

    user = UserPerformance.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update user performance based on whether the answer is correct
    if is_correct:
        user.score += 10
        user.correct_answers += 1
        user.streak += 1
    else:
        user.incorrect_answers += 1
        user.streak = 0

    # Commit the updated stats to the database
    db.session.commit()

    # Return the updated performance data to the client
    return jsonify({
        "message": "Answer recorded",
        "score": user.score,
        "correct_answers": user.correct_answers,
        "incorrect_answers": user.incorrect_answers,
        "streak": user.streak
    })


@app.route('/end_quiz', methods=['POST'])
def end_quiz():
    data = request.json
    user_id = data.get('user_id')

    with app.app_context():
        session = Session(db.engine)
        user = session.get(UserPerformance, user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = [{
        "username": user.username,
        "score": user.score,
        "correct_answers": user.correct_answers,
        "incorrect_answers": user.incorrect_answers,
        "streak": user.streak
    }]

    average_score = db.session.query(func.avg(UserPerformance.score)).scalar()
    average_correct_answers = db.session.query(func.avg(UserPerformance.correct_answers)).scalar()
    average_incorrect_answers = db.session.query(func.avg(UserPerformance.incorrect_answers)).scalar()
    average_streak = db.session.query(func.avg(UserPerformance.streak)).scalar()

    averages = {
        "average_score": average_score if average_score is not None else 0,
        "average_correct_answers": average_correct_answers if average_correct_answers is not None else 0,
        "average_incorrect_answers": average_incorrect_answers if average_incorrect_answers is not None else 0,
        "average_streak": average_streak if average_streak is not None else 0
    }

    averages = convert_decimal_to_float(averages)

    # Send to ML API
    sum_api_url = 'https://quizz-ml.onrender.com/sum'
    response = requests.post(sum_api_url, json={"user_data": user_data, "averages": averages})

    if response.status_code == 200:
        result = response.json()
        feedback = result.get('feedback', [])
        analysis = result.get('analysis', [])
        graph = result.get('graph', '')  # Capture the graph image base64 string

        return jsonify({
            "feedback": feedback,
            "analysis": analysis,
            "score": user.score,
            "graph": graph  # Add the graph to the response
        })
    else:
        return jsonify({"error": "Error from /sum API"}), 500




if __name__ == '__main__':
    app.run(debug=True)
