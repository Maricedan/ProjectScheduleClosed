import tkinter as tk
import os
from tkinter import ttk
from state_manager import state_manager




class TaskCard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Górna ramka dla etykiety i przycisku "Odśwież"
        self.top_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.refresh_button = ttk.Button(self.top_frame, text="Odśwież", command=self.populate_file_list)
        self.refresh_button.pack(side=tk.LEFT)
        
        self.label_var = tk.StringVar()
        self.label_var.set("")
        self.info_label = ttk.Label(self.top_frame, textvariable=self.label_var)
        self.info_label.pack(side=tk.LEFT)
                
        # Ramka dla przycisków i listy plików
        self.right_frame = ttk.Frame(self, padding=(10, 10, 10, 10))
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(self.right_frame)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        
        self.controls_frame = ttk.Frame(self.right_frame)
        self.controls_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))
        
        self.load_button = ttk.Button(self.controls_frame, text="Wczytaj", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.add_button = ttk.Button(self.controls_frame, text="Dodaj", command=self.add_file)
        self.add_button.pack(side=tk.LEFT, padx=(5, 5))
        
        self.remove_button = ttk.Button(self.controls_frame, text="Usuń", command=self.remove_file)
        self.remove_button.pack(side=tk.LEFT, padx=(5, 0))

        # Ramka dla edytora tekstu
        self.left_frame = ttk.Frame(self, padding=(10, 10, 0, 10))
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.text_editor = tk.Text(self.left_frame)
        self.text_editor.pack(fill=tk.BOTH, expand=True)

    def populate_file_list(self, task_folder):
        """Wypełnia listę plików z folderu zadania."""
        self.file_listbox.delete(0, tk.END)  # Usuwanie wszystkich elementów z listboxa
        if os.path.exists(task_folder):
            files = os.listdir(task_folder)
            for file in files:
                self.file_listbox.insert(tk.END, file)

    def update_label(self, info_dict):
        new_label = f"Numer projektu: {info_dict['project_number']}, Ścieżka: {info_dict['path_in_tree']}, Zadanie: {info_dict['task_name']}"
        self.label_var.set(new_label)

    def load_file(self):
        """Wczytuje zaznaczony plik do edytora tekstu."""
        pass  # Kod do implementacji
        
    def add_file(self):
        """Dodaje nowy plik."""
        pass  # Kod do implementacji
    
    def remove_file(self):
        """Usuwa zaznaczony plik."""
        pass  # Kod do implementacji


