import streamlit as st
import os
from dotenv import load_dotenv
from utils.helper import extract_text_from_pdf
import google.generativeai as genai
from deep_translator import GoogleTranslator
from fpdf import FPDF
from PyPDF2 import PdfReader

from dotenv import load_dotenv

import time

# ✅ Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Supported languages
languages = {
    "English": "en", "Urdu": "ur", "Sindhi": "sd", "Arabic": "ar",
    "French": "fr", "German": "de", "Spanish": "es"
}

# ✅ PDF path
PDF_PATH = r"pdf.pdf"

# ✅ Extract PDF text
try:
    doc_text = extract_text_from_pdf(PDF_PATH)
except Exception as e:
    st.error(f"❌ Failed to open PDF: {e}")
    st.stop()

# ✅ App UI
st.title("📖 AI Chatbot – Basic Principles of Islam (RAG + Gemini)")
selected_lang = st.selectbox("🌐 Select language for response:", list(languages.keys()))
question = st.text_input("💬 Ask your question about Islam...")

response_format = st.radio("📄 Choose response type:", ["Short", "Long"], horizontal=True)

if question:
    with st.spinner("🤖 Generating answer with Gemini..."):
        prompt = f"""
        Context from Islamic PDF:
        {doc_text[:3000]}

        User Question:
        {question}

        Provide:
        1. A short summary.
        2. A detailed answer.
        """

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            full_answer = response.text.strip()

            if not full_answer or "I don't have" in full_answer or "I'm not sure" in full_answer:
                st.warning("🤷 No relevant content found for this question.")
            else:
                parts = full_answer.split("\n", 1)
                short_ans = parts[0].strip()
                long_ans = parts[1].strip() if len(parts) > 1 else "More details not available."

                answer_to_show = short_ans if response_format == "Short" else long_ans

                if selected_lang != "English":
                    answer_to_show = GoogleTranslator(source='auto', target=languages[selected_lang]).translate(answer_to_show)

                st.markdown(f"### 📜 {'Short' if response_format == 'Short' else 'Long'} Form Answer")
                st.info(answer_to_show)

                # ✅ Save to PDF
                try:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.set_font("Arial", size=12)

                    pdf_text = f"Q: {question}\n\nAnswer:\n{answer_to_show}"
                    pdf.multi_cell(0, 10, pdf_text.encode('latin-1', 'replace').decode('latin-1'))

                    output_path = "answer_output.pdf"
                    pdf.output(output_path)

                    with open(output_path, "rb") as f:
                        st.download_button("📅 Download Answer as PDF", f, file_name="response.pdf", mime="application/pdf")

                except Exception as e:
                    st.warning("❌ Could not save answer to PDF due to encoding error.")

        except Exception as e:
            st.error(f"❌ Error from Gemini or translation: {e}")

# ✅ Feedback Section
st.markdown("---")
st.markdown("### 🙏 We value your feedback")
feedback = st.text_area("✍️ How was your experience with the AI Islamic chatbot?")
if st.button("Submit Feedback"):
    if feedback.strip():
        with open("feedback.txt", "a", encoding="utf-8") as f:
            f.write(f"Feedback: {feedback}\n---\n")
        st.success("✅ Thank you for your feedback!")
    else:
        st.warning("⚠️ Please write something before submitting.")
