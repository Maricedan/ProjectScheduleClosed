import tkinter as tk
import traceback
import sys
import os
from tkinter import ttk
from tkinter import messagebox
from user_management import UserManagement
from login import LoginWindow, login
from project_list import ProjectList
from project_editor import ProjectEditor
from figure import Figure
from settings import AppSettings
from task_card import TaskCard
from settings import settings
from state_manager import state_manager
from tkinter import simpledialog



class App:
    def __init__(self, root):
        self.root = root
        self.initialize()

    def initialize(self):
        # Inicjalizacja ustawień, sprawdź czy plik users.json istnieje
        self.find_data_file()

    def find_data_file(self):
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'users.json')
        
        # Sprawdzenie czy plik istnieje
        if not os.path.exists(data_path):
            self.show_path_dialog()

    def show_path_dialog(self):
        # Otwórz okno dialogowe, w którym użytkownik może podać ścieżkę
        new_path = simpledialog.askstring("Błąd", "Nie odnaleziono pliku. Podaj ścieżkę do folderu, w którym znajdują się dane.")
        
        # Zapisz nową ścieżkę i ponownie wykonaj metodę find_data_file
        if new_path:
            self.save_path(new_path)
            self.find_data_file()
            
    def save_path(self, raw_path):
        normalized_path = raw_path.replace('\\', '\\\\')
        settings.sciezka_do_danych = normalized_path
        settings.to_json()


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    with open('errors.log', 'a') as f:
        f.write(text)

sys.excepthook = log_uncaught_exceptions



def main():
    root = tk.Tk()
    root.title("Projekty robotyczne")
    root.withdraw()
    
    settings.from_json()  # Odczytuje istniejące ustawienia z pliku JSON przy inicjalizacji
    
    app = App(root)

    main_frame = ttk.Frame(root)
    main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    notebook = ttk.Notebook(main_frame)
    state_manager.set_notebook(notebook)

    user_management_frame = UserManagement(notebook)

    # Tworzenie instancji klasy Figure
    figure = Figure(notebook)
    state_manager.set_figure(figure)

    project_editor_frame = ProjectEditor(notebook, figure)
    
    state_manager.set_project_editor(project_editor_frame)

    project_list_frame = None
    
    task_card = TaskCard(notebook)
    state_manager.set_task_card(task_card)
        

    def on_login(username, password):
        if login(username, password):
            is_admin = username == "admin"

            # I. Sekcja "Mój dzień"
            my_day_frame = ttk.Frame(notebook)
            notebook.add(my_day_frame, text="Mój dzień")  # Dodaj na początku

            # II. Sekcja "Lista projektów" 
            project_list_frame = ProjectList(notebook, is_admin, project_editor_frame)
            notebook.add(project_list_frame, text="Lista projektów")  # Dodaj jako drugą zakładkę
            project_list_frame.load_projects()
            
            state_manager.set_project_list(project_list_frame)

            # III. Sekcja "Edycja projektu"
            notebook.add(project_editor_frame, text="Edycja projektu")  # Dodaj jako trzecią zakładkę
                        
            # IV. Sekcja "Harmonogram projektu"
            notebook.add(figure, text="Harmonogram projektu")

            # Związanie zdarzenia widoczności z odświeżeniem harmonogramu
            figure.bind("<Visibility>", figure.refresh_schedule)
    
            # V. Sekcja "Karta zadania"
            notebook.add(task_card, text="Karta zadania")

            # VI. Sekcja "Statystyki projektu"
            project_stats_frame = ttk.Frame(notebook)
            notebook.add(project_stats_frame, text="Statystyki projektu")

             # VII. Sekcja "Ustawienia aplikacji"
            app_settings_frame = AppSettings(notebook)
            notebook.add(app_settings_frame, text="Ustawienia aplikacji")

            # Jeśli jest adminem, dodaj sekcję zarządzania użytkownikami
            if is_admin:
                notebook.add(user_management_frame, text="Zarządzanie użytkownikami")

            notebook.select(figure)

            root.deiconify()
            login_window.destroy()
        else:
            messagebox.showerror("Błąd logowania", "Nieprawidłowy login lub hasło")

    login_window = LoginWindow(root, on_login)
    login_window.protocol("WM_DELETE_WINDOW", root.destroy)

    notebook.pack(fill=tk.BOTH, expand=True)

    root.geometry("1600x900")

    root.bind('<Control-z>', lambda event: project_editor_frame.undo())

    root.mainloop()

if __name__ == "__main__":
    main()



