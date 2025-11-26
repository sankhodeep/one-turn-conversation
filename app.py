import sys
import os
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFileDialog, QMessageBox,
    QCheckBox, QLineEdit
)
from PySide6.QtCore import Signal, QObject
from pdf_engine import create_pdf_page, merge_pdfs

# --- Communication object for worker thread ---
class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:
    - finished: Emits a string to indicate task completion or error.
    """
    finished = Signal(str)

class PdfWorker(QObject):
    """
    Runs the PDF creation and merging process in a separate thread.

    This worker prevents the GUI from freezing during I/O-intensive operations.
    It communicates its status back to the main thread via signals.

    Args:
        user_text (str): The text from the user message input.
        model_text (str): The text from the model response input.
        main_pdf_path (str): The absolute path to the main PDF file.
        show_headings (bool): If True, headings will be added to the PDF.
        user_heading (str): The heading for the user message section.
        model_heading (str): The heading for the model response section.
    """
    def __init__(self, user_text, model_text, main_pdf_path, show_headings, user_heading, model_heading):
        super().__init__()
        self.signals = WorkerSignals()
        self.user_text = user_text
        self.model_text = model_text
        self.main_pdf_path = main_pdf_path
        self.show_headings = show_headings
        self.user_heading = user_heading
        self.model_heading = model_heading

    def run(self):
        """
        Executes the PDF generation and merging task.

        Creates a temporary PDF page with the provided text and then merges it
        into the main PDF document. Emits a 'finished' signal with a success
        or error message.
        """
        try:
            temp_page_path = "_temp_page.pdf"
            
            success_create = create_pdf_page(
                self.user_text, self.model_text, temp_page_path,
                self.show_headings, self.user_heading, self.model_heading
            )
            if not success_create:
                raise RuntimeError("Failed to create the temporary PDF page.")

            success_merge = merge_pdfs(self.main_pdf_path, temp_page_path)
            if not success_merge:
                raise RuntimeError("Failed to merge the new page into the main PDF.")
                
            self.signals.finished.emit("Success! Page added.")
        except Exception as e:
            self.signals.finished.emit(f"Error: {e}")

# --- Main Application Window ---
class MainWindow(QMainWindow):
    """
    The main application window for the Conversation Archiver.

    This class sets up the user interface, including text boxes, buttons,
    and file selection dialogs. It handles user interactions and launches
    the PDF worker thread.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversation Archiver")
        self.setGeometry(100, 100, 700, 800)

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Options ---
        self.show_headings_check = QCheckBox("Show Headings")
        self.show_headings_check.setChecked(True)
        main_layout.addWidget(self.show_headings_check)

        # --- User Message ---
        self.user_heading_entry = QLineEdit("User Message")
        main_layout.addWidget(self.user_heading_entry)
        self.user_text_box = QTextEdit()
        main_layout.addWidget(self.user_text_box)

        # --- Model Response ---
        self.model_heading_entry = QLineEdit("Model Response")
        main_layout.addWidget(self.model_heading_entry)
        self.model_text_box = QTextEdit()
        main_layout.addWidget(self.model_text_box)

        # --- File Chooser ---
        file_layout = QHBoxLayout()
        self.pdf_path_label = QLineEdit("No file selected...")
        self.pdf_path_label.setReadOnly(True)
        file_layout.addWidget(self.pdf_path_label)
        choose_file_button = QPushButton("Choose File...")
        choose_file_button.clicked.connect(self.choose_file)
        file_layout.addWidget(choose_file_button)
        main_layout.addLayout(file_layout)

        # --- Bottom Bar ---
        bottom_layout = QHBoxLayout()
        self.add_button = QPushButton("Add to PDF")
        self.add_button.clicked.connect(self.process_and_add_pdf)
        bottom_layout.addWidget(self.add_button)
        self.status_label = QLabel("Status: Ready")
        bottom_layout.addWidget(self.status_label)
        main_layout.addLayout(bottom_layout)

    def choose_file(self):
        """Opens a file dialog to select the main PDF file."""
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Your Main PDF File", "", "PDF Files (*.pdf)")
        if filepath:
            self.pdf_path_label.setText(filepath)

    def process_and_add_pdf(self):
        """
        Validates inputs and starts the PDF worker thread.

        Retrieves text from the input boxes and the selected PDF path,
        performs basic validation, and then creates and starts a PdfWorker
        to handle the PDF generation.
        """
        user_text = self.user_text_box.toPlainText().strip()
        model_text = self.model_text_box.toPlainText().strip()
        main_pdf_path = self.pdf_path_label.text()

        if not user_text and not model_text:
            QMessageBox.warning(self, "Warning", "Both text boxes are empty.")
            return
        if "No file selected..." in main_pdf_path:
            QMessageBox.warning(self, "Warning", "Please choose a destination PDF file.")
            return

        self.add_button.setEnabled(False)
        self.status_label.setText("Status: Processing...")

        # --- Setup and run worker thread ---
        self.worker = PdfWorker(
            user_text, model_text, main_pdf_path,
            self.show_headings_check.isChecked(),
            self.user_heading_entry.text().strip(),
            self.model_heading_entry.text().strip()
        )
        self.thread = threading.Thread(target=self.worker.run)
        self.worker.signals.finished.connect(self.on_processing_finished)
        self.thread.start()

    def on_processing_finished(self, message):
        """
        Handles the 'finished' signal from the PDF worker thread.

        Updates the status label with the result message, clears the text
        boxes on success, and re-enables the 'Add to PDF' button.

        Args:
            message (str): The status message from the worker.
        """
        if message.startswith("Error"):
            QMessageBox.critical(self, "Error", message)
            self.status_label.setText("Status: Error!")
        else:
            self.status_label.setText(f"Status: {message}")
            self.user_text_box.clear()
            self.model_text_box.clear()
        self.add_button.setEnabled(True)

def main():
    """Initializes and runs the Qt application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()