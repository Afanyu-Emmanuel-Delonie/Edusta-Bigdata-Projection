# EduStat — Student Performance Analytics Platform

A full-stack web application that combines **Django**, **Machine Learning**, and **interactive data visualization** to help educational institutions monitor student performance, identify at-risk students, and make data-driven decisions.

> Built as a Big Data course final project, this system demonstrates end-to-end ML integration — from raw CSV data to live predictions served through a Django web interface.

---

## Live Demo

> Deployed on Render.com — [View Live](https://your-app.onrender.com) *(update with your URL)*

---

## Screenshots

> *(Add screenshots of your dashboard, risk tracker, and insights pages here)*

---

## Features

- **Analytics Dashboard** — Real-time overview of student GPA distribution, pass/fail rates, and department-level performance
- **Risk Tracker** — Flags at-risk students based on CA scores, attendance, and historical baselines
- **Graduation Analytics** — Tracks graduation readiness across academic years
- **Institutional Insights** — Department consistency matrix, teacher recovery rates, and course-level pass rate charts
- **Data Management** — Bulk CSV/Excel upload for semester records with validation
- **ML Prediction Engine** — Random Forest + Logistic Regression models predicting Pass/Fail outcomes
- **Secure Authentication** — Session-based login with "Remember Me" support
- **Responsive UI** — Clean interface built with Tailwind CSS, works on all screen sizes

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1, Django REST Framework |
| ML / Data | scikit-learn, Pandas, NumPy, SciPy, XGBoost |
| Visualization | Matplotlib, Seaborn |
| Frontend | Tailwind CSS (CDN), Vanilla JS |
| Database | SQLite (dev) / PostgreSQL (production) |
| Deployment | Render.com, Gunicorn, WhiteNoise |
| Reports | ReportLab, xhtml2pdf, python-docx |

---

## ML Pipeline

Two classification models are trained on engineered student features:

```
Raw CSV Data
    └── Feature Engineering (attendance, CA scores, exam averages, risk indicators)
            └── Train/Test Split (80/20)
                    ├── Random Forest Classifier  ← primary model
                    └── Logistic Regression       ← baseline comparison
                            └── Saved as .pkl → loaded by Django for live predictions
```

**Metrics evaluated:** Accuracy, Precision, Recall, F1-score

---

## Project Structure

```
Edusta-Bigdata-Projection/
├── edustat/                    # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── performance/                # Core analytics app
│   ├── ml_models/              # ML engine, trainer, saved .pkl models
│   ├── management/commands/    # Custom management commands
│   ├── processors/             # Chart helpers, data handlers
│   ├── templatetags/
│   ├── models.py               # Student, AcademicRecord, Department, Course
│   ├── views.py                # Dashboard, risk tracker, insights, data upload
│   └── urls.py
├── accounts/                   # Authentication app (login/logout)
├── templates/                  # HTML templates
│   ├── base.html
│   ├── accounts/
│   └── performance/
├── static/                     # Static assets (images, JS)
├── media/                      # User-uploaded files
├── scripts/                    # Standalone utility scripts
│   ├── generate_data.py
│   └── train_now.py
├── manage.py
├── requirements.txt
└── render.yaml
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Edusta-Bigdata-Projection.git
cd Edusta-Bigdata-Projection
```

### 2. Set up the Python environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Set up the database

```bash
python manage.py migrate
```

### 4. Create an admin account

```bash
python manage.py createsuperuser
```

### 5. (Optional) Load sample data

```bash
python scripts/generate_data.py
```

### 6. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`

---

## Deployment on Render

The project is pre-configured via `render.yaml`:

| Setting | Value |
|---|---|
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn edustat.wsgi:application` |
| Database | PostgreSQL (auto-provisioned) |

Connect your GitHub repo to [Render.com](https://render.com) and it deploys automatically.

Set these environment variables on Render:

```
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://...  (auto-set by Render)
```

---

## Data Format

To import student records via the Data Management page, your CSV should include:

| Column | Description |
|---|---|
| `student_id` | Unique student identifier |
| `first_name` / `last_name` | Student name |
| `department_code` | e.g. `CS`, `ENG`, `BIZ` |
| `course_code` | e.g. `CS101` |
| `ca_total` | Continuous Assessment score |
| `mid_term` | Mid-term exam score |
| `final_exam` | Final exam score |
| `attendance_rate` | Float between 0 and 1 |
| `academic_year` | e.g. `2025/2026` |

---

## What I Learned

- Integrating trained ML models (`.pkl`) into a live Django web application
- Building a multi-app Django project with clean separation of concerns
- Handling bulk data imports with transactional integrity using `transaction.atomic()`
- Deploying a full-stack Python app to production with PostgreSQL on Render
- Designing responsive dashboards with Tailwind CSS

---

## Author

**Your Name**
- GitHub: [@your-username](https://github.com/your-username)
- LinkedIn: [linkedin.com/in/your-profile](https://linkedin.com/in/your-profile)

---

## License

This project is open source and available under the [MIT License](LICENSE).
