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
