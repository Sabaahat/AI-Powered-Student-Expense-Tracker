💰 AI-Powered Student Expense Tracker

<p align="center">
  <img src="banner.png" alt="AI-Powered Student Expense Tracker Banner" width="100%">
</p><h1 align="center">AI-Powered Student Expense Tracker</h1><p align="center">
  <b>Plan Better. Spend Wisely. Achieve More.</b>
  <br>
  A smart AI-powered expense management application designed especially for students.
</p><p align="center">
  <img src="https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white">
  <img src="https://img.shields.io/badge/Streamlit-Web%20App-FF4B4B?logo=streamlit&logoColor=white">
  <img src="https://img.shields.io/badge/Google%20Gemini-AI-8E75B2?logo=googlegemini&logoColor=white">
  <img src="https://img.shields.io/badge/Machine%20Learning-Scikit--learn-orange">
  <img src="https://img.shields.io/badge/Status-In%20Development-orange">
</p>---

📌 About the Project

The AI-Powered Student Expense Tracker is a Python-based web application designed to help students manage their pocket money, track daily expenses, monitor budgets, and develop better saving habits.

The application combines expense management, data analytics, machine learning, and Artificial Intelligence to make financial tracking easier and smarter.

Using Google Gemini AI, the application aims to provide personalized financial insights, spending analysis, and recommendations to help students make better financial decisions.

🎯 Project Objectives

- Help students manage their pocket money effectively.
- Track daily, weekly, and monthly expenses.
- Monitor budgets and understand spending patterns.
- Encourage better saving habits.
- Analyze financial behaviour using data analytics.
- Provide AI-powered financial insights and suggestions.

✨ Key Features

- 💰 Pocket Money Management: Record and monitor available pocket money.
- 📝 Expense Tracking: Add, edit, delete, and manage expenses.
- 📅 Expense History: View previously recorded transactions.
- 📊 Expense Analysis: Understand spending through charts and reports.
- 🎯 Budget Monitoring: Track expenses against budget limits.
- ⚠️ Budget Alerts: Identify when spending approaches the budget limit.
- 🤖 AI-Powered Suggestions: Receive personalized spending and saving recommendations.
- 🔮 Spending Prediction: Explore estimated future expenses using historical spending data.
- 📈 Financial Analytics: Analyze daily and monthly spending patterns.

Note: Features are being implemented and tested as part of project development.

🛠️ Technologies Used

Technology| Purpose
Python| Core programming language
Streamlit| Web application interface
SQLite| Database management
Pandas| Data processing and analysis
Matplotlib| Data visualization
Scikit-learn| Machine learning and prediction
Google Gemini API| AI-powered financial insights
NumPy| Numerical operations
Git & GitHub| Version control and project hosting

🤖 AI Integration

Google Gemini AI is planned as the intelligent assistant of this project.

It will help students:

- Analyze their spending habits.
- Identify unnecessary expenses.
- Receive personalized saving suggestions.
- Understand their financial behaviour.
- Get intelligent financial recommendations.

📂 Project Structure

AI-Powered-Student-Expense-Tracker/
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   └── expenses.db
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── analytics.py
│   ├── charts.py
│   ├── ai_advisor.py
│   └── ui_helpers.py
│
├── .env
├── .env.example
├── .gitignore
├── app.py
├── seed_data.py
├── requirements.txt
├── README.md
└── banner.png

📁 Module Description

File| Description
app.py| Main Streamlit application and page routing
config.py| Environment configuration and constants
database.py| SQLite initialization and CRUD operations
analytics.py| Pandas aggregations and spending analysis
charts.py| Matplotlib charts and visualizations
ai_advisor.py| Google Gemini API integration
ui_helpers.py| Custom CSS, KPI cards and budget alerts
seed_data.py| Generates sample student expense data
config.toml| Custom Streamlit theme configuration

⚙️ Installation and Setup

1. Clone the Repository

git clone https://github.com/Sabaahat/AI-Powered-Student-Expense-Tracker.git

2. Navigate to the Project Folder

cd AI-Powered-Student-Expense-Tracker

3. Create a Virtual Environment

python -m venv venv

4. Activate the Virtual Environment

Windows:

venv\Scripts\activate

Linux / macOS:

source venv/bin/activate

5. Install Required Libraries

pip install -r requirements.txt

6. Configure Gemini API

Create a ".env" file in the project root directory.

Add your API configuration:

GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=your_available_gemini_model

Replace the placeholders with your actual Gemini API key and an available model.

Important: Never upload your ".env" file or expose your private API key on GitHub.

7. Run the Application

streamlit run app.py

The application will open in your browser.

🚀 Future Enhancements

- Advanced AI financial assistant.
- More detailed expense reports.
- Improved spending prediction.
- Personalized monthly saving goals.
- Enhanced dashboard and user experience.
- More advanced financial analytics.

👩‍💻 Developer

Sabaahat Y

B.Tech – Computer Science and Engineering (Data Science)

GitHub: "Sabaahat" (https://github.com/Sabaahat)

LinkedIn: "Connect with me" (https://www.linkedin.com/in/sabaahat-y-0a99782b6)

GitHub Repository: "AI-Powered Student Expense Tracker" (https://github.com/Sabaahat/AI-Powered-Student-Expense-Tracker)

---

<p align="center">
  ⭐ If you find this project interesting, consider giving it a star!
  <br><br>
  <b>Made with ❤️ using Python and AI</b>
</p>
