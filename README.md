# Conversation Archiver

A desktop application built with PySide6 that allows users to archive conversations (e.g., with AI models) into a styled PDF document. It leverages Puppeteer (Node.js) for high-quality PDF generation from HTML and `pypdf` for merging PDF files.

## Features

*   **Rich Text Input**: Supports Markdown, including tables and syntax-highlighted code blocks.
*   **Customizable Output**: Option to include customizable headings for each conversation turn.
*   **High-Quality PDFs**: Generates styled PDF pages using web technologies (HTML/CSS) via Puppeteer.
*   **Continuous Archiving**: Merges new conversation pages into an existing PDF or creates a new one.
*   **Responsive UI**: A non-blocking user interface that remains responsive while the PDF is being generated.

## How It Works

The application follows a multi-process architecture to ensure the UI remains responsive:

1.  **Frontend (PySide6)**: The main `app.py` script creates the GUI. When the user clicks "Add to PDF," it gathers the text and settings from the UI.
2.  **Backend (Python)**: Instead of generating the PDF directly, the main app starts a separate thread (`PdfWorker`). This worker calls the `pdf_engine.py` script, which:
    a. Converts the user's Markdown input into styled HTML.
    b. Injects the HTML into a template with CSS for styling, fonts, and emoji support.
    c. Saves this as a temporary `_temp.html` file.
3.  **PDF Generation (Node.js)**: The Python script then calls the `generate_pdf.js` Node.js script.
    a. **Puppeteer**, a headless browser automation library, opens the `_temp.html` file.
    b. It renders the page just like a web browser and prints it to a temporary PDF file (`_temp_page.pdf`).
4.  **Merging (Python)**: The Python script then merges this newly created page into the main PDF document using the `pypdf` library.
5.  **Cleanup**: All temporary files are removed, and a success message is displayed in the UI.

## Technologies Used

*   **Python 3**: For the main application logic.
    *   **PySide6**: The official Qt for Python library for the GUI.
    *   `pypdf`: For merging PDF documents.
    *   `Markdown` & `Pygments`: For converting Markdown text to styled HTML.
*   **Node.js**: For the PDF generation backend.
    *   **Puppeteer**: Headless Chrome/Chromium automation.
*   **HTML/CSS**: For styling the content of the PDF.

## Setup Instructions

### Prerequisites

*   **Python**: Version 3.7 or newer.
*   **Node.js**: Version 14.x or newer, along with `npm`.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [your-repo-url]
    cd ConversationArchiver
    ```

2.  **Set up a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

## Usage

1.  **Run the application:**
    ```bash
    python app.py
    ```
2.  **Choose a PDF File**:
    *   Click the "Choose File..." button to select an existing PDF you want to add pages to.
    *   If you don't select a file, the first page you generate will become a new PDF file in the project's root directory.
3.  **Enter Text**:
    *   Type or paste your text into the "User Message" and "Model Response" text boxes. You can use Markdown for formatting.
    *   Customize the headings for each section if desired.
4.  **Add to PDF**:
    *   Click the "Add to PDF" button.
    *   The status bar will show "Processing..." and will update to "Success!" when the page has been added.

## Contributing

We welcome contributions! If you've found a bug or have a feature request, please open an issue on the GitHub repository.

---

_This README was updated to provide a more comprehensive guide for new developers._
