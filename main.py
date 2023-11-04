from flask import Flask,render_template,request,session,redirect,flash
import pymysql
import hashlib
import PyPDF2
import openai


app = Flask(__name__)
app.secret_key = 'data_transmition'
app.jinja_env.globals.update(len=len)

def sql_connector():
    conn=pymysql.connect(host='localhost',user="root",password='',database='qna_generator')
    cur=conn.cursor()
    return conn,cur

@app.route('/upload', methods=['POST','GET'])
def upload():
    return render_template("upload.html")

@app.route('/home')
def home():
    return render_template('home.html')

def extract_pdf_data(file):
    reader = PyPDF2.PdfReader(file)
    # Get the number of pages in the PDF
    num_pages = len(reader.pages)
    
    # Initialize an empty string to store the extracted text
    text = ""
    # Loop through all pages and extract the text
    for page in range(num_pages):
        page_obj = reader.pages[page]
        text += page_obj.extract_text()
    # Return the extracted text
    return text

@app.route('/logout',methods=['GET','POST'])
def logout():
    return render_template('home.html')

@app.route("/Registration",methods=['GET','POST'])
def register():
    payment_status=request.args.get('payment')
    print(payment_status)
    if payment_status=='1':
        return render_template('Registration.html',payment_status=payment_status)
    if request.method=='POST':
        payment_status=request.form.get('payment_status')
        if payment_status=='1':
            name=request.form.get('u_name')
            email=request.form.get('u_email')
            contact=request.form.get('u_contact')
            password=request.form.get('u_pass')
            enc_pass=hashlib.md5(password.encode()).hexdigest()
            conn,c=sql_connector()
            c.execute("select contact,payment_status from user")
            out=c.fetchall()
            for i in out:
                if i[0]==contact and i[1] == '0':
                    flash('Contact already user.Try different Contact number.', 'error')
                    return redirect('/Registration')
                elif i[0]==contact and i[1] == '1':
                    flash('Contact already user.Try different Contact number.', 'error')
                    return redirect('/Registration?payment=1')
                else:
                    if name!='' or email!='' or contact!='' or password!='':
                        conn,c=sql_connector()
                        c.execute("INSERT INTO user(name,email,contact,password,payment_status) VALUES('{}','{}',{},'{}',{})".format(name,email,int(contact),enc_pass,int(1)))
                        conn.commit()
                        conn.close()
                        flash("Registered Successfull.", "success")
                        return redirect('/login')
                    else: 
                        flash("Please fill the required fields", "error")
        else:
            flash("Please Make Payment first",'error')
    else:
        return render_template('Registration.html')
    return render_template('Registration.html')

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        uname=request.form.get('u_name')
        upass=request.form.get('u_pass')
        enc_pass=hashlib.md5(upass.encode()).hexdigest()
        conn,c=sql_connector()
        c.execute("select contact,password,payment_status from user")
        out=c.fetchall()
        for i in out:
            if i[0]==uname and i[1]==enc_pass and i[2]==1:
                session['user']=uname
                session['check']=1
                return redirect('/home')
            else:
                flash('Wrong Username or Password', 'error')
    return render_template("login.html")

@app.route("/question",methods=['GET','POST'])
def question():
    return render_template("MCQ.html")


openai.api_key = "open-ai_api key"
def generate_questions_and_answers(paragraph):
    model_engine = "text-davinci-002"  # choose a language model to use

    # Generate questions using GPT-3
    questions_prompt = f"Generate questions based on the following paragraph:\n\n{paragraph}\n\nQuestions:"
    questions = openai.Completion.create(
        engine=model_engine,
        prompt=questions_prompt,
        max_tokens=1024,
        n=3,
        stop=None,
        temperature=0.5,
    )
    unique_questions = set([q.text.strip() for q in questions.choices])
    # Generate answers to the questions using GPT-3
    answers = []
    for question in unique_questions:
        answer_prompt = f"Answer the following question based on the paragraph and just write the answer not question again:\n\nQuestion: {question}\n\nAnswer:"
        answer = openai.Completion.create(
            engine=model_engine,
            prompt=answer_prompt,
            max_tokens=1024,
            n=3,
            stop=None,
            temperature=0.5,
        )
        answers.append(answer.choices[0].text.strip())

    return {"questions": list(unique_questions), "answers": answers}
@app.route("/theory_text", methods=["POST",'GET'])
def generate_questions():
    return render_template('theory_text.html')

@app.route("/theory_PDF", methods=["POST",'GET'])
def theory_PDF():
    return render_template('theory_PDF.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)