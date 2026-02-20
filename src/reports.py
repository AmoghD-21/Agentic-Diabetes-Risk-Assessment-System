# from fpdf import FPDF
# from  datetime import datetime
# import re

# class DiabetesReport(FPDF):
#     def header(self):
#         self.set_font('Helvetica', 'B', 15)
#         self.cell(0, 10, 'Diabetes Risk Assessment Report', 0, 1, 'C')
#         self.set_font('Helvetica', 'I', 10)
#         # FIX: Added .datetime before .now()
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
#         self.cell(0, 10, f'Generated on: {timestamp}', 0, 1, 'C')
#         self.ln(10)

#     def footer(self):
#         self.set_y(-15)
#         self.set_font('Helvetica', 'I', 8)
#         self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# def sanitize_text(text):
#     """Removes emojis/symbols that standard PDF fonts can't handle."""
#     if not text: return ""
#     # Ensures the text is safe for the latin-1 encoding used by FPDF core fonts
#     return re.sub(r'[^\x00-\x7F]+', '', text)

# def generate_pdf_report(metrics, result, advice):
#     pdf = DiabetesReport()
#     pdf.add_page()
    
#     # 1. Metrics
#     pdf.set_font('Helvetica', 'B', 12)
#     pdf.cell(0, 10, '1. Patient Metrics', 0, 1)
#     pdf.set_font('Helvetica', '', 11)
#     for key, value in metrics.items():
#         pdf.cell(0, 8, f"- {key.capitalize()}: {value}", 0, 1)
#     pdf.ln(5)
    
#     # 2. Results
#     pdf.set_font('Helvetica', 'B', 12)
#     pdf.cell(0, 10, '2. Clinical Analysis Result', 0, 1)
#     pdf.set_font('Helvetica', 'B', 11)
    
#     # Logic for risk color coding
#     if "High" in str(result):
#         pdf.set_text_color(200, 0, 0) # Red
#     else:
#         pdf.set_text_color(0, 128, 0) # Green
        
#     pdf.cell(0, 10, f"Assessment: {sanitize_text(str(result))}", 0, 1)
    
#     # 3. Recommendations
#     pdf.set_text_color(0, 0, 0) # Reset to black
#     pdf.ln(5)
#     pdf.set_font('Helvetica', 'B', 12)
#     pdf.cell(0, 10, '3. Personalized Recommendations', 0, 1)
#     pdf.set_font('Helvetica', '', 10)
    
#     # Clean markdown formatting and sanitize
#     clean_advice = advice.replace('#', '').replace('*', '').strip()
#     pdf.multi_cell(0, 8, sanitize_text(clean_advice))
    
#     # fpdf2's output() returns bytes by default, which Streamlit needs
#     return bytes(pdf.output())




from fpdf import FPDF
from datetime import datetime
import re

class DiabetesReport(FPDF):
    def header(self):
        # Header with professional title
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Diabetes Risk & Nutrition Analysis', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 10)
        
        # Using the correct datetime reference based on your import
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 10, f'Report Generated: {timestamp}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        # Page numbering
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def sanitize_text(text):
    """Removes non-ASCII characters (emojis/symbols) to prevent PDF crashes."""
    if not text: return ""
    # Strips everything that isn't a standard keyboard character
    return re.sub(r'[^\x00-\x7F]+', '', text)

def generate_pdf_report(metrics, result, advice, diet_plan=None):
    """Generates a professional PDF containing metrics, ML results, and the diet plan."""
    pdf = DiabetesReport()
    pdf.add_page()
    
    # --- 1. Patient Metrics Section ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, ' 1. Extracted Clinical Metrics', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 11)
    for key, value in metrics.items():
        pdf.cell(0, 8, f"   - {key.capitalize()}: {value}", 0, 1)
    pdf.ln(5)
    
    # --- 2. ML Analysis Section ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, ' 2. AI Risk Assessment', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    # Risk Color Coding
    if "High" in str(result):
        pdf.set_text_color(200, 0, 0) # Professional Red
    else:
        pdf.set_text_color(0, 128, 0) # Professional Green
        
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 10, f"   Result: {sanitize_text(str(result))}", 0, 1)
    
    # Reset Text Color
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # --- 3. Personalized 7-Day Diet Plan Section ---
    # We prioritize the diet plan if it exists
    if diet_plan:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, ' 3. Indian Vegetarian 7-Day Nutrition Plan', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        # Clean markdown table symbols for a cleaner PDF look
        clean_plan = diet_plan.replace('|', ' ').replace('-', '').replace('#', '').strip()
        pdf.multi_cell(0, 7, sanitize_text(clean_plan))
    else:
        # Fallback to general advice if no specific plan was generated
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, ' 3. General Recommendations', 0, 1, 'L', fill=True)
        pdf.ln(2)
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 7, sanitize_text(advice.replace('#', '').replace('*', '')))

    # Return as bytes for Streamlit download_button
    return bytes(pdf.output())