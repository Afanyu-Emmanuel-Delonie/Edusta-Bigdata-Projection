
# Edustat 📊: Data Visualization and Reporting Platform

## ✨ Overview

**Edustat** is a web application built using the **Django** framework, focusing on advanced data visualization and sophisticated reporting. It utilizes a powerful set of Python libraries for data handling and document generation, and features a clean, responsive interface styled with **Tailwind CSS**.

The project is structured for easy local development and is fully configured for cloud deployment on **Render.com**.

## 🚀 Key Features

* **Django Backend:** A secure and robust application framework using **Django** version 5.2.8
* **API Development:** Uses **Django REST Framework** version 3.16.1 for scalable API endpoints
* **Data Processing:** Leverages **Pandas** (2.3.3) and **NumPy** (2.3.5) for efficient data manipulation and analysis.
* **Reporting:**
    * Generates high-quality PDF reports using **WeasyPrint** (66.0) and supporting libraries.
    * Handles Excel file creation and reading using **OpenPyXL** (3.1.5) and **xlrd** (2.0.2).
* **Visualization:** Creates charts and graphs using **Matplotlib** (3.10.7) and **Seaborn** (0.13.2).
* **Modern Frontend:** Utilizes the utility-first **Tailwind CSS** (4.1.17) for styling.
* **i18n Support:** Includes **arabic-reshaper** (3.0.0) and **python-bidi** (0.6.7) for bi-directional text handling.

---

## 🛠️ Local Development Setup

### 📋 Prerequisites

* **Python 3.x**
* **Node.js & npm**

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd edustat

2. Python Environment Setup
Install Python dependencies as listed in requirements.txt:

Bash

# Recommended: Create and activate a virtual environment first
python -m venv venv
source venv/bin/activate 

pip install -r requirements.txt
3. Frontend Setup (Tailwind CSS)
Install Node.js dependencies from package.json:

Bash

npm install
4. Run the Application
You will need two separate terminal windows for the following steps:

A. Start the CSS Watcher
In the first terminal, run the script to continuously compile Tailwind CSS:

Bash

npm run watch:css
# This runs: tailwindcss -i ./static/src/style.css -o ./static/dist/css/style.css --watch
Keep this window open.

B. Start the Django Server
In the second terminal (with your Python environment active), prepare the database and start the server:

Bash

python manage.py migrate
python manage.py runserver
The application will be accessible at http://127.0.0.1:8000/.

🌐 Deployment on Render
The project is pre-configured for deployment on Render.com using the instructions in render.yaml.

Configuration	Value
Type	web
Runtime	"python"
Build Command	"pip install -r requirements.txt"
Start Command	"gunicorn edustat.wsgi:application"

Export to Sheets

To Deploy: Simply connect your GitHub repository to your Render account, and the platform will automatically detect and follow the configuration in render.yaml.

🤝 Contributing
We welcome contributions! Please feel free to open an issue for bugs or suggestions, or submit a pull request with improvements.
=======
# Edusta Big Data – Student Performance Prediction System


# 📌 Project Overview

This project is part of the Big Data course, where we designed and implemented a machine learning system to analyze and predict student academic performance (Pass/Fail) based on multiple academic and behavioral indicators.

# The project integrates: 

- Django Web Framework

- Machine Learning (Random Forest + Logistic Regression)

- Data Cleaning & Feature Engineering

- Model Evaluation & Prediction

- Team-based development using Git & Branching


The main goal of the system is to help educators identify students at risk of failing early, enabling timely intervention.


---------------------------------------------

# 📊 Dataset Description

We used a prepared dataset containing cleaned and engineered features of students such as:

- Assignment, midterm, final exam scores
- Attendance percentage
- Consistency and improvement metrics
- Exam averages
- Risk indicators
- Performance gaps
- Final pass_fail label (target variable)


Final training was performed on:

performance/ml/data/features.csv

This dataset contains fully numeric engineered features, making it ideal for machine learning classification.


---------------------------------------

# 🤖 Machine Learning Models

Two models were implemented and evaluated:

- 1. Random Forest Classifier

Main model for prediction

Works best with engineered numeric features

Handles non-linear patterns

No scaling required

Provided highest accuracy and stability


- 2. Logistic Regression (Baseline)

Simple linear classifier

Used as a comparison model

Helps validate Random Forest performance

Both models generate classification metrics including:

- Accuracy
- Precision
- Recall
- F1-score


# 🛠 ML Pipeline Overview

- Data Processing

- Load dataset

- Extract features (X) and target (y)

- Perform train/test split

- Prepare data for model training


Implemented in:

performance/ml/scripts/data_processing.py

Model Training

Train Random Forest and Logistic Regression

Evaluate results

Save trained model as .pkl


Implemented in:

performance/ml/scripts/train_model.py

Saved models are stored in:

performance/ml/models/

Prediction Logic

Load saved model

Accept student data input

Execute prediction

Return pass/fail + probability


Will be implemented in:

performance/ml/scripts/predict_model.py



# 👥 Team Responsibilities

- Member 1–2: Dataset Cleaning

Handle missing values

Resolve inconsistencies

Generate clean dataset


- Member 3: Feature Preparation

Analyze data

Engineer useful features

Split into training & testing sets


- Member 4: Model Training

Train Random Forest

Train Logistic Regression

Evaluate model performance

Save model files


- Member 5: Prediction Logic

Load saved model

Implement prediction function

Test prediction output


- Member 6: Django Backend Integration

Connect prediction function to Django

Build prediction API endpoint

Handle backend logic


- Member 7: Django Frontend

Build input form UI

Display prediction results

Style and finalize user interface


- Member 8: Documentation & Deployment

Final README

Project documentation

Prepare for presentation


# 🏗 Project Structure

performance/
  ml/
    data/
      features.csv
    models/
      random_forest_passfail.pkl
      logistic_regression_passfail.pkl
    scripts/
      data_processing.py
      train_model.py
      predict_model.py
webapp/
  ...
README.md
manage.py



▶ How to Run the Project

1. Clone repository

git clone <repository-url>

2. Create virtual environment

python -m venv venv
venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Run Django server

python manage.py runserver

5. Train model (if needed)

python performance/ml/scripts/train_model.py


# 🎯 Project Goal

This system helps educational institutions:

Predict student outcomes early

Identify at-risk students

Improve intervention strategies

Enhance teacher decision-making


By combining Big Data techniques with predictive analytics, this project demonstrates how machine learning can be applied in academic performance monitoring.



📞 Contact & Team

Developed by:
Edusta Big Data Final Project Group

Course: Big Data Analytics

