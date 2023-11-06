import tkinter as tk
import json
import os
from tkinter import ttk
from state_manager import state_manager
from settings import settings


class UserManagement(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.widget_refs = {}
        self.users = self.load_users()

        self.create_widgets()

    def create_widgets(self):
        # Kod tworzenia widżetów przeniesiony z funkcji main()
        self.user_management_frame = ttk.Frame(self)

        self.add_user_button = tk.Button(self.user_management_frame, text="Dodaj użytkownika", command=self.add_user)
        self.add_user_button.pack()

        self.remove_user_button = tk.Button(self.user_management_frame, text="Usuń użytkownika", command=self.remove_user)
        self.remove_user_button.pack()

        self.user_label = tk.Label(self.user_management_frame, text="Użytkownik:")
        self.user_label.pack()
        self.user_entry = tk.Entry(self.user_management_frame)
        self.user_entry.pack()

        self.password_label = tk.Label(self.user_management_frame, text="Hasło:")
        self.password_label.pack()
        self.password_entry = tk.Entry(self.user_management_frame, show="*")
        self.password_entry.pack()

        self.users_listbox_label = tk.Label(self.user_management_frame, text="Lista użytkowników:")
        self.users_listbox_label.pack()
        self.users_listbox = tk.Listbox(self.user_management_frame)
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        self.update_users_listbox()

        self.user_management_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)  # Dodano tę linię
        
    def add_user(self):
        # Kod dodawania użytkownika
        user = self.user_entry.get()
        password = self.password_entry.get()
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'users.json')

        if user and password:
            self.users[user] = password
            self.update_users_listbox()
            self.save_users()
            project_editor_frame = state_manager.get_project_editor()
            project_editor_frame.users = project_editor_frame.load_users(data_path) 

    def remove_user(self):
        # Kod usuwania użytkownika
        selection = self.users_listbox.curselection()
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'users.json')

        if selection:
            selected_user = self.users_listbox.get(selection)
            if selected_user:
                del self.users[selected_user]
                self.update_users_listbox()
                self.save_users()
                project_editor_frame = state_manager.get_project_editor()
                project_editor_frame.users = project_editor_frame.load_users(data_path) 

    def update_users_listbox(self):
        # Kod aktualizacji listy użytkowników
        self.users_listbox.delete(0, tk.END)
        for user in self.users:
            self.users_listbox.insert(tk.END, user)

    def save_users(self):
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'users.json')
        if not os.path.exists(data_folder_path):
            os.makedirs(data_folder_path)
        with open(data_path, 'w') as file:
            json.dump(self.users, file)

    def load_users(self):
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'users.json')
        try:
            with open(data_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}


