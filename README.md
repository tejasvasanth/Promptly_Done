#PromptlyDone - The Dual-LLM Code Generation Tool ⚡

Go from idea to complete codebase in minutes. An intelligent tool that optimizes your prompt and generates production-ready code.



## 🤔 About The Project

Starting a new project involves significant time spent on boilerplate code, file structure, and configuration. AI CodeGenius was built to eliminate this bottleneck. It's a powerful developer tool that leverages a unique, dual-LLM pipeline to transform a simple idea into a complete, well-structured codebase.

This project showcases an innovative approach to code generation by first using an AI model to refine the user's intent before using another to write the code, resulting in significantly higher-quality output.

## ✨ Key Features

- **🧠 Intelligent Prompt Optimization:** Uses the Gemini API to analyze a user's basic idea and transform it into a detailed, technical prompt.
- **🏗️ Full Codebase Generation:** Feeds the optimized prompt to the Claude API to generate a complete, structured, and ready-to-use project.
- **✍️ Interactive Review Step:** Allows users to review and edit the AI-optimized prompt before the final code generation, ensuring full control over the output.
- **📦 Downloadable Project:** Delivers the final codebase as a downloadable `.zip` file, ready to be opened in your favorite IDE.

## 🛠️ Built With

This project is a full-stack application built with a modern tech stack:

- **Frontend:** [React.js](https://reactjs.org/)
- **Backend:** [Python](https://www.python.org/) (with Flask/FastAPI)
- **Database:** [SQLite](https://www.sqlite.org/index.html)
- **AI Models:**
  - [Google Gemini API](https://ai.google.dev/) (for prompt optimization)
  - [Anthropic Claude API](https://www.anthropic.com/claude) (for code generation)

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

- Node.js & npm installed
- Python & pip installed

### Installation

1.  **Clone the repo**
    ```sh
    git clone [https://github.com/tejasvasanth/ai-codegenius.git](https://github.com/tejasvasanth/ai-codegenius.git)
    ```
2.  **Backend Setup**
    ```sh
    cd ai-codegenius/backend
    pip install -r requirements.txt
    ```
    Create a `.env` file and add your API keys:
    ```
    GEMINI_API_KEY='YOUR_GEMINI_API_KEY'
    CLAUDE_API_KEY='YOUR_CLAUDE_API_KEY'
    ```
    Run the backend server. The `database.db` file will be created automatically.
    ```sh
    python app.py
    ```

3.  **Frontend Setup**
    ```sh
    cd ai-codegenius/frontend
    npm install
    ```
    Run the frontend development server:
    ```sh
    npm start
    ```
    The application should now be running on `http://localhost:3000`.

## 🖥️ How It Works

1.  **Enter Your Idea:** Start by typing a simple description of the project you want to build.
2.  **Review & Refine:** AI CodeGenius uses Gemini to optimize your idea into a detailed prompt. You can review and edit this prompt to your liking.
3.  **Generate & Download:** Once you approve the prompt, Claude generates the entire codebase, which you can download as a `.zip` file.

| 1. Enter Prompt | 2. Review Optimized Prompt | 3. Download Code |
| :---: | :---: | :---: |
| ![Enter Prompt](https://via.placeholder.com/400x250.png?text=Step+1+Screenshot) | ![Review Prompt](https://via.placeholder.com/400x250.png?text=Step+2+Screenshot) | ![Download Code](https://via.placeholder.com/400x250.png?text=Step+3+Screenshot) |


##  roadmap

- [ ] Support for more languages and frameworks (e.g., Vue, Svelte, Go).
- [ ] Direct integration to create a new GitHub repository.
- [ ] Add Dockerfile generation for easier deployment.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📧 Contact

Tejas Vasanth - [github.com/tejasvasanth](https://github.com/tejasvasanth)
