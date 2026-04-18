# 🥗 AI Diet Coach: Multi-Agent Personal Nutrition System

An intelligent, production-grade agentic AI system for personal diet management. Built with **LangGraph**, this application utilizes a multi-agent architecture to autonomously calculate nutritional targets, log meals via real-world APIs, generate dynamic meal plans, and provide data-driven dietary coaching.

### 🌟 **[Live Demo: Try the AI Diet Coach Here](YOUR_STREAMLIT_LINK_HERE)** ---

## 🧠 Architecture Overview

This project moves beyond standard chatbots by implementing a **stateful, multi-agent orchestrator** using LangGraph. 

An LLM-powered Router intercepts user queries and dynamically directs them to specialized agents:
* **Profile Agent:** Calculates BMR, TDEE, and macro-splits using the Mifflin-St Jeor equation.
* **Nutrition Agent:** Queries the USDA FoodData Central API for accurate nutritional metrics, handles missing items via LLM estimation, and logs meals.
* **Meal Plan Agent:** Evaluates daily remaining caloric/macro budgets to generate personalized meal suggestions.
* **Coach Agent:** Analyzes 7-day rolling data to provide motivational, data-driven progress assessments.

## ✨ Key Features

* **Agentic Routing:** Smart intent classification ensures the right specialized agent handles each specific task.
* **Real Nutrition Data:** Integration with the **USDA FoodData Central API** for scientifically accurate macro and caloric tracking.
* **Tool Use & Loops:** Agents autonomously trigger functions (fetching data, writing to DB, calculating) and loop back to the LLM to formulate final responses.
* **Persistent Memory:** SQLite integration tracks user profiles, historical meal logs, weight progression, and chat context.
* **Interactive Dashboard:** A sleek UI built with **Streamlit** and **Plotly**, featuring progress rings, macro distribution pies, and 7-day trend analysis.
* **100% Free Tier Stack:** Configured to run on high-speed, free APIs (Groq, Gemini) and free deployment hosting.

## 🛠️ Tech Stack

* **Agent Framework:** LangChain, LangGraph
* **LLM Providers:** Groq (Llama-3.3-70B), Google GenAI (Gemini 2.0 Flash)
* **Frontend UI:** Streamlit
* **Data Visualization:** Plotly, Pandas
* **Database:** SQLAlchemy (SQLite)
* **External APIs:** USDA FoodData Central

---

## 🚀 Installation & Setup (Local Development)

**1. Clone the repository:**
`git clone https://github.com/YourUsername/ai-diet-agent.git`
`cd ai-diet-agent`

**2. Create and activate a virtual environment:**
*Windows:*
`python -m venv venv`
`venv\Scripts\activate`

*Mac/Linux:*
`python3 -m venv venv`
`source venv/bin/activate`

**3. Install dependencies:**
`pip install -r requirements.txt`

**4. Set up Environment Variables:**
Create a `.env` file in the root directory and add your API keys:
`GROQ_API_KEY=your_groq_key_here`
`GOOGLE_API_KEY=your_gemini_key_here`
`USDA_API_KEY=your_usda_key_here`
`LLM_PROVIDER=groq`

**5. Run the Application:**
`streamlit run app.py`

