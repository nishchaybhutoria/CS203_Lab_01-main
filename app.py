import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

course_add_logger = logging.getLogger('AddCourseLogger')

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
required_fields = ["code", "name", "instructor", "semester", "schedule", "classroom", "prerequisites", "grading"]

# Instrument Flask with OpenTelemetry
FlaskInstrumentor().instrument_app(app)

# Configure OpenTelemetry
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({"service.name": "catalog-app"}) # create service name for this app
    )
)
jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

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
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("render_catalog") as span:
        span.set_attribute("request_method", request.method)
        span.set_attribute("user_ip", request.remote_addr)
        courses = load_courses()
        span.set_attribute("course_count", len(courses))
        return render_template('course_catalog.html', courses=courses)


@app.route('/course/<code>')
def course_details(code):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("view_course") as span:
        span.set_attribute("request_method", request.method)
        span.set_attribute("user_ip", request.remote_addr)
        span.set_attribute("course_code", code)
        courses = load_courses()
        course = next((course for course in courses if course['code'] == code), None)

        if not course:
            span.set_attribute("error", True)
            span.set_attribute("error_message", f"Course with code {code} not found.")
            flash(f"No course found with code '{code}'.", "error")
            return redirect(url_for('course_catalog'))

        return render_template('course_details.html', course=course)


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    form = AddCourseForm()
    # print(form.data)
    tracer = trace.get_tracer(__name__)
    # trigger form submission for POST request only
    if request.method == 'GET':
        with tracer.start_as_current_span("view_add_course_form") as span:
            span.set_attribute("request_method", request.method)
            span.set_attribute("user_ip", request.remote_addr)
        return render_template('add_course.html', form=form)

    with tracer.start_as_current_span("submit_add_course_form") as span:
        span.set_attribute("request_method", request.method)
        span.set_attribute("user_ip", request.remote_addr)

        new_course = form.data.copy()
        new_course.pop('csrf_token')

        # validate if all required fields are present
        if form.validate_on_submit():

            try:
                with open("course_catalog.json", "r") as json_file:
                    file_data = json.loads(json_file.read())
            except Exception as e:
                return redirect('/catalog')

            file_data.append(new_course)
            span.set_attribute("course_code", new_course.get("code"))
            span.set_attribute("course_name", new_course.get("name"))

            course_add_logger.info(f'Course {new_course['code']} added successfully. All required fields are present.')

            try:
                with open("course_catalog.json", "w") as json_file:
                    json_file.write(json.dumps(file_data, indent=4))
                span.set_status(trace.Status(trace.StatusCode.OK, description="JSON file updated successfully."))
            except Exception as e:
                course_add_logger.error(f'Error {e} when updating the JSON file.')
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, description="Error updating JSON file."))

            return redirect('/catalog')
        
        # log an error with the missing fields if the form is invalid and pre-fill the form with the old data
        else:
            print(new_course)
            missing = [field for field in required_fields if not new_course.get(field)]
            course_add_logger.error(
                f"Failed to add course. Missing fields: {', '.join(missing)}"
            )

            with tracer.start_as_current_span("add_course_form_validation_error",
                context=trace.set_span_in_context(span)) as child_span:
                child_span.set_status(Status(StatusCode.ERROR, description="Validation error: Missing required fields"))
                child_span.set_attribute("missing_fields", ", ".join(missing))

            return render_template('add_course.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
