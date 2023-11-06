import tkinter as tk
import os
import json
from tkinter import ttk
from settings import settings


class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_login_callback):
        super().__init__(parent)
        self.title("Logowanie")
        self.on_login_callback = on_login_callback

        username_label = ttk.Label(self, text="Login:")
        username_label.grid(row=0, column=0)
        self.username_entry = ttk.Entry(self)
        self.username_entry.grid(row=0, column=1)

        password_label = ttk.Label(self, text="Hasło:")
        password_label.grid(row=1, column=0)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1)

        login_button = ttk.Button(self, text="Zaloguj", command=self.on_login)
        login_button.grid(row=2, column=0, columnspan=2)

        # Ustawienie fokusu na polu wprowadzania nazwy użytkownika
        self.username_entry.focus_set()

        # Dodanie wiązania do okna, które wywołuje funkcję on_login, gdy naciśnięty zostanie klawisz Enter
        self.bind("<Return>", self.on_login)

         # dodanie domyślnych danych logowania
        self.username_entry.insert(0, 'admin')
        self.password_entry.insert(0, '1')
        self.after(100, self.on_login)  # automatyczne logowanie po 1 sekundzie

    def on_login(self, event=None):
        self.on_login_callback(self.username_entry.get(), self.password_entry.get())


def login(username, password):
    default_users = {"admin": "1", "user": "2"}
    data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
    data_path = os.path.join(data_folder_path, 'users.json')

    try:
        if not os.path.exists(data_folder_path):
            os.makedirs(data_folder_path)
        with open(data_path, 'r') as file:
            users = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        users = default_users
                
    users.update(default_users)

    return users.get(username) == password