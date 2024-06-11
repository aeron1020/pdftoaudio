import PyPDF2
import pyttsx3
import os
import re
from tkinter import Tk, Button, Label, Entry, filedialog
from threading import Thread, Event

# Global variables to control the playback
is_paused = Event()
is_stopped = Event()
tts_engine = pyttsx3.init()

def clean_text(text):
    """
    Cleans up the extracted text by removing unwanted characters
    and formatting it for better readability.
    Adds pauses for new paragraphs, bullet points, and numbered lists.
    """
    # Replace double newlines with paragraph pause
    cleaned_text = text.replace('\n\n', ' <paragraph_pause> ').replace('\r\n\r\n', ' <paragraph_pause> ')
    # Replace single newlines with spaces
    cleaned_text = cleaned_text.replace('\n', ' ').replace('\r', ' ')
    # Add pauses for bullet points and numbered lists
    cleaned_text = re.sub(r'([*•-])\s+', r' \1 <bullet_pause> ', cleaned_text)
    cleaned_text = re.sub(r'(\d+\. )', r' \1 <bullet_pause> ', cleaned_text)
    # Remove extra spaces
    cleaned_text = ' '.join(cleaned_text.split())
    return cleaned_text

def read_pdf(file_path, start_page, end_page, save_to_file=False):
    global is_paused, is_stopped, tts_engine
    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            tts_engine.setProperty('rate', 150)
            tts_engine.setProperty('volume', 0.9)

            voices = tts_engine.getProperty('voices')
            print("Available voices:")
            for index, voice in enumerate(voices):
                print(f"{index + 1}: {voice.name}")
            voice_choice = int(input("Select a voice by number: ")) - 1
            tts_engine.setProperty('voice', voices[voice_choice].id)

            full_text = ""
            for page_num in range(start_page - 1, end_page):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                if text:
                    cleaned_text = clean_text(text)
                    full_text += cleaned_text + " "

            segments = full_text.split('<paragraph_pause>')

            if save_to_file:
                output_file = file_path.replace(".pdf", ".mp3")
                for segment in segments:
                    sub_segments = segment.split('<bullet_pause>')
                    for sub_segment in sub_segments:
                        tts_engine.save_to_file(sub_segment, output_file)
                        tts_engine.save_to_file(" ", output_file)
                    tts_engine.save_to_file(" ", output_file)
                tts_engine.runAndWait()
                print(f"Audio saved to {output_file}")
            else:
                for segment in segments:
                    sub_segments = segment.split('<bullet_pause>')
                    for sub_segment in sub_segments:
                        if is_stopped.is_set():
                            return
                        while is_paused.is_set():
                            tts_engine.stop()
                        comma_segments = sub_segment.split('<comma_pause>')
                        for i, comma_segment in enumerate(comma_segments):
                            tts_engine.say(comma_segment)
                            if i < len(comma_segments) - 1:
                                tts_engine.setProperty('pitch', 200)  # High pitch for commas
                                tts_engine.say(",")
                                tts_engine.setProperty('pitch', 100)  # Reset pitch
                        tts_engine.say(" ")
                    tts_engine.say(" ")
                tts_engine.runAndWait()

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def select_file():
    global pdf_file_path
    pdf_file_path = filedialog.askopenfilename(title="Select a PDF file", filetypes=[("PDF files", "*.pdf")])

def start_reading():
    global is_stopped, is_paused
    is_stopped.clear()
    is_paused.clear()
    try:
        start_page = int(start_page_entry.get())
        end_page = int(end_page_entry.get())
        if start_page < 1 or end_page < start_page:
            status_label.config(text="Invalid page range.")
        else:
            status_label.config(text="Reading...")
            Thread(target=read_pdf, args=(pdf_file_path, start_page, end_page)).start()
    except ValueError:
        status_label.config(text="Invalid page number entered.")

def pause_reading():
    if is_paused.is_set():
        is_paused.clear()
    else:
        is_paused.set()

def stop_reading():
    is_stopped.set()
    tts_engine.stop()

if __name__ == "__main__":
    root = Tk()
    root.title("PDF to Audio Reader")

    select_button = Button(root, text="Select PDF File", command=select_file)
    select_button.pack()

    start_page_label = Label(root, text="Start Page:")
    start_page_label.pack()
    start_page_entry = Entry(root)
    start_page_entry.pack()

    end_page_label = Label(root, text="End Page:")
    end_page_label.pack()
    end_page_entry = Entry(root)
    end_page_entry.pack()

    start_button = Button(root, text="Start Reading", command=start_reading)
    start_button.pack()

    pause_button = Button(root, text="Pause/Resume", command=pause_reading)
    pause_button.pack()

    stop_button = Button(root, text="Stop", command=stop_reading)
    stop_button.pack()

    status_label = Label(root, text="")
    status_label.pack()

    root.mainloop()
