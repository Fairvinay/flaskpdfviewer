from flask import Flask, render_template, request, send_from_directory, redirect, url_for ,  send_file
from flask_cors import CORS, cross_origin

import glob
import os
import sys
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF for PDF processing
import tempfile

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    return render_template("index.html", pdf_files=pdf_files)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return redirect(url_for("upload_success_pdf"))
    return "Invalid file type", 400

@app.route("/uploaded")
def upload_success_pdf():
	list_of_files = glob.glob(app.config["UPLOAD_FOLDER"]+"/*")
	# * means all if need specific format then *.csv
	latest_file = max(list_of_files, key=os.path.getctime)
	print(latest_file)
	unlok_pdfName =  latest_file.rsplit('\\',1)[1]
	return render_template("uploadsuccess.html", filename=unlok_pdfName)
	#class ctx: pass 
    #ctx.filename = latest_file.name
    #setattr(ctx, 'size', ' ')
    #context = { "name": "", "age": "" }
    

@app.route("/view/<filename>")
def view_pdf(filename):
    return render_template("viewer.html", filename=filename)

@app.route("/pdf/<filename>")
def serve_pdf(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    

@app.route('/remove_password', methods=['POST'])
@cross_origin(origin='*')
def unlock_pdf():
    password =  request.get_json().get('password')  #request.form.get('password')
    uploaded_file = request.get_json().get('filename') #  request.form.get('filename') # request.files['pdfFile']

    if not password or not uploaded_file:
        return "Missing password or PDF file", 400

    try:
        # Create a temporary file to store the unlocked PDF
        temp_output = tempfile.NamedTemporaryFile(delete=False)
        filepath_unloked = os.path.join(app.config["UPLOAD_FOLDER"], "_unlocked_"+uploaded_file)
        pdfFileObj_unloked = open(filepath_unloked ,'w')   
	    
        # Create a PDF reader and writer
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], uploaded_file)
        pdfFileObj = open(filepath ,'rb')        
        pdf_reader = PdfReader(pdfFileObj)      #PdfReader(uploaded_file)
        pdf_writer = PdfWriter()
        pdf_writer_unloked = PdfWriter()

        # Decrypt the PDF using the provided password
        if pdf_reader.decrypt(password):
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])
                pdf_writer_unloked.add_page(pdf_reader.pages[page_num])

            # Write the unlocked PDF to the temporary file
            pdf_writer.write(temp_output)
            with  open(filepath_unloked , "wb") as output_stream:
               pdf_writer_unloked.write(output_stream)

            # Close the temporary file
            temp_output.close()
            unlok_pdfName =  filepath_unloked.rsplit('\\',1)[1]
            print('unlok_pdfName '+unlok_pdfName, file=sys.stderr)
            # Send the unlocked PDF file as an attachment
            # return send_file(temp_output.name, as_attachment=True)
            return  unlok_pdfName

        return "Incorrect password", 400

    except Exception as e:
        return "An error occurred while processing the PDF: " + str(e), 500

if __name__ == "__main__":
    app.run(debug=True)
