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
