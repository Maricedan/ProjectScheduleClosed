import tkinter as tk
import json
import os
import uuid  # biblioteka uuid do generowania unikalnych identyfikatorów
import copy
import holidays
from tkinter import ttk
from tkinter import messagebox
from tkinter import PhotoImage
from tkinter import Toplevel
from tkinter import TclError
from tkinter.simpledialog import Dialog
from tkcalendar import DateEntry
from tkcalendar import Calendar
from datetime import datetime, timedelta
from state_manager import state_manager
from settings import settings




class UserDialog(Toplevel):
    def __init__(self, parent, users, x=0, y=0):
        Toplevel.__init__(self, parent)
        self.geometry(f"+{x-150}+{y-50}")  # Ustawia okno na pozycji kursora myszy
        self.parent = parent
        self.title("Wybierz użytkownika")

        self.user_combobox = ttk.Combobox(self, values=users)
        self.user_combobox.pack(padx=10, pady=10)

        ttk.Button(self, text="OK", command=self.ok).pack(pady=10)
        
        self.bind('<Return>', self.ok)  # Powiązanie klawisza Enter z metodą ok

        self.result = None
        self.wait_window()

    def ok(self, event=None):  # Dodanie argumentu event, który jest opcjonalny
        self.result = self.user_combobox.get()
        self.destroy()
        self.parent.save_to_json()  # Zapisz dane do pliku JSON



class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, initial_date=None, x=0, y=0):
        super().__init__(parent)
        self.parent = parent
        self.geometry(f"+{x}+{y}")
        self.result = None

        if initial_date:
            year, month, day = initial_date.year, initial_date.month, initial_date.day
            self.calendar = Calendar(self, year=year, month=month, day=day)
        else:
            self.calendar = Calendar(self)

        self.calendar.pack(padx=10, pady=10)
        ttk.Button(self, text="OK", command=self.ok).pack(pady=10)
        self.wait_window()


    def ok(self):
        self.result = self.calendar.selection_get()
        self.destroy()
        self.parent.save_to_json()  # Zapisz dane do pliku JSON



class DurationDialog(Dialog):
    def body(self, master):
        self.title("Podaj liczbę dni")
        self.duration = tk.IntVar(value=1)
        label = tk.Label(master, text="Liczba dni:")
        label.pack()
        validate_command = master.register(self.validate_input) # Rejestracja funkcji walidującej
        entry = tk.Entry(master, textvariable=self.duration, validate="key", validatecommand=(validate_command, '%P'))
        entry.pack()
        entry.after(1, lambda: entry.focus_set()) # Ustawienie fokusu
        entry.after(1, lambda: entry.select_range(0, 'end')) # Zaznaczenie całego tekstu

    def validate_input(self, value):
        if value == "": # Pozwolenie na pusty ciąg znaków, aby można było usunąć wartość
            return True
        try:
            int(value) # Sprawdzenie, czy wartość jest liczbą całkowitą
            return True
        except ValueError:
            return False

    def apply(self):
        self.result = self.duration.get()



class ProjectEditor(ttk.Frame):
    def __init__(self, parent, figure, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.project = None
        
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'users.json')
        self.users = self.load_users(data_path)

        # Załadowanie obrazów
        self.project_icon = PhotoImage(file='project.gif').subsample(120, 120)
        self.section_icon = PhotoImage(file='section.gif').subsample(120, 120)
        self.subsection_icon = PhotoImage(file='subsection.gif').subsample(120, 120)
        self.task_icon = PhotoImage(file='task.gif').subsample(120, 120)
        
        self.project_id = None

        self.create_widgets()

        # Słownik, który mapuje item_id do pełnego tekstu
        self.full_texts = {}

        # Dodajemy schowek jako atrybut klasy
        self.clipboard = None

        # Historia zmian
        self.history = []

        self.figure = figure

    def load_users(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return list(data.keys())  # Zwraca listę nazw użytkowników


    # Przechowujemy dodatkowe kolumny jako słownik
    COLUMN_NAMES = {
        "description": "Opis",
        "dependency_name": "Zależność",
        "start_date": "Data rozpoczęcia",
        "duration": "Czas trwania",
        "end_date": "Data zakończenia",
        "status": "Status",
        "comments": "Komentarze",
        "user": "Użytkownik",
        "dependency": "Zależność",
        "item_type": "Typ"
    }

    def save_to_json(self, filename=None):
        tree = {}
        for item_id in self.tree.get_children():
            tree[item_id] = self.get_tree_data(item_id)

        if self.project is not None:
            data_folder_path = os.path.join(settings.sciezka_do_danych, 'data', 'projects')
            if filename is None:
                # Jeśli nazwa pliku nie jest podana, użyj id projektu
                if not os.path.exists(data_folder_path):
                    os.makedirs(data_folder_path)
                filename = os.path.join(data_folder_path, f'project_{self.project.id}.json')
        
            with open(filename, 'w') as f:
                json.dump(tree, f)
        else:
            print("Nie wybrano żadnego projektu, nie można zapisać do pliku JSON.")


    def get_tree_data(self, item_id):
        data = {
            'text': self.tree.item(item_id, 'text').strip(),
            'values': dict(zip(self.COLUMN_NAMES.keys(), self.tree.item(item_id, 'values'))),
            'children': {},
        }
        for child_id in self.tree.get_children(item_id):
            data['children'][child_id] = self.get_tree_data(child_id)
        return data
    

    def get_item_type(self, item_id):
        item_data = self.get_tree_data(item_id)
        return item_data['values'].get('item_type', None)


    def focus_on_tree_item(self, unique_id):
        # Czyścimy obecną selekcję
        self.tree.selection_remove(self.tree.selection())

        # Ustawiamy nową selekcję
        self.tree.selection_set(unique_id)

        # Make the item visible
        self.tree.see(unique_id)

        # Open all parent nodes to make sure the item is visible
        parent = self.tree.parent(unique_id)
        while parent:
            self.tree.item(parent, open=True)
            parent = self.tree.parent(parent)


    def create_widgets(self):
        # Tworzenie ramki, żeby przycisk i etykieta były obok siebie
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X)

        # Przycisk odświeżania
        refresh_button = ttk.Button(top_frame, text="Odśwież", command=self.refresh_project_tree)
        refresh_button.pack(side=tk.LEFT, padx=10, pady = 10)

        self.title_label = ttk.Label(top_frame, text="Brak wybranego projektu")
        self.title_label.pack(side=tk.LEFT)
        
        # Dodawanie przycisków rozwijania
        expand_1_button = ttk.Button(top_frame, text="Rozwiń poziom 1", command=lambda: self.expand_tree(1))
        expand_1_button.pack(side=tk.LEFT, padx=10)
        expand_2_button = ttk.Button(top_frame, text="Rozwiń poziom 2", command=lambda: self.expand_tree(2))
        expand_2_button.pack(side=tk.LEFT, padx=10)
        expand_all_button = ttk.Button(top_frame, text="Rozwiń wszystko", command=lambda: self.expand_tree('all'))
        expand_all_button.pack(side=tk.LEFT, padx=10)

        # Dodawanie widoku drzewa do prezentacji projektu
        self.tree = ttk.Treeview(self, style="Section.Treeview")
        self.tree.pack(fill=tk.BOTH, expand=1, padx=10)
        self.tree['columns'] = ('description')
        self.tree.column('#0', width=120, minwidth=50)
        self.tree.column('description', anchor=tk.W, width=200)
        self.tree.heading('#0', text='Nazwa', anchor=tk.W)
        self.tree.heading('description', text='Opis', anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=1)
        
        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='white')

        # Obsługa zdarzenia podwójnego kliknięcia
        self.tree.bind("<Double-1>", self.on_double_click)

        # Dodawanie pól do wprowadzania nazwy i opisu
        ttk.Label(self, text="Nazwa:").pack(anchor=tk.W, padx=10)
        self.name_entry = ttk.Entry(self)
        self.name_entry.pack(fill=tk.X, padx=10, pady=(0, 5))
        ttk.Label(self, text="Opis:").pack(anchor=tk.W, padx=10)
        self.description_entry = ttk.Entry(self)
        self.description_entry.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Tworzenie legendy
        self.create_legend()
        
        # Tworzenie ramki na dolnej części interfejsu
        bottom_frame = ttk.Frame(self)
        
        # Dodawanie przycisków do dodawania sekcji, podsekcji i zadań
        button_frame = ttk.Frame(bottom_frame)
        self.add_section_button = ttk.Button(button_frame, text="Dodaj sekcję", command=self.add_section)
        self.add_section_button.pack(side=tk.LEFT, padx=5)
        self.add_subsection_button = ttk.Button(button_frame, text="Dodaj podsekcję", command=self.add_subsection)
        self.add_subsection_button.pack(side=tk.LEFT, padx=5)
        self.add_task_button = ttk.Button(button_frame, text="Dodaj zadanie", command=self.add_task)
        self.add_task_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(button_frame, text="Usuń", command=self.delete_item)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.copy_button = ttk.Button(button_frame, text="Kopiuj", command=self.copy_item)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.paste_button = ttk.Button(button_frame, text="Wklej", command=self.paste_item)
        self.paste_button.pack(side=tk.LEFT, padx=5)

        button_frame.pack(side=tk.LEFT, padx=10)

        # Dodawanie pól do wprowadzania daty rozpoczęcia i zakończenia
        date_frame = ttk.Frame(bottom_frame)
        self.start_date_entry = DateEntry(date_frame)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)

        # Użytkownicy
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data')
        data_path = os.path.join(data_folder_path, 'users.json')
        self.user_combobox = ttk.Combobox(date_frame, values=self.users)
        self.user_combobox.pack(side=tk.LEFT, padx=5)

        date_frame.pack(side=tk.LEFT, padx=10)
                
        # Wyśrodkowanie ramki bottom_frame względem nadrzędnego widgetu
        bottom_frame.pack(side=tk.BOTTOM, pady=10)
        
        # Tworzymy nowy zestaw kolumn, pomijając 'item_type'
        display_columns = [col for col in self.COLUMN_NAMES.keys() if col != 'item_type' and col != 'dependency']

        # Konfiguracja widoku drzewa: ustawienie kolumn, ich szerokości, minimalnej szerokości i wyrównania,
        # oraz przypisanie odpowiednich nagłówków dla kolumn
        self.tree['columns'] = tuple(display_columns)  # Zamiast self.COLUMN_NAMES.keys()
        self.tree.column('#0', width=630, minwidth=50)
        for column in display_columns:  # Zamiast self.COLUMN_NAMES.keys()
            self.tree.column(column, anchor=tk.W, width=90)
        self.tree.heading('#0', text='Nazwa', anchor=tk.W)
        for column in display_columns:  # Zamiast self.COLUMN_NAMES.items()
            self.tree.heading(column, text=self.COLUMN_NAMES[column], anchor=tk.W)
            

    def expand_tree(self, level):
        def _expand_children(item, current_level):
            if level == 'all' or current_level < level:
                children = self.tree.get_children(item)
                self.tree.tag_configure('oddrow', background='#F0F8FF')
                for child in children:
                    self.tree.item(child, open=True)
                    _expand_children(child, current_level + 1)
            elif current_level >= level:                
                self.tree.tag_configure('oddrow', background='white')
                children = self.tree.get_children(item)
                for child in children:
                    self.tree.item(child, open=False)
                
        root = ''
        _expand_children(root, 0)
            

    def create_legend(self):
        # Tworzenie ramki na legendę
        self.legend_frame = ttk.Frame(self)
        self.legend_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        # Tworzenie etykiet dla każdej z ikon
        self.project_legend = ttk.Label(self.legend_frame, image=self.project_icon, text="Projekt", compound=tk.LEFT)
        self.project_legend.pack(side=tk.LEFT, padx=(0, 10))

        self.section_legend = ttk.Label(self.legend_frame, image=self.section_icon, text="Sekcja", compound=tk.LEFT)
        self.section_legend.pack(side=tk.LEFT, padx=(0, 10))

        self.subsection_legend = ttk.Label(self.legend_frame, image=self.subsection_icon, text="Podsekcja", compound=tk.LEFT)
        self.subsection_legend.pack(side=tk.LEFT, padx=(0, 10))

        self.task_legend = ttk.Label(self.legend_frame, image=self.task_icon, text="Zadanie", compound=tk.LEFT)
        self.task_legend.pack(side=tk.LEFT, padx=(0, 10))
        
        
    def get_expanded_items(self, parent=''):
        if not hasattr(self, 'tree'):
            return []
        
        expanded = []
        children = self.tree.get_children(parent)
        for child in children:
            if self.tree.item(child, 'open'):
                expanded.append(child)
                expanded += self.get_expanded_items(child)
        return expanded
    

    def set_expanded_items(self, items):
        if not hasattr(self, 'tree') or not items:
            return

        for item in items:
            try:
                self.tree.item(item, open=True)
            except tk.TclError:  # Element może nie istnieć
                continue

            
    def save_state(self):
        state = self.tree.get_children('')
        self.history.append(state) # funkcja na razie nie aktywna


    def undo(self): # funkcja na razie nie aktywna
        previous_state = self.history.pop()


    def generate_values(self, data):
        return (data.get('description', ''), data.get('dependency_name', ''),
                data.get('start_date', ''), data.get('duration', ''),
                data.get('end_date', ''), data.get('status', ''),
                data.get('comments', ''), data.get('user', ''),
                data.get('dependency', ''),
                data.get('item_type', ''))
    

    def load_project(self, project):
        # Zapisz rozwinięte elementy
        expanded_items = self.get_expanded_items()
        
        # Usuń wszystkie istniejące elementy z drzewa
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.project = project
        self.title_label.config(text=f"Edycja projektu: {project.id} - {project.title}")

        self.figure.set_project_id(project.id)
        
        self.project_id = project.id
    
        # Sprawdź, czy projekt jest już załadowany do drzewa
        if not self.tree.exists(project.id):
            self.tree.insert("", "end", iid=project.id, text="  "+project.title, values=(project.description,), image=self.project_icon)
            self.add_section_button.config(state="normal")

            data_folder_path = os.path.join(settings.sciezka_do_danych, 'data', 'projects')
            data_path = os.path.join(data_folder_path, f'project_{project.id}.json')

            self.row_count = [0]
    
            try:
                # Próba wczytania danych z pliku
                with open(data_path, 'r') as f:
                    data = json.load(f)
                self.insert_data_into_tree("", data)  # Wczytanie danych do drzewa
            except FileNotFoundError:
                # Jeżeli plik nie istnieje, to prawdopodobnie projekt nie ma jeszcze żadnych sekcji
                pass
            
        # Przywróć rozwinięte elementy
        self.set_expanded_items(expanded_items)


    def insert_data_into_tree(self, parent, tree_data, row_count=[0]):
        image = None  # Set default value for image
                      
        for item_id, item_data in tree_data.items():
            item_type = item_data['values'].get('item_type', '')  # Get the item type

            # Determine the icon based on item type
            if parent == "":
                image = self.project_icon
            elif item_type == 'section':
                image = self.section_icon
            elif item_type == 'subsection':
                image = self.subsection_icon
            elif item_type == 'task':
                image = self.task_icon
            else:
                image = self.project_icon

            # Check if the item with this ID already exists
            if not self.tree.exists(item_id):
                tag = 'oddrow' if self.row_count[0] % 2 == 0 else 'evenrow'
                # Insert the item into the tree
                self.tree.insert(parent, "end", iid=item_id, text="  "+item_data['text'], 
                                 values=self.generate_values(item_data['values']), image=image, tags=(tag,))

                self.row_count[0] += 1  # Update the row counter

            # Add children of the item to the tree (if they exist)
            if 'children' in item_data:
                self.insert_data_into_tree(item_id, item_data['children'], row_count)
        
        
    def add_section(self):
        name = self.name_entry.get()
        description = self.description_entry.get()
        data = {"description": description,
                "start_date": "", 
                "end_date": "", 
                "status": "", 
                "comments": "",
                "item_type": "section"}
    
        selection = self.tree.selection()  # Dodajemy to, aby określić obecnie wybrany element
        
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)
        
        if selection:  # Upewniamy się, że jakiś element jest wybrany
            project = selection[0]  # Przypisujemy wybrany element do zmiennej "project"
            # Generujemy unikalny identyfikator dla nowo dodawanego elementu
            unique_id = str(uuid.uuid4())  
            self.tree.insert(project, "end", iid=unique_id, text="  "+name, values=self.generate_values(data), image=self.section_icon)
            self.add_subsection_button.config(state="normal")
            self.tree.item(project, open=True)  # Rozwiń projekt
        else:
            messagebox.showerror("Błąd", "Nie wybrano żadnego projektu.") 
                
        self.save_to_json()  # Zapisz dane do pliku JSON po dodaniu sekcji


    def add_subsection(self):
        name = self.name_entry.get()
        description = self.description_entry.get()
        data = {"description": description,
                "start_date": "", 
                "end_date": "", 
                "status": "", 
                "comments": "",
                "item_type": "subsection"}
        selection = self.tree.selection()
        
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)

        if selection:  
            section = selection[0]
            unique_id = str(uuid.uuid4())
            self.tree.insert(section, "end", iid=unique_id, text="  "+name, values=self.generate_values(data), tags=('subsection',), image=self.subsection_icon)
            self.add_task_button.config(state="normal")
            self.tree.item(section, open=True)  # Rozwiń sekcję
        else:
            messagebox.showerror("Błąd", "Nie wybrano żadnej sekcji.")
                    
        self.save_to_json()  # Zapisz dane do pliku JSON po dodaniu podsekcji


    def get_full_path(self, item_id):
        path_parts = []
        while item_id:  # Przechodzenie przez drzewo do korzenia
            item = self.tree.item(item_id)
            path_parts.append(item['text'].strip())
            item_id = self.tree.parent(item_id)
        return ' / '.join(reversed(path_parts))  # Odwrócenie, aby ścieżka była w odpowiedniej kolejności


    def add_task(self):
        # Pobieranie nazwy i opisu z pól wprowadzania
        name = self.name_entry.get()
        description = self.description_entry.get()
        start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')  # Konwersja na łańcuch znaków
        end_date = (self.start_date_entry.get_date() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Pobieranie aktualnie wybranej podsekcji
        selection = self.tree.selection()
        
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)

        # Pobieranie aktualnie wybranego użytkownika
        user = self.user_combobox.get()

        if selection:  # Sprawdzenie, czy istnieje zaznaczenie
            subsection = selection[0]

            # Tworzenie unikalnego identyfikatora dla zadania
            unique_id = str(uuid.uuid4())

            # Tworzenie dynamicznej ścieżki dla zadania
            data_folder_path = os.path.join(settings.sciezka_do_danych, 'data', 'projects', str(self.project.id))
            task_path = os.path.join(data_folder_path, str(unique_id))

            # Utworzenie folderu, jeżeli nie istnieje
            os.makedirs(task_path, exist_ok=True)

            # Przygotowanie danych do zapisu
            data = {
                "description": description,
                "start_date": start_date,
                "duration": 1,
                "end_date": end_date,
                "status": "nierozpoczęte",
                "comments": "",
                "user": user,
                "item_type": "task"
            }

            # Zapisywanie ścieżki zadania w pliku JSON
            task_data_path = os.path.join(task_path, f'{unique_id}_basic_data.json')
            with open(task_data_path, 'w') as file:
                full_path_in_tree = self.get_full_path(subsection) + ' / ' + name  # Użycie funkcji get_full_path
                basic_data = {
                    "project_number": self.project.id,
                    "path_in_tree": full_path_in_tree,
                    "task_name": name
                }
                json.dump(basic_data, file)

            # Dodawanie zadania do drzewa
            self.tree.insert(subsection, "end", iid=unique_id, text="  "+name, values=self.generate_values(data), tags=('task',), image=self.task_icon)
            self.tree.item(subsection, open=True)  # Rozwiń podsekcję            
        else:
            messagebox.showerror("Błąd", "Nie wybrano żadnej podsekcji.")

        self.save_to_json()  # Zapisz dane do pliku JSON po dodaniu zadania


    def delete_item(self):
        # Pobieranie aktualnie wybranego elementu
        selection = self.tree.selection()
        
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)

        self.save_state()
    
        if selection:  # Sprawdzenie, czy istnieje zaznaczenie
            item = selection[0]

            # Wyświetlanie okienka dialogowego z pytaniem, czy na pewno chcemy usunąć element
            result = messagebox.askquestion("Usuwanie", f"Czy na pewno chcesz usunąć element {self.tree.item(item, 'text')}?", icon='warning')

            if result == 'yes':  # Jeżeli odpowiedź brzmi tak
                self.tree.delete(item)  # Usuń element
                self.save_to_json()  # Zapisz dane do pliku JSON po usunięciu elementu
        else:
            messagebox.showerror("Błąd", "Nie wybrano żadnego elementu.")


    def copy_item(self):
        # Pobieranie aktualnie wybranego elementu
        selection = self.tree.selection()
        
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)

        if selection:  # Sprawdzenie, czy istnieje zaznaczenie
            item = selection[0]
            self.clipboard = self.get_tree_data(item)  # Kopiowanie danych elementu do schowka
            print("clipboard: ", self.clipboard)
        else:
            messagebox.showerror("Błąd", "Nie wybrano żadnego elementu.")


    def generate_unique_ids(self, item_data):
        unique_id = str(uuid.uuid4())  # Generujemy unikalny identyfikator dla nowego elementu
        new_item_data = copy.deepcopy(item_data)  # Tworzymy kopię danych elementu

        new_children = {}
        for child_id, child_data in new_item_data['children'].items():
            # Generowanie nowych ID dla każdego dziecka, a następnie rekurencyjne wywołanie funkcji
            # dla każdego z dzieci, aby upewnić się, że wszyscy potomkowie mają unikalne ID
            new_child_data = self.generate_unique_ids(child_data)
            new_children.update(new_child_data)

        new_item_data['children'] = new_children
        return {unique_id: new_item_data}
    

    def paste_item(self):
        # Pobieranie aktualnie wybranego elementu
        selection = self.tree.selection()
        
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)

        if selection:  # Sprawdzenie, czy istnieje zaznaczenie
            parent = selection[0]
            if self.clipboard is not None:  # Sprawdzanie, czy coś jest w schowku
                # Generujemy unikalne identyfikatory dla skopiowanych danych
                unique_data = self.generate_unique_ids(self.clipboard)
                # Wstawiamy skopiowane dane do drzewa jako dzieci obecnie wybranego elementu
                self.insert_data_into_tree(parent, unique_data)
                self.save_to_json()  # Zapisz dane do pliku JSON po wklejeniu elementu
        else:
            messagebox.showerror("Błąd", "Nie wybrano żadnego elementu.")

            
    def on_double_click(self, event):
        # Pobranie ID elementu i kolumny, na którym nastąpiło podwójne kliknięcie
        item_id = self.tree.identify('item', event.x, event.y)
        column = self.tree.identify_column(event.x)

        # Sprawdzanie, czy podwójne kliknięcie nie nastąpiło na kolumnie nazwy
        if column != '#0' and item_id:
            item_values = self.tree.item(item_id, 'values')
            if item_values:
                column_index = int(column[1:]) - 1
                column_keys = list(self.COLUMN_NAMES.keys())
                if column_index < len(item_values):
                    column_name = column_keys[column_index]

                    # Obsługa podwójnego kliknięcia w kolumnie z datą
                    if column_name == 'start_date':
                        start_date_str = item_values[column_index]
                        if start_date_str:  # Sprawdzanie, czy start_date_str nie jest puste
                            initial_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        else:
                            initial_date = None

                        date_dialog = CalendarDialog(self, initial_date=initial_date, x=event.x_root, y=event.y_root)

                        if date_dialog.result is not None:
                            date = date_dialog.result
                            self.save_changes(item_id, column_index, date.strftime('%Y-%m-%d'))
                            self.refresh_project_tree()

                    elif column_name == 'end_date':
                        # Pobieranie bieżącej wartości start_date
                        column_index_for_start_date = column_keys.index('start_date')
                        start_date_str = item_values[column_index_for_start_date]
                        start_date_datetime = datetime.strptime(start_date_str, '%Y-%m-%d')
                        start_date = start_date_datetime.date() # Konwersja na typ date

                        end_date_str = item_values[column_index]
                        if end_date_str:  # Sprawdzanie, czy end_date_str nie jest puste
                            initial_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                        else:
                            initial_date = None

                        date_dialog = CalendarDialog(self, initial_date=initial_date, x=event.x_root, y=event.y_root)
                        if date_dialog.result is not None:
                            end_date = date_dialog.result
                            # Upewniamy się, że end_date nie jest wcześniejsza niż start_date
                            if end_date < start_date:
                                messagebox.showerror("Błąd", "Data zakończenia nie może być wcześniejsza niż data rozpoczęcia.")
                            else:
                                self.save_changes(item_id, column_index, end_date.strftime('%Y-%m-%d'))
                                self.update_duration_based_on_end_date(item_id)  # Oblicz i zaktualizuj czas trwania
                                self.refresh_project_tree()
                                
                    # Obsługa podwójnego kliknięcia w kolumnie z czasem trwania
                    elif column_name == 'duration':
                        duration_dialog = DurationDialog(self)
                        if duration_dialog.result is not None:
                            self.save_changes(item_id, column_index, duration_dialog.result)
                            #self.update_end_date_based_on_duration(item_id)
                            self.refresh_project_tree()

                    # Obsługa podwójnego kliknięcia w kolumnie zależności
                    elif column_name == 'dependency_name':
                        self.show_dependency_dialog(item_id, x=event.x_root, y=event.y_root)
                            
                    # Obsługa podwójnego kliknięcia w kolumnie z użytkownikiem
                    elif column_name == 'user':
                        item_type = self.get_item_type(item_id)
    
                        if item_type == 'task':
                            user_dialog = UserDialog(self, self.users, x=event.x_root, y=event.y_root)
                            if user_dialog.result is not None:
                                self.save_changes(item_id, column_index, user_dialog.result)
            
                    # Obsługa podwójnego kliknięcia w kolumnie ze statusem
                    elif column_name == "status":
                        if (item_id, column_index) in self.full_texts:
                            current_value = self.full_texts[(item_id, column_index)]
                        else:
                            current_value = item_values[column_index]
                        self.open_status_window(item_id, column_index, column_name, current_value, x=event.x_root, y=event.y_root) # Otwarcie okna wyboru statusu

                    # Obsługa podwójnego kliknięcia w innych kolumnach
                    else:
                        if (item_id, column_index) in self.full_texts:
                            current_value = self.full_texts[(item_id, column_index)]
                        else:
                            current_value = item_values[column_index]
                        self.open_value_window(item_id, column_index, column_name, current_value)

        # Obsługa rozwijania i zwijania elementów przez podwójne kliknięcie na kolumnie nazwy
        elif column == '#0' and item_id:
            if self.tree.item(item_id, "open"):
                self.tree.item(item_id, open=False) # Zwiń element
            else:
                self.tree.item(item_id, open=True)  # Rozwiń element

        return "break" # Zablokuj domyślne zachowanie dla podwójnego kliknięcia


    def show_dependency_dialog(self, task_id, x=0, y=0):
        project_list = state_manager.get_project_list()
        # Utwórz nowe okno dialogowe
        dependency_window = tk.Toplevel(self)
        dependency_window.title("Zarządzanie zależnością")
        dependency_window.geometry(f"300x150+{x}+{y-140}")
        dependency_window.attributes('-topmost', 'true')  # Upewnij się, że okno jest zawsze na wierzchu

        # Dodaj etykietę z instrukcjami
        label_text = (
            "Najpierw zaznacz zadanie, po którym ma wystąpić\n"
            "to, na które kliknąłęś, a później kliknij Dodaj,\naby dodać zależność."
        )
        label = tk.Label(dependency_window, text=label_text)
        label.pack(pady=10)

        # Funkcja do zamykania okna i zapisywania zmian
        def handle_dependency(action):
            if action == 'add':
                self.add_dependency(task_id)
            else:
                self.load_project(project_list.active_project)
                self.remove_dependency(task_id)
            dependency_window.destroy()
            self.save_to_json()
            
        dependency_window.bind('<Return>', lambda event: handle_dependency('add'))

        # Dodaj przyciski do dodawania i usuwania zależności
        add_button = tk.Button(dependency_window, text="Dodaj zależność", command=lambda: handle_dependency('add'))
        add_button.pack(side="left", padx=10)
        remove_button = tk.Button(dependency_window, text="Usuń zależność", command=lambda: handle_dependency('remove'))
        remove_button.pack(side="right", padx=10)

        
    def add_dependency(self, task_id):
        # Pobierz aktualnie zaznaczone zadanie
        selected_task = self.tree.selection()
        
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)
        
        if selected_task:
            selected_task_id = selected_task[0]
        
            # Pobierz nazwę zaznaczonego zadania
            selected_task_name = self.tree.item(selected_task_id, 'text')
        
            # Zaktualizuj zależność dla zadanego zadania
            values = list(self.tree.item(task_id, 'values'))
            column_keys = list(self.COLUMN_NAMES.keys())
            values[column_keys.index('dependency')] = selected_task_id
            values[column_keys.index('dependency_name')] = selected_task_name
            self.tree.item(task_id, values=values)

        self.refresh_project_tree()


    def remove_dependency(self, task_id):
        # Usuń zależność dla zadanego zadania
        values = list(self.tree.item(task_id, 'values'))
        column_keys = list(self.COLUMN_NAMES.keys())
        values[column_keys.index('dependency')] = ""
        values[column_keys.index('dependency_name')] = ""
        self.tree.item(task_id, values=values)


    def save_changes(self, item_id, column_index, new_value):
        # Pobieranie bieżących wartości elementu
        values = list(self.tree.item(item_id, 'values'))
                    
        project_list = state_manager.get_project_list()
        self.load_project(project_list.active_project)

        # Zapisywanie pełnego tekstu w słowniku
        if isinstance(new_value, str):
            self.full_texts[(item_id, column_index)] = new_value
            values[column_index] = new_value.split('\n')[0]  # Aktualizacja wartości w wybranej kolumnie na pierwszą linię tekstu
        else:
            values[column_index] = new_value

        # Aktualizacja wartości w drzewie
        self.tree.item(item_id, values=values)

        self.save_to_json()  # Zapisz dane do pliku JSON
        

    def open_value_window(self, item_id, column_index, column_name, value):
        # Tworzenie nowego okna z wartością
        value_window = tk.Toplevel(self)
        value_window.title(self.COLUMN_NAMES[column_name])

        # Dodanie widgetu Text, który umożliwi wyświetlenie długiej wartości
        text_widget = tk.Text(value_window, wrap='word')  
        text_widget.insert('1.0', value)
        text_widget.pack(expand=True, fill='both')

        # Dodanie przycisku do zapisywania zmienionych wartości
        save_button = ttk.Button(value_window, text='Zapisz', command=lambda: self.save_changes(item_id, column_index, text_widget.get('1.0', 'end-1c')))
        save_button.pack(pady=10)


    def open_status_window(self, item_id, column_index, column_name, current_value, x=0, y=0):
        status_window = tk.Toplevel(self)
        status_window.title("Wybierz status")
        status_window.geometry(f"+{x-150}+{y-50}")

        statuses = ["nierozpoczęte", "w realizacji", "do testowania", "zrealizowane", "zakończone"]
        status_combobox = ttk.Combobox(status_window, values=statuses)
        status_combobox.pack(padx=10, pady=10)
        status_combobox.set(current_value)

        def save_and_close(event=None):
            self.save_changes(item_id, column_index, status_combobox.get())
            status_window.destroy()

        ttk.Button(status_window, text="OK", command=save_and_close).pack(pady=10)
    
        status_window.bind('<Return>', save_and_close)

        status_window.wait_window()


    def refresh_project_tree(self):

        max_iterations = 18
        iteration_counter = 0
    
        # Zmienna, która będzie śledzić, czy zaszły jakiekolwiek zmiany w datach
        changes_made = True
    
        while changes_made and iteration_counter < max_iterations:
            changes_made = self.refresh_tree()
            iteration_counter += 1

        print(f"Number of iterations: {iteration_counter}")

        # Jeśli osiągnięto maksymalną liczbę iteracji, wyświetl komunikat
        if iteration_counter == max_iterations:
            messagebox.showwarning('Warning', 'Odświeżanie nie zakończyło się po 18 przejściach!')

        self.save_to_json()


    def refresh_tree(self):
        changes_made = False
        root_id = self.tree.get_children()[0]
        for child_id in self.tree.get_children(root_id):
            changes_made |= self.refresh_subtree(child_id)
        return changes_made


    def refresh_subtree(self, item_id):
        changes_made = False
    
        original_values = list(self.tree.item(item_id, 'values'))
    
        # Wywołanie funkcji dotyczących czasu
        self.update_start_date_based_on_dependency(item_id)
        self.update_end_date_based_on_duration(item_id)
    
        # Porównaj wartości z oryginalnymi, żeby zobaczyć, czy coś się zmieniło
        new_values = list(self.tree.item(item_id, 'values'))
        if original_values != new_values:
            changes_made = True

        # Przeszukiwanie dzieci bieżącego elementu
        for child_id in self.tree.get_children(item_id):
            changes_made |= self.refresh_subtree(child_id)
    
        return changes_made


    def update_start_date_based_on_dependency(self, item_id):
        values = list(self.tree.item(item_id, 'values'))
        column_keys = list(self.COLUMN_NAMES.keys())
        dependency_id = values[column_keys.index('dependency')]

        if dependency_id:
            try:
                dependency_end_date = list(self.tree.item(dependency_id, 'values'))[column_keys.index('end_date')]
            except TclError:
                # Jeżeli dependency_id nie istnieje, nie rób nic i wyjdz z funkcji
                return

            values[column_keys.index('start_date')] = dependency_end_date
            self.tree.item(item_id, values=values)


    def update_end_date_based_on_duration(self, item_id):
        # Pobieranie bieżących wartości elementu
        values = list(self.tree.item(item_id, 'values'))
        column_keys = list(self.COLUMN_NAMES.keys())
    
        # Pobieranie wartości start_date i duration
        start_date_str = values[column_keys.index('start_date')]
        duration_str = values[column_keys.index('duration')]

        if start_date_str and duration_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            duration = int(duration_str)

            # Uwzględniamy święta i weekendy w Polsce
            pl_holidays = holidays.Poland(years=start_date.year)
            end_date = start_date
            working_days_added = 0

            while working_days_added < duration:
                end_date += timedelta(days=1)
                if end_date.weekday() >= 5 or end_date in pl_holidays:
                    continue
                working_days_added += 1

            # Aktualizacja wartości end_date
            values[column_keys.index('end_date')] = end_date.strftime('%Y-%m-%d')
            self.tree.item(item_id, values=values)

            #self.save_to_json()  # Zapisz dane do pliku JSON


    def update_duration_based_on_end_date(self, item_id):
        values = self.tree.item(item_id, 'values')
        column_keys = list(self.COLUMN_NAMES.keys())
        start_date_column_index = column_keys.index('start_date')
        end_date_column_index = column_keys.index('end_date')

        start_date_str = values[start_date_column_index]
        end_date_str = values[end_date_column_index]

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        # Oblicz różnicę pomiędzy datami, pomijając weekendy i święta
        duration = self.calculate_working_days(start_date, end_date)

        # Aktualizuj wartość czasu trwania
        duration_column_index = column_keys.index('duration')
        self.save_changes(item_id, duration_column_index, duration)


    def calculate_working_days(self, start_date, end_date):
        # Uwzględniamy święta i weekendy w Polsce
        pl_holidays = holidays.Poland(years=start_date.year)
        working_days = 0
        current_date = start_date

        while current_date < end_date:
            current_date += timedelta(days=1)
            if current_date.weekday() >= 5 or current_date in pl_holidays:
                continue
            working_days += 1
    
        return working_days






