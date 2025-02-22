from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import requests
import PyPDF2
import io
from dotenv import load_dotenv
import os
from fpdf import FPDF

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")  # Replace with your Gemini API key
gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

# Ensure the instance path directory exists
instance_dir = os.path.join(app.instance_path, "downloads")
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)


# Function to generate quiz using Gemini API
def generate_quiz(prompt, num_questions):
    headers = {"Content-Type": "application/json"}
    prompt_text = f"""
    Generate {num_questions} multiple-choice questions based on the following content:
    {prompt}
    Show the title of the topic and a statement that Quiz are generated on topic.
    Each question should have four options labeled a), b), c), and d). Only one option should be correct.

    Format each question as follows:

    Question X: <Question Text>
                a) <Option A>
                b) <Option B>
                c) <Option C>
                d) <Option D>
                Answer:<correct option Letter>
    """
    data = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(gemini_url, headers=headers, json=data, params={"key": api_key}, timeout=60)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            return result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', "").strip()
        return "Error: No content returned from Gemini API."
    except requests.exceptions.RequestException as e:
        return f"Error during API request: {str(e)}"


# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        return "".join([page.extract_text() for page in pdf_reader.pages])
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


# Function to generate a PDF
def generate_pdf(quiz_text):
    pdf_path = os.path.join("instance", "quiz.pdf")  # Path for saving the PDF file
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)  # Ensure content fits within the page
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Effective page width
    page_width = pdf.w - 2 * pdf.l_margin
    line_height = 10  # Space between lines
    indent_width = 10  # Indent for options

    # Process each line of input
    lines = quiz_text.split("\n")

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("**Question"):  # For Questions
            pdf.set_font("Arial", style="B", size=12)  # Bold for questions
            pdf.multi_cell(page_width, line_height, stripped_line.replace("", ""), align='L')

        elif stripped_line.startswith(("a)", "b)", "c)", "d)")):  # For Options
            pdf.set_font("Arial", size=12)  # Regular font for options
            pdf.multi_cell(page_width - indent_width, line_height, stripped_line, align='L')

        elif stripped_line == "":  # Blank lines for spacing
            pdf.ln(line_height // 2)  # Add a small gap

        else:  # For general text like topic or description
            pdf.set_font("Arial", size=9)
            pdf.multi_cell(page_width, line_height, stripped_line, align='L')

    # Save the PDF
    pdf.output(pdf_path)
    return pdf_path


# Routes
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")  # Load the new homepage


@app.route("/quiz", methods=["GET"])
def index():
    return render_template("index1.html")  # Redirect to the quiz page

@app.route("/result", methods=["GET"])
def result():
    # Render the result page
    return render_template("result.html")


@app.route("/help", methods=["GET"])
def help_page():
    # Render the help page
    return render_template("help.html")


@app.route("/generate", methods=["POST"])
def generate_quiz_route():
    topic = request.form.get("topic", "").strip()
    note = request.form.get("note", "").strip()
    file = request.files.get("file")
    num_questions = request.form.get("num_questions", 5)

    try:
        num_questions = int(num_questions)
    except ValueError:
        num_questions = 5

    if topic:
        input_text = f"Generate questions on the topic: {topic}"
    elif note:
        input_text = note
    elif file and file.filename:
        input_text = extract_text_from_pdf(file)
    else:
        return jsonify({"error": "Provide text, topic, or upload a PDF."})

    generated_quiz = generate_quiz(input_text, num_questions)
    if generated_quiz.startswith("Error:"):
        return jsonify({"error": generated_quiz})

    return jsonify({"quiz": generated_quiz})


@app.route("/download", methods=["GET"])
def download_quiz():
    pdf_path = request.args.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, attachment_filename="quiz.pdf")
    return jsonify({"error": "File not found."}), 404


if __name__ == "__main__":
    app.run(debug=True)
