import os
import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import pygame
from tkinter import ttk
from tkmacosx import Button
import csv

# Initialize pygame mixer
pygame.mixer.init()

# Database setup
connection = sqlite3.connect("music.db")
cursor = connection.cursor()

# Create tables if not exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS moods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mood_name TEXT UNIQUE NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    mood_id INTEGER,
    FOREIGN KEY (mood_id) REFERENCES moods (id)
)
''')

connection.commit()

# Function to get songs for a mood
def get_songs_for_mood(mood):
    cursor.execute("SELECT name, path FROM songs WHERE mood_id=(SELECT id FROM moods WHERE mood_name=?)", (mood,))
    return cursor.fetchall()

# Function to play a song
def play_song(song_path):
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()

# Function to pause the song
def pause_song():
    pygame.mixer.music.pause()

# Function to unpause the song
def unpause_song():
    pygame.mixer.music.unpause()

    
def Add_song():
    # Create a new window for adding a song
    add_song_window = tk.Toplevel()
    add_song_window.title("Add a New Song")
    add_song_window.geometry("400x400")
    add_song_window.configure(bg="#111c23")
    
    # Labels and Entry for Mood
    mood_label = tk.Label(add_song_window, text="Enter Mood:", font=("Courier", 16), bg="#111c23", fg="#f38375")
    mood_label.pack(pady=10)
    mood_entry = tk.Entry(add_song_window, font=("Courier", 14), width=20, bg="#2a353c", fg="#f38375")
    mood_entry.pack(pady=10)
    
    # Button to select a song
    song_label = tk.Label(add_song_window, text="Selected Song: None", font=("Courier", 12), bg="#111c23", fg="#f38375")
    song_label.pack(pady=10)
    
    def select_song():
        song_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3;*.wav")])
        if song_path:
            song_label.config(text=f"Selected Song: {os.path.basename(song_path)}")
            add_song_window.selected_song_path = song_path  # Store the selected song path
    
    select_song_button = Button(add_song_window, text="Select Song", command=select_song, font=("Courier", 20), height=30, width=200,bg="#2a353c", fg="#f38375", borderless=1)
    select_song_button.pack(pady=10)
    
    # Save the song to the database
    def save_song():
        mood = mood_entry.get().strip()
        song_path = getattr(add_song_window, "selected_song_path", None)
        
        if not mood or not song_path:
            messagebox.showerror("Error", "Please enter a mood and select a song.")
            return
        
        # Insert mood if not exists
        cursor.execute("INSERT OR IGNORE INTO moods (mood_name) VALUES (?)", (mood,))
        connection.commit()
        
        # Get mood_id
        cursor.execute("SELECT id FROM moods WHERE mood_name=?", (mood,))
        mood_id = cursor.fetchone()[0]
        
        # Insert song into the database
        cursor.execute("INSERT INTO songs (name, path, mood_id) VALUES (?, ?, ?)", (os.path.basename(song_path), song_path, mood_id))
        connection.commit()
        
        messagebox.showinfo("Success", f"Song '{os.path.basename(song_path)}' added under mood '{mood}'.")
        add_song_window.destroy()
    
    save_button = Button(add_song_window, text="Save Song", command=save_song, font=("Courier", 14), bg="#2a353c", fg="#f38375", borderless=1)
    save_button.pack(pady=20)


# Function to load questions and mood mapping from a CSV file
def load_quiz_from_csv(csv_file):
    questions = []
    mood_mapping = {}
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                question = row["question"]
                options = row["options"].split("|")
                moods = row["mood_mapping"].split("|")
                questions.append((question, options))
                for option, mood in zip(options, moods):
                    mood_mapping[option] = mood
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load quiz: {e}")
    return questions, mood_mapping

# Function for mood quiz
def mood_quiz():
    csv_file = "/Users/apple/Desktop/CS Project/quiz_questions.csv"  # Path to your CSV file
    questions, mood_mapping = load_quiz_from_csv(csv_file)
    answers = []

    if not questions:
        messagebox.showerror("Error", "No quiz questions available.")
        return

    def submit_answer():
        answer = quiz_var.get()
        if not answer:
            messagebox.showerror("Error", "Please select an option.")
            return
        answers.append(answer)
        next_question()

    def next_question():
        nonlocal question_index
        question_index += 1
        if question_index < len(questions):
            question_label.config(text=questions[question_index][0])
            for i, option in enumerate(questions[question_index][1]):
                quiz_buttons[i].config(text=option, value=option)
        else:
            determine_mood()

    def determine_mood():
        mood_count = {"Happy": 0, "Sad": 0, "Neutral": 0}
        for answer in answers:
            if answer in mood_mapping:
                mood_count[mood_mapping[answer]] += 1
        user_mood = max(mood_count, key=mood_count.get)
        quiz_window.destroy()
        load_playlist(user_mood)

    quiz_window = tk.Toplevel()
    quiz_window.title("Mood Quiz")
    quiz_window.geometry("800x400")
    quiz_window.configure(bg="#111c23")

    question_index = -1
    quiz_var = tk.StringVar(value="")

    question_label = tk.Label(quiz_window, text="", font=("Courier", 20), bg="#111c23", fg="#f38375")
    question_label.pack(pady=20)

    quiz_buttons = []
    for _ in range(3):
        button = tk.Radiobutton(
            quiz_window, text="", font=("Courier", 18), variable=quiz_var, value="", indicatoron=0,width=40,bg="#2a353c", fg="#f38375"
        )
        button.pack(pady=10)
        quiz_buttons.append(button)

    next_question()

    submit_button = Button(quiz_window, text="Submit", font=("Courier",18),command=submit_answer, width=200,bg="#2a353c", fg="#f38375", borderless=1)
    submit_button.pack(pady=20)

def load_playlist(mood):
    songs = get_songs_for_mood(mood)
    if songs:
        player_window = tk.Toplevel()
        player_window.title(f"Music Player - {mood} Mood")
        player_window.geometry("920x200")
        player_window.configure(bg="#111c23")

        song_frame = tk.LabelFrame(player_window, text="Playlist", relief="solid", bd=1,  font=("Courier", 10, "bold"), bg="#0c161e",fg="#f698b1")
        song_frame.grid(row=0, column=0, rowspan=2, padx=20, pady=10, sticky="nsew")

        song_box = tk.Listbox(song_frame,bg="#2a353c", fg="#f38375", width=40, height=8,  font=("Courier", 14))
        song_box.grid(row=0, column=0, padx=5, pady=(10,5))

        scrollbar = tk.Scrollbar(song_frame, orient=tk.VERTICAL, command=song_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        song_box.config(yscrollcommand=scrollbar.set)

        for song in songs:
            song_box.insert(tk.END, song[0])

        progress = tk.DoubleVar()

        def update_progress_bar(song_duration):
            current_time = pygame.mixer.music.get_pos() / 1000  # Current time in seconds
            if current_time < song_duration:
                progress.set((current_time / song_duration) * 100)
                progress_bar.after(500, update_progress_bar, song_duration)
            else:
                progress.set(100)
                song_label.config(text="Currently Playing: ")

        def play_selected_song():
            selected_song = song_box.get(tk.ACTIVE)
            song_path = next(song[1] for song in songs if song[0] == selected_song)
            play_song(song_path)
            song_label.config(text=f"Currently Playing: {selected_song}")
            song = pygame.mixer.Sound(song_path)
            song_duration = song.get_length()
            update_progress_bar(song_duration)

        def stop_and_exit():
            pygame.mixer.music.stop()
            player_window.destroy()

        def pause_song_button():
            pause_song()

        def unpause_song_button():
            unpause_song()

        currently_playing_frame = tk.LabelFrame(
            player_window, text="Current Song", relief="solid", bd=1, font=("Courier", 10, "bold"), bg="#0c161e",fg="#f698b1"
        )
        currently_playing_frame.grid(row=0, column=1, padx=(0, 20), pady=(10, 5), sticky="nsew")

        song_label = tk.Label(currently_playing_frame, text="Currently Playing: ", font=("Courier", 16), width=40, anchor="w", bg="#0c161e", fg="#f38375")
        song_label.grid(row=0, column=0, padx=10, pady=5)

        style = ttk.Style()
        style .theme_use('clam')
        style.configure("TProgressbar", thickness=40,background='#f698b1', troughcolor='#282A36')

        progress_bar = ttk.Progressbar(currently_playing_frame, variable=progress, maximum=100, length=380, style="TProgressbar")
        progress_bar.grid(row=1, column=0, padx=10, pady=5)

        controls_frame = tk.LabelFrame(player_window, text="Control Buttons", relief="solid", bd=1, font=("Courier", 10, "bold"), bg="#0c161e",fg="#f698b1")
        controls_frame.grid(row=1, column=1, padx=(0, 20), pady=(5, 10), sticky="nsew")

        play_btn = Button(controls_frame, text="Play", command=play_selected_song, font=("Courier", 16), bg="#2a353c", fg="#f38375", borderless=1)
        stop_btn = Button(controls_frame, text="Stop", command=stop_and_exit, font=("Courier", 16), bg="#2a353c", fg="#f38375", borderless=1)
        pause_btn = Button(controls_frame, text="Pause", command=pause_song_button, font=("Courier", 16),bg="#2a353c", fg="#f38375", borderless=1)
        unpause_btn = Button(controls_frame, text="Unpause", command=unpause_song_button, font=("Courier", 16), bg="#2a353c", fg="#f38375", borderless=1)
        
        
        play_btn.grid(row=0, column=0, padx=5, pady=5)
        stop_btn.grid(row=0, column=1, padx=5, pady=5)
        pause_btn.grid(row=0, column=2, padx=5, pady=5)
        unpause_btn.grid(row=0, column=3, padx=5, pady=5)

    else:
        messagebox.showinfo("No Songs", f"No songs found for mood '{mood}'.")


# Main GUI setup
window = tk.Tk()
window.title("Mood-Based Music Player")
window.geometry("500x400")
window.configure(bg="#111c23")

welcome_label = tk.Label(window, text="Mood-Based Music Player", font=("Courier", 28), bg="#111c23", fg="#f38375")
welcome_label.pack(pady=20)

quiz_button = Button(window, text="Take Mood Quiz", command=mood_quiz, font=("Courier", 20), bg="#2a353c", fg="#f38375", borderless=1)
quiz_button.pack(pady=20)

Add_song_button=Button(window, text="Add Song", command=Add_song, font=("Courier",20 ),bg="#2a353c", fg="#f38375", borderless=1)
Add_song_button.pack(pady=20)

exit_button =Button(window, text="Exit", command=window.destroy, font=("Courier", 20), bg="#2a353c", fg="#f38375", borderless=1)
exit_button.pack(pady=20)


window.mainloop()

# Close database connection
connection.close()