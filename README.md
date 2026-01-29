# EDUSTAT: Big Data Student Performance Projection

**Empowering Academic Excellence through Predictive Analytics**

---

## 📌 Project Overview

EDUSTAT is a data-driven platform designed to bridge the gap between raw academic records and actionable student insights. By leveraging Big Data principles and Machine Learning, the system critiques student results and projects future performance, enabling educators to intervene before a student falls behind.

---

## 🎯 Key Features

* **Predictive Critique Engine**: Uses Random Forest models to analyze student performance and provide qualitative feedback.
* **Automated Data Processing**: Seamlessly handles large datasets of student marks and attendance using Pandas and NumPy.
* **Real-time Analytics Dashboard**: Visualizes academic trends for faculty and administration.
* **Production-Ready Deployment**: Configured with WhiteNoise for static file management and Gunicorn for high-performance serving on Render/Linux.

---

## 🛠 Tech Stack

* **Backend**: Django (Python)
* **Database**: PostgreSQL (Production) / SQLite (Local Development)
* **Data Science**: Pandas, NumPy, Scikit-Learn
* **Deployment**: Gunicorn, WhiteNoise, Render Cloud

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10+
* Virtual Environment (venv)

### 2. Local Installation
```bash
# Clone the repository
git clone https://github.com/your-username/Edusta-Bigdata-Projection.git
cd Edusta-Bigdata-Projection

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

---

## 📊 Machine Learning Workflow

The "Critique" feature follows a rigorous data science pipeline:

1. **Ingestion**: Data is pulled from PostgreSQL into a Pandas DataFrame.
2. **Transformation**: Features (Attendance, Midterm, Assignments) are converted to NumPy arrays.
3. **Modeling**: A Random Forest Classifier is trained to categorize student risk levels.
4. **Output**: The system generates a qualitative critique based on model probability scores.

---

## ☁️ Deployment Strategy

This project is optimized for cloud environments:

* **Static Files**: Managed via `whitenoise` to ensure CSS/JS load instantly without a separate CDN.
* **Database**: Uses `dj-database-url` to switch dynamically between local and cloud databases.
* **Availability**: Integrated with Cron Jobs to eliminate "cold starts" and ensure 24/7 dashboard availability.

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

