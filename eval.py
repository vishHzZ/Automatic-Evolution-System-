import streamlit as st
import mysql.connector
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fpdf import FPDF
import re
import fitz  # PyMuPDF for reading PDFs
import re
from rapidfuzz import fuzz
import os
import io
import PyPDF2
from PyPDF2 import PdfReader

# Database configuration
host = "82.180.143.66"
user = "u263681140_students"
passwd = "testStudents@123"
db_name = "u263681140_students"
# Function to check admin credentials
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=passwd,
    database=db_name,
    #pool_name=None  # Disabling connection pooling
)
# Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host= "82.180.143.66",
        user="u263681140_students",
        password="testStudents@123",
        database="u263681140_students"
    )

# Function to fetch data from a table
def fetch_data(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data
    except Exception as e:
        st.error(f"Database error: {e}")
        return []
def check_admin_login(email, password):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=passwd,
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM admin WHERE mail = %s AND password = %s",
            (email, password)
        )
        return cursor.fetchone() is not None
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
def adminLogin():
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    if st.session_state["page"] == "login":
        with st.form("admin_form"):
            st.subheader("🧑💼 Administrator Login")
            email = st.text_input("Admin Email")
            password = st.text_input("Admin Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if check_admin_login(email, password):
                    st.session_state.update({"page": "admin_dash", "role": "admin"})
                    st.success("Admin login successful!")
                    st.rerun()
                else:
                    st.error("Invalid admin credentials")

    elif st.session_state["page"] == "admin_dash":
        st.title("Administrator Dashboard")

        # Horizontal radio buttons
        selected_option = st.radio(
            "Select Data to View:",
            ["Students", "Teachers","UpdateProfile", "Check Marks"],
            horizontal=True,
            key="admin_view"
        )

        if selected_option == "Students":
            st.subheader("📚 Student Records")
            student_data = fetch_data("students")
            if student_data:
                df = pd.DataFrame(student_data)
                st.dataframe(df)
            else:
                st.warning("No student data found in the database.")

        elif selected_option == "Teachers":
            st.subheader("👩🏫 Teacher Records")
            teacher_data = fetch_data("teacher")
            if teacher_data:
                df = pd.DataFrame(teacher_data)
                st.dataframe(df)
            else:
                st.warning("No teacher data found in the database.")

        # Add logout button at bottom
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.session_state["page"] = "login"
            st.rerun()

def RegisterUser():
    branches = [
        "Computer Science", 
        "Mechanical Engineering", 
        "Electrical Engineering", 
        "Civil Engineering", 
        "Electronics and Communication", 
        "Information Technology",
        "Chemical Engineering", 
        "Aerospace Engineering"
    ]
    st.title("Registration Form")

    registration_type = st.selectbox("Select Registration Type", ["Teacher", "Student"])

    with st.form("registration_form"):
        if registration_type == "Teacher":
            name = st.text_input("Name")
            mail = st.text_input("Email")
            mobile = st.text_input("Mobile Number")
            password = st.text_input("Password", type="password")
            branch = st.selectbox("Branch", branches)  
            submitted = st.form_submit_button("Register")

            if submitted:
                if name and mail and mobile and password and branch:
                    if not is_valid_email(mail):
                        st.warning("Please enter a valid email address!")
                    elif not is_valid_mobile(mobile):
                        st.warning("Mobile number must be 10 digits!")
                    else:
                        insert_teacher(name, mail, mobile, password, branch)
                        st.session_state.registered_email = mail
                        st.session_state.registered_password = password
                        st.session_state.page = "login"  # Redirect to login page
                        st.rerun()                        
        elif registration_type == "Student":
            name = st.text_input("Name")
            enrolment = st.text_input("Enrolment Number")
            mail = st.text_input("Email")
            mobile = st.text_input("Mobile Number")
            password = st.text_input("Password", type="password")
            branch = st.selectbox("Branch", branches) 
            submitted = st.form_submit_button("Register")

            if submitted:
                if name and enrolment and mail and mobile and password and branch:
                    if not is_valid_email(mail):
                        st.warning("Please enter a valid email address!")
                    elif not is_valid_mobile(mobile):
                        st.warning("Mobile number must be 10 digits!")
                    else:
                        insert_student(name, enrolment, mail, mobile, password, branch)
                        st.session_state.registered_email = mail
                        st.session_state.registered_password = password
                        st.session_state.page = "login"  # Redirect to login page
                        st.rerun()                                            

                else:
                    st.warning("Please fill all the fields!")

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.(com|in|org|edu|ac\.in)$'
    return re.match(pattern, email) is not None

def is_valid_mobile(mobile):
    pattern = r'^\d{10}$'
    return re.match(pattern, mobile) is not None
def teacher_email_exists(mail):
    db, cur = None, None
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM teacher WHERE mail = %s", (mail,))
        return cur.fetchone() is not None
    finally:
        if cur:
            cur.close()
        if db:
            db.close()

def student_exists(mail, enrolment):
    db, cur = None, None
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM students WHERE email = %s OR enrolment = %s", (mail, enrolment))
        return cur.fetchone() is not None
    finally:
        if cur:
            cur.close()
        if db:
            db.close()
def insert_teacher(name, mail, mobile, password, branch):
    db, cur = None, None
    try:
        if teacher_email_exists(mail):
            st.warning("Email already exists for another teacher!")
            return

        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()

        insert_query = '''INSERT INTO teacher (name, mail, mobile, password, branch) 
                          VALUES (%s, %s, %s, %s, %s);'''
        cur.execute(insert_query, (name, mail, mobile, password, branch))
        db.commit()
        st.success("Teacher registered successfully!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        if cur:
            cur.close()
        if db:
            db.close()

def insert_student(name, enrolment, mail, mobile, password, branch):
    db, cur = None, None
    try:
        if student_exists(mail, enrolment):
            st.warning("Email or enrolment number already exists for another student!")
            return

        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()

        insert_query = '''INSERT INTO students (name, enrolment, email, mobile, password, branch) 
                          VALUES (%s, %s, %s, %s, %s, %s);'''
        cur.execute(insert_query, (name, enrolment, mail, mobile, password, branch))
        db.commit()
        st.success("Student registered successfully!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        if cur:
            cur.close()
        if db:
            db.close()
# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Function to extract roll number
def extract_roll_number(text):
    match = re.search(r'Roll Number:\s*(\d+)', text)
    return match.group(1) if match else "Unknown"

# Function to extract questions and answers
def extract_questions_answers(pdf_text):
    lines = pdf_text.split("\n")
    questions, answers = [], []
    current_question, current_answer = None, ""

    for line in lines:
        line = line.strip()
        if line.startswith("Q "):
            if current_question:
                questions.append(current_question)
                answers.append(current_answer.strip())
            current_question = line
            current_answer = ""
        elif current_question:
            current_answer += " " + line

    if current_question:
        questions.append(current_question)
        answers.append(current_answer.strip())
    return questions, answers

# Function to extract question number
def extract_question_number(question):
    match = re.search(r'Q\s?\d+', question)
    if match:
        q_number = match.group(0).replace(" ", "")
        question_text = re.sub(r'Q\s?\d+', '', question).strip()
        return q_number, question_text
    return None, question

# Function to clean answers
def clean_answer_column(answer):
    return str(answer).replace('Answer: ', '').strip() if answer else ""

# Function to calculate similarity
def calculate_similarity(answer1, answer2):
    return fuzz.ratio(str(answer1), str(answer2)) if answer1 and answer2 else 0

# Function to assign marks
def assign_marks(similarity, total_marks):
    if similarity >= 90:
        return total_marks
    elif similarity >= 70:
        return total_marks * 0.75
    elif similarity >= 50:
        return total_marks * 0.50
    else:
        return 0

# Function to process a single student's PDF and evaluate answers
def process_student_pdf(correct_answers_file, student_pdf):
    try:
        # Load correct answers
        correct_answers = pd.read_excel(correct_answers_file)
        
        # Process student answers
        pdf_text = extract_text_from_pdf(student_pdf)
        questions, answers = extract_questions_answers(pdf_text)
        roll_number = extract_roll_number(pdf_text)
        
        student_answers = pd.DataFrame({'Question': questions, 'Answers': answers})
        student_answers[['No', 'Question']] = student_answers['Question'].apply(lambda x: pd.Series(extract_question_number(x)))
        student_answers['Answers'] = student_answers['Answers'].apply(clean_answer_column)

        # Ensure 'No' column exists in correct answers
        if 'No' not in correct_answers.columns:
            st.error("❌ The uploaded correct answers file is missing a 'No' column.")
            return None
        else:
            # Merge and compute similarity
            df_merged = pd.merge(student_answers, correct_answers, on='No', suffixes=('_student', '_correct'), how="inner")

            # Handle missing columns gracefully
            if "Answers_student" not in df_merged.columns:
                df_merged.rename(columns={"Answers": "Answers_student"}, inplace=True)

            df_merged['Similarity (%)'] = df_merged.apply(
                lambda row: calculate_similarity(row.get('Answers_student', ''), row.get('Answers_correct', '')),
                axis=1
            )
            df_merged['Assigned Marks'] = df_merged.apply(
                lambda row: assign_marks(row['Similarity (%)'], row['Marks']),
                axis=1
            )

            # Compute total marks
            total_marks_obtained = df_merged['Assigned Marks'].sum()
            total_possible_marks = correct_answers['Marks'].sum()

            return roll_number, df_merged, total_marks_obtained, total_possible_marks

    except Exception as e:
        st.error(f"🚨 Error processing files: {e}")
        return None

def insert_student_result(roll_number, subject, marks):
    
    cursor = None  # Initialize cursor to None
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host="82.180.143.66",
            user="u263681140_students",
            password="testStudents@123",
            database="u263681140_students"
        )
        
        # Create a cursor object
        cursor = connection.cursor()
        #subject = "Cloud Computing"
        # SQL query to insert data
        query = """
        INSERT INTO StudentResult (RollNumber, Subject, Marks) 
        VALUES (%s, %s, %s)
        """
        marks = int(marks)
        # Prepare the data to be inserted
        data = (roll_number, subject, marks)

        # Execute the query
        cursor.execute(query, data)

        # Commit the transaction
        connection.commit()

    except mysql.connector.Error as err:
        st.write(f"Error: {err}")
    finally:
        # Close the cursor and connection only if cursor was created
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def extract_subject_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            for line in text.split("\n"):
                if line.strip().startswith("Subject:"):
                    return line.split(":")[1].strip()
    return None


def main1():
    # File upload inputs
    correct_answers_file = st.file_uploader("Upload Correct Answers File", type="xlsx")
    student_pdfs = st.file_uploader("Upload Student PDF Files", type="pdf", accept_multiple_files=True)

    if correct_answers_file and student_pdfs:
        all_results = []

        # Process each student PDF
        for student_pdf in student_pdfs:
            result = process_student_pdf(correct_answers_file, student_pdf)
            if result:
                roll_number, df_merged, total_marks_obtained, total_possible_marks = result
                all_results.append({
                    "Roll Number": roll_number,
                    "Total Marks Obtained": total_marks_obtained,
                    "Total Possible Marks": total_possible_marks,
                    "Details": df_merged
                })
                sub = extract_subject_from_pdf(student_pdf)
                st.write("Subject is: ", sub)
                insert_student_result(roll_number,sub, total_marks_obtained)
                

        # Display results for all students
        for result in all_results:
            st.subheader(f"📌 Roll Number: {result['Roll Number']}")
            st.write(f"### ✅ Total Marks: {result['Total Marks Obtained']:.2f} / {result['Total Possible Marks']:.2f}")
            st.dataframe(result["Details"])

            # Save and download individual results
            output_file = f"{result['Roll Number']}_graded_answers.csv"
            result["Details"].to_csv(output_file, index=False)
            st.download_button(f"⬇️ Download Results for {result['Roll Number']}", data=open(output_file, "rb"), file_name=output_file, mime="text/csv")


def check_teacher_login(email, password):
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM teacher WHERE mail = %s AND password = %s", (email, password))
        return cur.fetchone() is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        if 'db' in locals(): db.close()
def check_student_login(email, password):
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM students WHERE email = %s AND password = %s", (email, password))
        return cur.fetchone() is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        if 'db' in locals(): db.close()
def check_admin_login(email, password):
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM admin WHERE mail = %s AND password = %s", (email, password))
        return cur.fetchone() is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        if 'db' in locals(): db.close()

# -------------------- DASHBOARDS --------------------
def teacher_dashboard():
    main1()    
    if st.button("🔴 Logout"):
        st.session_state.update({"page": "login", "logged_in": False})
        st.rerun()
    

def fetch_student_info(email):

    """Fetch student information from database using email"""
    conn = None
    cursor = None
    try:
        # Use existing database configuration
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=passwd,
            database=db_name
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT name, enrolment, email, mobile, branch FROM students WHERE email = %s", 
            (email,)
        )
        return cursor.fetchone()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
def read_student_results():
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host="82.180.143.66",
            user="u263681140_students",
            password="testStudents@123",
            database="u263681140_students"
        )
        
        # Create a cursor object
        cursor = connection.cursor()

        # SQL query to select all data from StudentResult table
        query = "SELECT * FROM StudentResult"

        # Execute the query
        cursor.execute(query)

        # Fetch all records from the table
        records = cursor.fetchall()

        # Fetch column names dynamically
        column_names = [i[0] for i in cursor.description]  # Get column names from DB

        # Debugging: print records and column names
        print(f"Fetched Records: {records}")
        print(f"Column Names from DB: {column_names}")

        # Check if records are empty
        if not records:
            st.warning("No records found in the database.")
            return pd.DataFrame(columns=column_names)  # Return an empty dataframe

        # Create a Pandas DataFrame using dynamic column names
        df = pd.DataFrame(records, columns=column_names)

        return df

    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return pd.DataFrame()

    except ValueError as ve:
        st.error(f"Data Processing Error: {ve}")
        return pd.DataFrame()

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def adminDashboard():
    #st.title("👑 Administrator Dashboard")

    # Horizontal radio buttons for navigation
    selected_option = st.radio(
        "Select Data to View:",
        ["Result Details", "Teacher Details", "Student Details", "Update Profile"],
        horizontal=True,
        key="admin_view"
    )

    if selected_option == "Result Details":
        st.subheader("📊 Result Records")
        result_data =0
        df_results = read_student_results()
        if df_results is not None:
            st.dataframe(df_results)
        else:
            st.write("No student results found in the database.")

    elif selected_option == "Teacher Details":
        st.subheader("👩🏫 Teacher Records")
        teacher_data = fetch_data("teacher")
        if teacher_data:
            df = pd.DataFrame(teacher_data)
            st.dataframe(df)
        else:
            st.warning("No teacher data found in the database.")

    elif selected_option == "Student Details":
        st.subheader("📚 Student Records")
        student_data = fetch_data("students")
        if student_data:
            df = pd.DataFrame(student_data)
            st.dataframe(df)
        else:
            st.warning("No student data found in the database.")
    elif selected_option == "Update Profile":
        st.subheader("👩🏫 Update Teaher/Student Profile")
        branches = [
        "Computer Science", 
        "Mechanical Engineering", 
        "Electrical Engineering", 
        "Civil Engineering", 
        "Electronics and Communication", 
        "Information Technology",
        "Chemical Engineering", 
        "Aerospace Engineering"
        ]

        user_type = st.radio("Select Profile Type to Update:", ["Student", "Teacher"])
        if user_type == "Teacher":
            email = st.text_input("Enter Email to Update Profile:")
            name = st.text_input("Name")
            mobile = st.text_input("Mobile Number")
            password = st.text_input("Password", type="password")
            branch = st.selectbox("Branch", branches)     
            #submitted = st.form_submit_button("Update Teacher")            
        elif user_type == "Student":
            email = st.text_input("Enter Email to Update Profile:")
            name = st.text_input("Name")
            mobile = st.text_input("Mobile Number")
            password = st.text_input("Password", type="password")
            branch = st.selectbox("Branch", branches) 
            #submitted = st.form_submit_button("Update Student")
        if st.button("Update Profile"):
            if email and mobile and name and password and branch:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if len(mobile) == 10:
                        if user_type == "Student":
                            update_query = "UPDATE students SET name = %s, mobile = %s, password = %s,branch = %s WHERE email = %s"
                        else:
                            update_query = "UPDATE teacher SET name = %s, mobile = %s, password = %s,branch = %s WHERE mail = %s"
        
                        cursor.execute(update_query, (name, mobile, password, branch, email))
                        
                        conn.commit()
        
                        if cursor.rowcount > 0:
                            st.success(f"{user_type} Profile Updated Successfully!")
                        else:
                            st.warning(f"No {user_type} found with this email.")
        
                        cursor.close()
                        conn.close()
                    else:
                        st.warning(f" invalid mobile number.")
                    
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please fill all fields before updating.")
    
             
def admin_dashboard():
    st.title("👑 Admin Dashboard")
    adminDashboard()
    if st.button("🔴 Logout"):
        st.session_state.update({"page": "login", "logged_in": False})
        st.rerun()

    #st.write("Admin functionality for answer evaluation")
def HomePage():
    st.image("background.jpg", use_container_width=True, caption="Automated Answer Evaluation System")
    background_image_url = "https://www.freepik.com/free-vector/abstract-blue-circle-black-background-technology_34386132.htm#fromView=keyword&page=1&position=12&uuid=dc1355a0-023d-44c3-987d-ba1e0a8270b6&new_detail=true&query=Dark+Website+Background"  # Update with your image URL
 
    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; font-size: 14px; color: white;">
            &copy; 2025 Automated Answer Evaluation System. All Rights Reserved.
        </div>
    """, unsafe_allow_html=True)
def fetch_marks_subject(rno):
    # Establish the connection to the database
    connection = get_db_connection()

    # Create a cursor object to interact with the database
    cursor = connection.cursor()

    # SQL query to select Marks and Subject where RollNumber = rno
    query = "SELECT Marks, Subject FROM StudentResult WHERE RollNumber = %s"

    # Execute the query with the given RollNumber
    cursor.execute(query, (rno,))

    # Fetch all rows from the result of the query
    results = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    if results:
        # Convert results to DataFrame with column names
        df = pd.DataFrame(results, columns=["Marks", "Subject"])
        st.table(df)
    else:
        st.info("Marks details will be displayed here once available.")

def login_page():
    st.title("📚 Automated Answer Evaluation System")
    tab1, tab2, tab3, tab4 = st.tabs(["Home","Login", "Signup", "Admin Login"])
    with tab1:
        HomePage()
    with tab2:
        col1, col2 = st.columns([2, 3])
        with col1:
            # Display the image
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.image("nlp2.jpg", use_container_width=True, caption="Automated Answer Evaluation System")
        
        with col2:
            st.header("User Login")
            login_type = st.selectbox("Select Role", ["Teacher", "Student"], key="login_role")
            prefilled_email = st.session_state.get("registered_email", "")
            prefilled_password = st.session_state.get("registered_password", "")
            with st.form("login_form"):
                global global_var
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                if submit:
                    if login_type == "Teacher":
                        if check_teacher_login(email, password):
                            st.session_state.update({"page": "teacher_dash", "role": "teacher"})
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    elif login_type == "Student":
                        if check_student_login(email, password):
                            st.session_state["email"] = email 
                            st.session_state.update({"page": "student_dash", "role": "student"})
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

                    else:
                        st.warning("Student login not implemented yet")

    with tab3:
        RegisterUser()

    with tab4:
        #st.header("Administrator Login")
        adminLogin()
# -------------------- APP FLOW CONTROL --------------------
if "page" not in st.session_state:
    st.session_state.update({
        "page": "login",
        "logged_in": False,
        "role": None
    })

if(__name__ == "__main__"):
    #login_page()
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "teacher_dash":
        teacher_dashboard()
    elif st.session_state.get("page") == "student_dash":
        st.header("Student Dashboard")
        email = st.session_state.get("email")
        #st.write("Well Come:", email)
        student_info = fetch_student_info(email)
        if student_info:
            selected_tab = st.radio("Select View", ["Profile", "Marks"], horizontal=True)
            
            if selected_tab == "Profile":
                # Convert student info to DataFrame and display in table format
                profile_df = pd.DataFrame([{
                    "Name": student_info['name'],
                    "Enrolment": student_info['enrolment'],
                    "Email": student_info['email'],
                    "Mobile": student_info['mobile'],
                    "Branch": student_info['branch']
                }])
                
                st.write("### Student Profile")
                st.dataframe(profile_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Name": "Student Name",
                                "Enrolment": "Enrollment Number"
                            })
                
            else:
                st.write("### Marks Information")
                fetch_marks_subject(student_info['enrolment'])
                #st.info("Marks details will be displayed here once available")
            if st.button("🔴 Logout"):
                st.session_state.update({"page": "login", "logged_in": False})
                st.rerun()

        else:
            st.error("Student information not found")
    elif st.session_state.page == "admin_dash":
        admin_dashboard()
