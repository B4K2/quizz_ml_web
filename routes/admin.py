from flask import Blueprint, request, render_template, redirect, url_for
from models import db, Question

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Manage Questions
@admin_bp.route('/questions', methods=['GET'])
def manage_questions():
    questions = Question.query.all()
    return render_template('admin/manage_questions.html', questions=questions)

# Add Question
@admin_bp.route('/questions/add', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        difficulty = request.form['difficulty']
        category = request.form['category']
        correct_answer = request.form['correct_answer']


        new_question = Question(
            question_text=question_text,
            option1=option_1,
            option2=option_2,
            option3=option_3,
            option4=option_4,
            difficulty=difficulty,
            category=category,
            correct_answer=correct_answer
        )

        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('admin.manage_questions'))
    
    return render_template('admin/add_question.html')

@admin_bp.route('/questions/edit/<int:id>', methods=['GET', 'POST'])
def edit_question(id):
    question = Question.query.get_or_404(id)

    if request.method == 'POST':
        question.question_text = request.form['question_text']
        question.option1 = request.form['option_1']
        question.option2 = request.form['option_2']
        question.option3 = request.form['option_3']
        question.option4 = request.form['option_4']
        question.correct_answer = request.form['correct_answer']
        question.difficulty = request.form['difficulty']
        question.category = request.form['category']

        db.session.commit()
        return redirect(url_for('admin.manage_questions'))

    return render_template('admin/edit_question.html', question=question)


# Delete Question
@admin_bp.route('/questions/delete/<int:id>', methods=['GET'])
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('admin.manage_questions'))
