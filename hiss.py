import openai
import os
import streamlit as st
from dotenv import load_dotenv
import datetime
import bcrypt
from deta import Deta
from st_audiorec import st_audiorec
import pdfkit
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from datetime import date

# Specify the correct path to the wkhtmltopdf executable
wkhtmltopdf_path = 'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'

# Load environment variables
load_dotenv()

# Set up OpenAI API key
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Set up Deta
DETA_KEY = os.getenv('DETA_KEY')
deta = Deta(DETA_KEY)
db = deta.Base('User-Database')

# Chat-based language model system messages
system_messages = f"""Act as an AI Legal Advisor. Do not mention you are not an actual lawyer. 
Give legal advises based on the constitution of India in the following steps.

1: Check whether the issue is an actual legal issue.
2: Give legal advise
3: Explain the steps for how to and where to register complaint as a list.
4: Cite the necessary articles and sections under law with brief explainations about each with context to the problem.


Provide response in the  following format
Legal advise :<step 2 reasoning>

Steps for registering complaint: <step 3 reasoning>

Citations <step 4 reasoning>

Following is an example for response suitable for a women seeking divorce from her abusive husband:

Legal advice: If you are seeking a divorce, it is an actual legal issue that can be resolved through the legal process. However, it is important to consult with a lawyer to understand the specific requirements and procedures in your jurisdiction.

Steps for registering complaint:

1. Consult with a family law attorney: Schedule a meeting with a family law attorney to discuss your situation, understand the legal process, and gather necessary information and documentation for filing a divorce petition.

2. Prepare the divorce petition: With the help of your attorney, prepare a divorce petition that includes details about the marriage, grounds for divorce, and requested relief (such as property division, child custody, or spousal support).

3. File the divorce petition: The completed divorce petition should be filed in the appropriate family court. Pay the required filing fee and submit the necessary documents as per the court's instructions.

4. Serve the divorce petition: Serve a copy of the divorce petition to your spouse, following the legal requirements for service in your jurisdiction. This could be done through a professional process server or as directed by the court.

5. Participation in court process: Attend all scheduled court hearings and proceedings related to your divorce case. Cooperate with your attorney and provide any additional information or documentation as required by the court.

6. Resolution or trial: Depending on the circumstances, your divorce case may be resolved through negotiation, mediation, or other alternative dispute resolution methods. If an agreement cannot be reached, a trial may be necessary to resolve the outstanding issues.

7. Finalize the divorce: Once the court has made its final decision on the issues, a divorce decree or judgment of dissolution will be issued. Follow the court's instructions to finalize the divorce and ensure compliance with any orders or agreements.


Citations:

Hindu Marriage Act, 1955: This act governs Hindu marriage and allows for divorce under specific grounds mentioned in Section 13.
Indian Divorce Act, 1869: This act applies to Christian marriages and outlines the provisions for divorce under specific circumstances as mentioned in Section 10.
Special Marriage Act, 1954: This act provides for marriages between people of different religions or those who choose a civil marriage. It also allows for divorce under certain conditions mentioned in Section 27. Note: The specific citations may vary based on the personal law applicable to your situation. It is essential to consult with a lawyer to determine the relevant laws and provisions for your specific case.



"""

# Function to hash the password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # Decode bytes to string

# Function to insert a new user
def insert_user(email, username, password):
    date_joined = str(datetime.datetime.now())
    hashed_password = hash_password(password)

    return db.put({'key': username, 'username': username, 'password': hashed_password, 'date_joined': date_joined,"responses":[]})

# Function to authenticate a user
def authenticate_user(username, password):
    user = db.get(username)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return user
    return None

# Function to sign up a new user
def sign_up():
    with st.form(key='signup', clear_on_submit=True):
        st.subheader(':green[Sign Up]')
        email = st.text_input(':blue[Email]', placeholder='Enter Your Email')
        username = st.text_input(':blue[Username]', placeholder='Enter Your Username')
        password1 = st.text_input(':blue[Password]', placeholder='Enter Your Password', type='password')
        password2 = st.text_input(':blue[Confirm Password]', placeholder='Confirm Your Password', type='password')

        if st.form_submit_button('Sign Up'):
            if password1 == password2:
                result = insert_user(email, username, password1)
                st.success(f"User {username} successfully created! Date joined: {result['date_joined']}")
            else:
                st.error("Passwords do not match. Please try again.")

# Function to log in a user
def login():
    with st.form(key='login', clear_on_submit=True):
        st.subheader(':green[Log In]')
        username = st.text_input(':blue[Username]', placeholder='Enter Your Username')
        password = st.text_input(':blue[Password]', placeholder='Enter Your Password', type='password')

        if st.form_submit_button('Log In'):
            user = authenticate_user(username, password)
            if user:
                # Set the state variable to indicate successful login
                st.session_state.is_authenticated = True
                st.success(f"Welcome back, {user['username']}! Last login: {datetime.datetime.now()}")
                return user
            else:
                st.error("Authentication failed. Please check your username and password.")

# Function to display the legal advice chatbot
def get_legal_advice(prompt):
    # Call OpenAI API for legal advice
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_messages},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

legal_draft_system_message = f"""You are a an AI Lawyer. You will be given a case. An explaination of the case with references to the article in Indian constitution.
You are supposed to generate a legal draft for the petition. Include new lines(\n) wherever required since the generated resposonse has to fit into a pdf.
Below is an example for legal draft for a petition related to Divorce Petition by Hindu Wife on the Grounds of Cruelty.

IN THE FAMILY COURT BANDRA, MUMBAI

M.J. PETITION NO. ___ of ____

Smt. ___________,

daughter of ___________,

aged _______ years, residing at ___________ Petitioner.

Versus

XYZ, son of _________,

_______ years of age,

residing at _________,

carrying on __________ business...... Respondent.

 

In the matter of dissolution of marriage under Section 13 of the Hindu Marriage Act, 1956:

And

In the matter of the Family Courts Act, 1954;

And

In the matter of Divorce of the Petitioner with the Respondent on grounds of cruelty.

TO,

THE HON''BLE PRINCIPAL JUDGE

AND OTHER JUDGES OF THIS

HON''BLE COURT.

THE HUMBLE PETITION OF

THE PETITIONER ABOVENAMED

MOST RESPECTFULLY SHEWETH:

1.      That the Petitioner and the Respondent were lawfully married according to traditional Hindu Vedic rites on the ______ day of __02 at the ______ in Mumbai. Hereto annexed and marked Exhibit 'A' is a copy of the marriage certificate evidencing the said marriage.

2.      The Petitioner and the Respondent are Hindu by birth and they continue to be so.

3.      After the said marriage, the Petitioner and the Respondent cohabited and lived together at the Petitioner's house for about six years. There were two issues out of this marriage viz. LML (son of ________ years of age) and HIJ (daughter of ___ years of age).

4.      The Petitioner states that from the month of ___ 02, the Respondent began to ill-treat the Petitioner, and from the month of _____02, began to physically assault the Petitioner without any cause whatsoever. For some time, the Petitioner made no complaint and underwent such ill-treatment, hoping that the Defendant would see better sense. However, on or about ____month of 02, the Respondent attacked the Petitioner with a stick and inflicted serious injuries leading to multiple fractures in hand and leg of the Petitioner. The Petitioner thereupon lodged a complaint at the ____ Police Station, being complaint No. ___. The Petitioner craves leave to refer to and rely upon a copy of the said complaint when produced.

5.      The Petitioner says that as a result of the aforesaid injury inflicted on the Petitioner by the Respondent, the Petitioner had to be hospitalized for six days. The Petitioner craves leave to refer to and rely upon the Medical Certificate issued by Dr. ____ who treated the Petitioner at ______ Hospital.

6.      The petitioner says that even thereafter, the Respondent continued to treat the Petitioner in a cruel and violent manner. The Petitioner says that such cruelty has cause an apprehension in the mind of the Petitioner that it will be harmful and injurious for the Petitioner to continue to live with the respondent.

7.      There is no collusion or connivance between the Petitioner and the Respondent in filing this Petition.

8.      The Petitioner is claiming alimony @ Rs. ---- per month from the Respondent.

9.      No other proceedings with respect to the marriage between the Petitioner and the Respondent have been filed in this Honorable Court or in any other Court in India.

10.   The Petitioner and the Respondent were married in Mumbai and last cohabited in Mumbai within the territorial limits of the jurisdiction to entertain, try and dispose of the present Petition.

11.   The Petitioner being a lady is exempt from payment of Court fees.

12.   The Petitioner will rely on documents, a list whereof is annexed hereto.

The Petitioner therefore prays:

·          That this Honorable Court be pleased to decree a dissolution of the said marriage between the Petitioner and the Respondent;

·          That the Petitioner be granted alimony @ Rs. _______/- per month;

·          That the Respondent be ordered and decreed to pay to the Petitioner the costs of this Petition; and

·          In the alternate to prayer (c) above, the Respondent be directed to give the Petitioner a sum of Rs. ________/- so as to enable her to purchase suitable accommodation for herself;

·          That pending the hearing and final disposal of this petition, the Respondent be directed to provide the Petitioner with a monthly allowance of Rs. ____/- to meet her personal expenses and the expenses of running the matrimonial home;

·          For such further and other reliefs as the nature and circumstances of the case may require.

Petition drawn by:

Mr. ABC,

Advocate, Sd/- Petitioner

High Court, Mumbai.

VERIFICATION

I, ___________, the Petitioner above named, do hereby solemnly declare and say that what is contained in paragraphs _________ to __________ is true to my knowledge and that what is state in paragraphs _______ to _______ is stated on legal advice and I believe the same to be true.

______ day of ____02. Sd/-

Before me,

Registrar/Superintendent,
"""
def get_legal_draft(query, response):
    # Call OpenAI API for legal advice
    prompt_message = f"""Case: {query}
    Explaination: {response}"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": legal_draft_system_message},
            {"role": "user", "content": prompt_message}
        ]
    )
    return completion.choices[0].message.content

# Function to display the dashboard
# Function to display the dashboard
def dashboard():
    st.title("Just AI Dashboard")
    st.header("Welcome to the Dashboard!")

    # Check if the user is authenticated
    if hasattr(st.session_state, 'is_authenticated') and st.session_state.is_authenticated:
        # Retrieve user information from Deta
        user = db.get(st.session_state.username)
        if user:
            st.subheader("Legal Advice History:")
            responses = user.get("responses", [])
            for entry in responses:
                st.write(f"Query: {entry['query']}")
                st.write(f"Response: {entry['response']}")
                st.write("----")

        # Add other dashboard content here
    else:
        st.warning("Please log in to access the dashboard.")


        # Add other dashboard content here
    else:
        st.warning("Please log in to access the dashboard.")
This modification assumes that the user's responses are stored in the Deta database under the "responses" key. It retrieves the responses and displays them in the dashboard. You can further enhance the formatting and presentation based on your preferences.

Remember to update the dashboard function in your Streamlit app to include this modification.







    # Add your dashboard content here

# Main part of the Streamlit app
if __name__ == "__main__":
    # Display the login or sign-up page based on the selected navigation
    selected_page = st.sidebar.radio("Navigation", ["Home", "Sign Up", "Log In", "Legal Advice", "Dashboard"])

    if selected_page == "Home":
        st.header("Welcome to the Home Page!")
        st.write("Navigate to 'Sign Up', 'Log In', 'Legal Advice', or 'Dashboard' using the sidebar.")

    elif selected_page == "Sign Up":
        sign_up()

    elif selected_page == "Log In":
        user=login()
        if user:
           
            st.session_state["username"] = user['key']
            
    elif selected_page == "Legal Advice":
        # Check if the user is authenticated
        if hasattr(st.session_state, 'is_authenticated') and st.session_state.is_authenticated:
            user_prompt = st.text_area("Enter your legal query:")

            wav_audio_data = st_audiorec()


            
            if st.button("Get Legal Advice"):

                if user_prompt:
                    query = user_prompt
                    # Get legal advice from OpenAI
                    
                elif wav_audio_data is not None:
                
                    with open('myfile.wav', mode='bw') as f:
                        f.write(wav_audio_data)

                    audio_file= open("myfile.wav", "rb")
                    transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                    )
                    query = transcript.text
                    st.write(query)
                
                if user_prompt or wav_audio_data is not None:
                    legal_advice = get_legal_advice(query)

                    user = db.get(st.session_state.username)
                    responses = user["responses"]
                    responses.append({'query': query, 'response' : legal_advice})
                    updates = {'responses' : responses}
                    db.update(updates, st.session_state["username"])
                    st.write(legal_advice)
                    #st.success("Legal Advice:")
                    #st.write(legal_advice)
                    #if st.button("Generate legal draft"):
                    legal_draft = get_legal_draft(query, legal_advice)
                    html_response = f"""
                    <html>
                    <body>
                    <p>{legal_draft.replace('\n', '<br>')}
                    </p>
                    </body>
                    </html>"""
                    pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                    pdf = pdfkit.from_string(html_response, False, configuration=pdfkit_config)
                    # Display success message and provide a download link for the generated PDF
                    st.success("🎉 Your legal draft was generated!")
                    st.download_button(
                        "⬇️ Download PDF",
                        data=pdf,
                        file_name="legal_draft.pdf",
                        mime="application/octet-stream",
    )
                   
 

                    
                else:
                    st.enter("Please enter a legal query")



                


                    


        else:
            st.warning("Please log in to access the legal advice chatbot.")


    elif selected_page == "Dashboard":
        # Check if the user is authenticated
        if hasattr(st.session_state, 'is_authenticated') and st.session_state.is_authenticated:
            dashboard()
        else:
            st.warning("Please log in to access the dashboard.")