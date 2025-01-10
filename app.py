import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class AddCourseForm(FlaskForm):
    code = StringField('code', validators=[DataRequired()], default='')
    name = StringField('name', validators=[DataRequired()], default='')
    instructor = StringField('instructor', validators=[DataRequired()], default='')
    semester = StringField('semester', validators=[DataRequired()], default='')
    schedule = StringField('schedule', validators=[DataRequired()], default='')
    classroom = StringField('classroom', validators=[DataRequired()], default='')
    prerequisites = StringField('prerequisites', validators=[DataRequired()], default='')
    grading = StringField('grading', validators=[DataRequired()], default='')
    description = StringField('description', default='')


# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'secret'
COURSE_FILE = 'course_catalog.json'


# Utility Functions
def load_courses():
    """Load courses from the JSON file."""
    if not os.path.exists(COURSE_FILE):
        return []  # Return an empty list if the file doesn't exist
    with open(COURSE_FILE, 'r') as file:
        return json.load(file)


def save_courses(data):
    """Save new course data to the JSON file."""
    courses = load_courses()  # Load existing courses
    courses.append(data)  # Append the new course
    with open(COURSE_FILE, 'w') as file:
        json.dump(courses, file, indent=4)


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/catalog')
def course_catalog():
    courses = load_courses()
    return render_template('course_catalog.html', courses=courses)


@app.route('/course/<code>')
def course_details(code):
    courses = load_courses()
    course = next((course for course in courses if course['code'] == code), None)
    if not course:
        flash(f"No course found with code '{code}'.", "error")
        return redirect(url_for('course_catalog'))
    return render_template('course_details.html', course=course)


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    form = AddCourseForm()

    if form.validate_on_submit():
        print(form.data)
        new_course = form.data.copy()
        new_course.pop('csrf_token')

        with open("course_catalog.json", "r") as json_file:
            file_data = json.loads(json_file.read())

        file_data.append(new_course)
        print(file_data)

        with open("course_catalog.json", "w") as json_file:
            json_file.write(json.dumps(file_data, indent=4))

        return redirect('/success')

    return render_template('add_course.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
