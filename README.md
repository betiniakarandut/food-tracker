# 🍽️ Food Service Application 

A web application for managing food service, built with FastAPI and featuring real-time updates and efficient participant tracking.

## 🚀 Features

*   **Meal Registration:**  Register participants for meals (breakfast, lunch, dinner) with automatic meal time selection based on the current time. ⏰
*   **Real-time Awaiting List:**  View a live, updating list of participants awaiting service for each meal. 🔄
*   **Meal Counts:**  See the number of participants served for each meal time. 📊
*   **Participant Status:** Check the status of a participant for a specific meal (awaiting service, served, or not registered). ✅
*   **Remaining Participants Filter:** Filter and view participants who haven't requested a meal at a given meal time. 🕵️‍♀️
*   **Confirmation:** Confirm when food has been served to a participant. 👍
*   **Efficient Participant Tracking:**  Know who has eaten and who is still waiting. 💯
*   **User-Friendly Interface:** Easy-to-use web interface. ✨

## 🛠️ Technologies Used

*   **Backend:** Python, FastAPI 🐍
*   **Database:** SQLite 🗄️
*   **Frontend:** HTML, CSS, JavaScript 🕸️
*   **Real-time Updates:** Server-Sent Events (SSE) 📡

## ⚙️ Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/betiniakarandut/food-tracker.git](https://github.com/betiniakarandut/food-tracker.git)
    ```

2.  **Navigate to the project directory:**

    ```bash
    cd food-tracker
    ```

3.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv  # Create the virtual environment
    source venv/bin/activate  # Activate the virtual environment (Linux/macOS)
    venv\Scripts\activate  # Activate the virtual environment (Windows)
    ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the application:**

    ```bash
    uvicorn main:app --reload --port 8000
    ```

    This will start the FastAPI application on port 8000.  Open your web browser and go to `http://localhost:8000` to access the application.

## 📦 Deployment

1.  **Push to GitHub:** Ensure your code is pushed to a GitHub repository (see the contributing section for how to do this).
2.  **Choose a Platform:** Select a deployment platform (e.g., Render, Heroku, PythonAnywhere). Render is recommended for ease of use.
3.  **Follow Platform Instructions:** Consult the documentation for your chosen platform for detailed deployment steps. Ensure to configure static files serving correctly.

## 🗄️ Database Setup

The application uses SQLite. A `meals.db` file will be created automatically in your project directory when you first run the app.  For production, using an external database service (like PostgreSQL) is highly recommended.

## 🤝 Contributing

Contributions are welcome!  Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Commit your changes with a clear message.
5.  Push your branch to your forked repository.
6.  Submit a pull request.

## 📝 License

[MIT](LICENSE)

## 🎉 Acknowledgements

*   Built with the amazing FastAPI framework.
*   Inspired by the need for efficient food service management.

## Contact
If you have any questions or suggestions, please feel free to contact me.