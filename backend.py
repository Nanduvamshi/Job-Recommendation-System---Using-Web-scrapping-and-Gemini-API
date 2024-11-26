from flask import Flask, request, render_template, jsonify
import os
from flask_cors import CORS

import google.generativeai as genai
genai.configure(api_key='#paste your Gemini API key that is generated from the Gemini API website')
model = genai.GenerativeModel("gemini-1.5-flash",system_instruction="Read the whole resume, just give the skills mentioned in that in csv format consider only skills related to computer science dont take any soft skills and certifications,dont give anything extra than that.")

def initialize():
    import pandas as pd
    df = pd.read_csv("postings2.csv")
    # df.head()
    # df.info()

    df=df[0:1000]
    # df.shape
    # df.isna().sum()
    from sklearn.impute import SimpleImputer

    imp_freq = SimpleImputer(strategy = 'most_frequent')
    df['job_skills'] = imp_freq.fit_transform(df[['job_skills']]).ravel()
    # df.isna().sum()
    from sklearn.feature_extraction.text import TfidfVectorizer 
    tdif = TfidfVectorizer(stop_words = 'english')
    df['job_summary']=df['job_summary'].fillna('')
    tdif_matrix = tdif.fit_transform(df['job_summary'])
    # tdif_matrix.shape

    from sklearn.metrics.pairwise import linear_kernel
    cosine_sim = linear_kernel(tdif_matrix,tdif_matrix)
    indices = pd.Series(df.index, index=df['job_title']).drop_duplicates()
    return df


def recommend_jobs(df,skills):  
    # input_skills = input('enter skills').lower().split(',') 
    input_skills =skills.lower().split(',') 
    matched_jobs = df[df['job_skills'].apply(lambda x: any(skill in x.lower() for skill in input_skills))]
    jsonStr='{"jobs":['
    if not matched_jobs.empty:
        print("Recommended Job Titles and Links:")
        for _, row in matched_jobs.iterrows():
            # print(f"\"name\": {row['job_title']} ,\"link\": {row['job_link']}\"")
            # print(f"\"name\": {row['job_title']} ,\"link\": {row['job_link']}\"")
            # jsonStr += "{"+'"job_title": '+'"'+f'{row['job_title']}'+'"'+","+'"job_link": '+'"'+f'\"{row['job_link']}'+'"'+"},"
            tit=row['job_title'].replace('"'," ")
            jsonStr += '{' + \
                '"job_title": "' + f"{tit}" + '", ' + \
                '"job_link": "' + f"{row['job_link']}" + '"' + \
                '},'

    jsonStr=jsonStr[:-1]
    jsonStr+="]}"
    return jsonStr

df=initialize()
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_form():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        print('1')
        filename = file.filename
        # filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filename)
        print('2')
        sample_pdf = genai.upload_file( f"./{filename}")
        print('3')
        response = model.generate_content(["Give me a csv of skills preseneted in this resume. consider only skills related to computer science dont take any soft skills and certifications", sample_pdf])
        print(response.text)
        skills=response.text
        jsonStr=recommend_jobs(df,skills)
        import json

        return json.loads(jsonStr), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    app.run(debug=True)





