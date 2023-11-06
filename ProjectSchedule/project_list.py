import tkinter as tk
import os
import json
from tkinter import ttk
from tkinter.simpledialog import askstring
from tkinter import messagebox
from project import Project
from settings import settings


class ProjectList(ttk.Frame):
    def __init__(self, parent, is_admin=False, project_editor=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.project_editor = project_editor
        self.is_admin = is_admin
        self.projects = []
        self.active_project = None
        self.create_widgets()

    def create_widgets(self):
        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(side=tk.TOP, fill=tk.X)

        if self.is_admin:
            self.add_project_button = ttk.Button(self.controls_frame, text="Dodaj projekt", command=self.add_project)
            self.add_project_button.pack(side=tk.LEFT, padx=(10, 5), pady=10)

            self.remove_project_button = ttk.Button(self.controls_frame, text="Usuń projekt", command=self.remove_project)
            self.remove_project_button.pack(side=tk.LEFT, padx=(5, 10), pady=10)

        self.projects_listbox = tk.Listbox(self)
        self.projects_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Przypisujemy funkcję handle_project_selection do zdarzenia <<ListboxSelect>>
        self.projects_listbox.bind('<<ListboxSelect>>', self.handle_project_selection)

        self.selected_project_label = ttk.Label(self.controls_frame, text="")
        self.selected_project_label.pack(side=tk.LEFT, padx=(10, 5), pady=10)
        
        self.select_project_button = ttk.Button(self.controls_frame, text="Wybierz projekt", command=self.select_project)
        self.select_project_button.pack(side=tk.LEFT, padx=(5, 10), pady=10)
                                
    def add_project(self):
        project_number = askstring("Nowy projekt", "Wprowadź numer projektu (max 7 cyfr):", parent=self)
        if project_number is None or len(project_number) > 7 or not project_number.isdigit():
            messagebox.showerror("Błąd", "Wprowadź poprawny numer projektu (max 7 cyfr).")
            return

        project_title = askstring("Nowy projekt", "Wprowadź tytuł projektu:", parent=self)
        if project_title is None or project_title == "":
            messagebox.showerror("Błąd", "Wprowadź poprawny tytuł projektu.")
            return

        project_description = askstring("Nowy projekt", "Wprowadź opis projektu:", parent=self)
        if project_description is None or project_description == "":
            messagebox.showerror("Błąd", "Wprowadź poprawny opis projektu.")
            return

        project_status = ["Nieaktywny", "W realizacji", "Zakończony", "Zamknięty"]
        status_dialog_window = tk.Toplevel(self)
        status_dialog_window.title("Wybierz status projektu")
        status_dialog = ttk.Combobox(status_dialog_window, values=project_status, state="readonly")
        status_dialog.set(project_status[0])
        status_dialog.pack(padx=10, pady=10)

        def on_status_dialog_ok():
            nonlocal project_status
            project_status = status_dialog.get()
            status_dialog_window.destroy()

        status_dialog_button = ttk.Button(status_dialog_window, text="OK", command=on_status_dialog_ok)
        status_dialog_button.pack(padx=10, pady=10)
        self.wait_window(status_dialog_window)

        project = Project(project_number, project_title, project_status, project_description)
        self.projects.append(project)
        self.update_projects_listbox()
        self.save_projects() 

    def handle_project_selection(self, event):
        # Tu obsługujemy zdarzenie wyboru projektu z listy
        selection = self.projects_listbox.curselection()
        if selection:
            self.active_project = self.projects[selection[0]]
            self.selected_project_label.config(text=f"Wybrany projekt: {self.active_project.id} - {self.active_project.title}")
            self.save_active_project()

            if self.project_editor:
                self.project_editor.load_project(self.active_project)
                    
    def select_project(self, event=None):
        selection = self.projects_listbox.curselection()
        if selection:
            self.active_project = self.projects[selection[0]]
            self.selected_project_label.config(text=f"Wybrany projekt: {self.active_project.id} - {self.active_project.title}")
            self.save_active_project()

            if self.project_editor:
                self.project_editor.load_project(self.active_project)

    def highlight_project(self, _=None):
        selection = self.projects_listbox.curselection()
        if selection:
            project = self.projects[selection[0]]

    def save_active_project(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        if self.active_project is not None:
            with open('active_project.txt', 'w') as f:
                f.write(self.active_project.id)
        
    def load_active_project(self):
        try:
            with open('active_project.txt', 'r') as f:
                active_project_id = f.read()
                for i, project in enumerate(self.projects):
                    if project.id == active_project_id:
                        self.active_project = project
                        self.selected_project_label.config(text=f"Wybrany projekt: {self.active_project.id} - {self.active_project.title}")
                        self.projects_listbox.selection_set(i)  # Dodane: zaznacz odpowiedni projekt
                        self.select_project()  # Dodane: wywołaj select_project
                        break
        except FileNotFoundError:
            pass

    def remove_project(self):
        # Funkcja usuwania wybranego projektu
        selection = self.projects_listbox.curselection()
        if selection:
            confirm = messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć wybrany projekt?")
            if confirm:
                self.projects_listbox.delete(selection)
                del self.projects[selection[0]]
                self.save_projects()

    def load_projects(self):
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'projects.json')
    
        try:
            with open(data_path, 'r') as f:
                projects_data = json.load(f)

            for project_data in projects_data:
                project = Project(
                    project_data['id'],
                    project_data['title'],
                    project_data['status'],
                    project_data['description']
                )
                self.projects.append(project)

            self.update_projects_listbox()
            self.load_active_project()
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def update_projects_listbox(self):
        self.projects_listbox.delete(0, tk.END)
        for project in self.projects:
            self.projects_listbox.insert(tk.END, f"{project.id} - {project.status} - {project.title} - {project.description}")
            self.projects_listbox.bind('<<ListboxSelect>>', self.highlight_project)
            
    def save_projects(self):
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'projects.json')
    
        projects_data = []
        for project in self.projects:
            projects_data.append(project.to_dict())
        
        try:
            if not os.path.exists(data_folder_path):
                os.makedirs(data_folder_path)
            with open(data_path, 'w') as f:
                json.dump(projects_data, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass