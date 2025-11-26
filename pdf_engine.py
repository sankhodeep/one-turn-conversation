import os
import subprocess
import base64
import mimetypes
from pypdf import PdfWriter, PdfReader
import html
import markdown
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

def markdown_to_html_final(markdown_text):
    """
    Converts a Markdown string to HTML, with special handling for code blocks.

    This function finds all fenced code blocks, highlights them using Pygments,
    replaces them with placeholders, converts the remaining Markdown to HTML,
    and then re-injects the highlighted code blocks back into the HTML.

    Args:
        markdown_text (str): The Markdown text to convert.

    Returns:
        str: The fully-formatted HTML.
    """
    highlighted_blocks = []

    def _highlight_and_replace(match):
        language = match.group(1).strip()
        content = match.group(2).strip()
        placeholder = f"CODEBLOCK{len(highlighted_blocks)}"

        try:
            lexer = get_lexer_by_name(language)
        except Exception:
            lexer = TextLexer()

        formatter = HtmlFormatter(cssclass="codehilite")
        highlighted_code = highlight(content, lexer, formatter)
        highlighted_blocks.append(highlighted_code)

        # Return a simple placeholder that won't be altered by markdown processing
        return placeholder

    # 1. Find all code blocks, highlight them, and replace with a simple placeholder.
    pattern = re.compile(r"^[ \t]*```([^\n]*)\n(.*?)\n^[ \t]*```", re.DOTALL | re.MULTILINE)
    text_with_placeholders = pattern.sub(_highlight_and_replace, markdown_text)

    # 2. Process the main text (which now contains only placeholders).
    html_output = markdown.markdown(
        text_with_placeholders,
        extensions=['tables', 'nl2br', 'pymdownx.arithmatex'],
        extension_configs={
            'pymdownx.arithmatex': {'generic': True}
        }
    )

    # 3. Replace the placeholders with the fully rendered HTML for the code blocks.
    for i, block_html in enumerate(highlighted_blocks):
        # The markdown processor might wrap the placeholder in <p> tags.
        placeholder_p = f"<p>CODEBLOCK{i}</p>"
        if placeholder_p in html_output:
            html_output = html_output.replace(placeholder_p, block_html)
        else: # Fallback
            html_output = html_output.replace(f"CODEBLOCK{i}", block_html)

    return html_output

def merge_pdfs(main_pdf_path, new_page_path):
    """
    Merges a newly created PDF page into an existing PDF document.

    If the main PDF does not exist, the new page is renamed to become the
    main PDF. Otherwise, the new page is appended to the existing pages.
    The temporary new page file is always removed.

    Args:
        main_pdf_path (str): The path to the main (destination) PDF file.
        new_page_path (str): The path to the temporary single-page PDF to merge.

    Returns:
        bool: True on success, False on failure.
    """
    try:
        if not os.path.exists(main_pdf_path):
            os.rename(new_page_path, main_pdf_path)
            return True

        writer = PdfWriter()
        reader_main = PdfReader(main_pdf_path)
        for page in reader_main.pages:
            writer.add_page(page)
            
        reader_new = PdfReader(new_page_path)
        for page in reader_new.pages:
            writer.add_page(page)
            
        with open(main_pdf_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        return False
    finally:
        if os.path.exists(new_page_path):
            os.remove(new_page_path)

def create_pdf_page(user_text, model_text, image_paths, output_path, show_headings=True, user_heading="User Message", model_heading="Model Response"):
    """
    Creates a single, styled PDF page from user and model text.

    This function generates an HTML file from the input text, applying CSS
    styling and Markdown-to-HTML conversion. It then invokes a Node.js
    script (using Puppeteer) to render this HTML into a PDF.

    Args:
        user_text (str): The text from the user message input.
        model_text (str): The text from the model response input.
        image_paths (list): A list of paths to the images to be added.
        output_path (str): The path where the generated PDF page will be saved.
        show_headings (bool, optional): If True, headings are included. Defaults to True.
        user_heading (str, optional): The heading for the user section. Defaults to "User Message".
        model_heading (str, optional): The heading for the model section. Defaults to "Model Response".

    Returns:
        bool: True if the PDF was created successfully, False otherwise.
    """
    temp_html_path = os.path.join(os.path.dirname(__file__), '_temp.html')
    
    try:
        css_path = os.path.join(os.path.dirname(__file__), 'style.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        user_section = ""
        if user_text:
            if show_headings and user_heading:
                user_section += f"<h1>{html.escape(user_heading)}</h1>"
            user_text_html = markdown_to_html_final(user_text)
            user_section += f"<div class='content'>{user_text_html}</div>"

        model_section = ""
        if model_text:
            if show_headings and model_heading:
                model_section += f"<h1>{html.escape(model_heading)}</h1>"
            model_text_html = markdown_to_html_final(model_text)
            model_section += f"<div class='content'>{model_text_html}</div>"

        image_section = ""
        if image_paths:
            for image_path in image_paths:
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = "application/octet-stream"
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_section += f"<img src='data:{mime_type};base64,{encoded_string}'/>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>PDF Page</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
            <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <style>
                {css_content}
            </style>
        </head>
        <body>
            {user_section}
            {model_section}
            {image_section}
        </body>
        </html>
        """
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        script_path = os.path.join(os.path.dirname(__file__), 'generate_pdf.js')
        subprocess.run(
            ['node', script_path],
            check=True,
            cwd=os.path.dirname(__file__)
        )

        os.rename(os.path.join(os.path.dirname(__file__), '_temp_page.pdf'), output_path)

        print(f"Successfully created PDF page at: {output_path}")
        return True

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error calling Puppeteer script: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
