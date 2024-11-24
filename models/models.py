from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(100))
    option2 = db.Column(db.String(100))
    option3 = db.Column(db.String(100))
    option4 = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    category = db.Column(db.String(50))
    correct_answer = db.Column(db.String(100))


    def __init__(self, question_text, option1, option2, option3, option4, correct_answer, category, difficulty):
        self.question_text = question_text
        self.option1 = option1
        self.option2 = option2
        self.option3 = option3
        self.option4 = option4
        self.correct_answer = correct_answer
        self.category = category
        self.difficulty = difficulty
