# **CS203: Software Tools & Techniques for AI**
## **Lab 01: Distributed Tracing and Telemetry**
**IIT Gandhinagar, Sem II - 2024-25**

---

### **Objective**
In this assignment, we explore distributed tracing and telemetry in a pre-built Flask-based Course Information Portal. The aim is to implement OpenTelemetry instrumentation, analyze traces, and generate telemetry data for better observability.

---

### **Features Implemented**
1. **Add Courses to the Catalog**:
   - Added an **"Add a New Course"** button on the catalog page to navigate to a course addition form.
   - Successful form submissions:
     - Add the course to the catalog.
     - Log a message indicating successful course addition (`INFO` level).
   - Missing required fields:
     - Log an error (`ERROR` level).
     - Notify the user via the UI.
     - Retain the user input.

2. **OpenTelemetry Tracing**:
   - Instrumented the following routes with OpenTelemetry:
     - **`/catalog`**: Renders the course catalog.
     - **`/add_course`**: Handles course addition, including validation.
     - **`/course/<code>`**: Displays course details.
   - Created meaningful spans for key operations:
     - Example: `submit_add_course_form`, `add_course_form_validation_error`.
   - Added trace attributes for better observability (e.g., `user_ip`, `request_method`, `course_code`).

3. **Exporting Telemetry Data to Jaeger**:
   - Set up **Jaeger** as the tracing backend.
   - Exported telemetry data including:
     - Total requests to each route.
     - Processing time for each operation.
     - Error counts (e.g., validation errors).
   - Logs capture key events:
     - Course additions.
     - Errors during form submissions.
     - Successful rendering of pages.

---

### **Getting Started**
Follow the steps below to set up and run the application.

#### **1. Clone the Repository**
```bash
git clone https://github.com/nishchaybhutoria/CS203_Lab_01-main.git
cd CS203_Lab_01-main
```

#### **2. Install Dependencies**
Install Python dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

#### **3. Run Jaeger**
Start the Jaeger tracing backend using Docker:
```bash
sudo docker run -d --name jaeger \
    -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
    -p 5775:5775/udp \
    -p 6831:6831/udp \
    -p 6832:6832/udp \
    -p 5778:5778 \
    -p 16686:16686 \
    -p 14268:14268 \
    -p 14250:14250 \
    -p 9411:9411 \
    jaegertracing/all-in-one:1.41 --log-level=debug
```
- Jaeger UI will be available at [http://localhost:16686](http://localhost:16686).

#### **4. Run the Flask Application**
Start the Flask app:
```bash
flask run
```
- Access the application at [http://localhost:5000](http://localhost:5000).
