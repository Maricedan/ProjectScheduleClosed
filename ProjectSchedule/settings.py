import json
import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser


class Settings:
    def __init__(self):
        # Background colors
        self.kolor_tla_wykresu_harmonogramu_1 = "#F7F7F7"  # Light grey for even days, to keep the background unobtrusive
        self.kolor_tla_wykresu_harmonogramu_2 = "#EDEDED"  # Slightly darker grey for odd days, still subtle
        self.kolor_tla_wykresu_dni_wolnych = "#FFE5E5"     # Soft red to indicate holidays and weekends
        self.kolor_linii_dzielacych = "#B0BEC5"            # Subdued blue for dividing lines
        self.kolor_obecnego_dnia = "#FFEBEE"               # Very light purple for the current day

        # Tile colors for tasks
        # Yellow shades for tasks that are slightly late
        self.kolor_kafelka_spozniony_troche_1 = "#FFD180"  # Muted yellow shade 1
        self.kolor_kafelka_spozniony_troche_2 = "#FFCC80"  # Muted yellow shade 2

        # Orange and red shades for tasks that are very late
        self.kolor_kafelka_spozniony_bardzo_1 = "#FF8A80"  # Soft orange
        self.kolor_kafelka_spozniony_bardzo_2 = "#FF5252"  # Soft red

        # Blue shades for planned tasks
        self.kolor_kafelka_zaplanowany_1 = "#81D4FA"       # Light blue shade 1
        self.kolor_kafelka_zaplanowany_2 = "#4FC3F7"       # Light blue shade 2

        # Sky blue shades for tasks in progress
        self.kolor_kafelka_w_realizacji_1 = "#29B6F6"      # Sky blue shade 1
        self.kolor_kafelka_w_realizacji_2 = "#039BE5"      # Sky blue shade 2

        # Pink shades for tasks in testing
        self.kolor_kafelka_w_trakcie_testow_1 = "#FFAB91"  # Soft pink shade 1
        self.kolor_kafelka_w_trakcie_testow_2 = "#FF80AB"  # Soft pink shade 2

        # Green shades for completed tasks
        self.kolor_kafelka_zrealizowane_1 = "#AED581"      # Pastel green shade 1
        self.kolor_kafelka_zrealizowane_2 = "#81C784"      # Pastel green shade 2

        # Grey shades for ended tasks
        self.kolor_kafelka_zakonczone_1 = "#BDBDBD"        # Neutral grey shade 1
        self.kolor_kafelka_zakonczone_2 = "#9E9E9E"        # Neutral grey shade 2
        
        self.kolor_kafelka_dupowaty = '#FFFFFF'
        
        self.liczba_dni_do_czerwieni_kafelka = 3
        
        self.czy_weekend_na_wierzchu = False
        
        self.sciezka_do_danych = 'C:/Users/RMD/OneDrive - Hitmark Sp. z o.o/RMD/Aplikacja'

        self.default_colors = {k: v for k, v in self.__dict__.items() if k != "default_colors"}

    def to_json(self):
        with open("settings.json", "w") as f:
            json.dump(self.__dict__, f)

    def from_json(self):
        try:
            with open("settings.json", "r") as f:
                data = json.load(f)
            for key in self.__dict__.keys():
                setattr(self, key, data.get(key, getattr(self, key, self.default_colors.get(key))))
        except FileNotFoundError:
            pass

settings = Settings()


class AppSettings(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
       # Create a canvas and a vertical scrollbar side by side
        self.canvas = tk.Canvas(self, bg='#F0F0F0')
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Scroll with mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Create a frame inside the canvas to put the widgets
        self.inner_frame = tk.Frame(self.canvas, bg="#F0F0F0", width=1400)  
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        self.inner_frame.grid_columnconfigure(1, minsize=700)

        self.color_vars = {}
        self.number_vars = {}

        # Tworzenie ColorPickerów
        column = 0
        for attribute, color in vars(settings).items():
            if not attribute.startswith("kolor"):
                continue
            color_var = tk.StringVar(value=color)
            self.color_vars[attribute] = color_var
            default_color = settings.default_colors.get(attribute, "#FFFFFF")
            color_picker_frame = ColorPicker(self.inner_frame, attribute, color_var, default_color, column).frame
            color_picker_frame.grid(row=column, column=0, padx=5, pady=5)
            column += 1

        # Tworzenie widgetów do zmiany liczby
        column = 0
        for attribute, value in vars(settings).items():
            if not attribute.startswith("liczba"):
                continue
            number_var = tk.IntVar(value=value)
            self.number_vars[attribute] = number_var
            number_picker_frame = NumberPicker(self.inner_frame, attribute, number_var, 0, 365).frame
            number_picker_frame.grid(row=column, column=1, padx=5, pady=5, sticky="w")
            column += 1

        # Initialize toggle button states
        self.bool_vars = {}
        self.bool_buttons = {}  # Initialize an empty dictionary to keep the buttons

        def make_toggle_function(attr):
            def toggle_button():
                current_state = self.bool_vars[attr].get()
                button = self.bool_buttons[attr]
                if current_state:
                    button.configure(style="Gray.TButton")
                else:
                    button.configure(style="Green.TButton")
                new_state = not current_state
                self.bool_vars[attr].set(new_state)
                setattr(settings, attr, new_state)  # Update the settings attribute to match the tk.BooleanVar
            return toggle_button

        # Creating Toggle Buttons
        for attribute, value in vars(settings).items():
            if not attribute.startswith("czy"):
                continue
            bool_var = tk.BooleanVar(value=value)
            self.bool_vars[attribute] = bool_var
            display_label = attribute.replace('_', ' ')
            button = ttk.Button(self.inner_frame, text=display_label, command=make_toggle_function(attribute), style="Green.TButton" if value else "Gray.TButton")
            button.grid(row=column, column=1, padx=5, pady=5)  # Using the same 'column' variable to align with number variables
            self.bool_buttons[attribute] = button  # Store the button in the dictionary
            column += 1  # Increment the column for the next button
            
        # Widget for sciezka_do_danych
        self.path_var = tk.StringVar(value=settings.sciezka_do_danych)
        self.path_label = tk.Label(self.inner_frame, text="ścieżka do danych")
        self.path_label.grid(row=column, column=1, padx=5, pady=5, sticky="w")
        self.path_entry = tk.Entry(self.inner_frame, textvariable=self.path_var, width = 30)
        self.path_entry.grid(row=column, column=1, padx=306, pady=5, sticky="w")
        self.path_button = ttk.Button(self.inner_frame, text="Zapisz", command=self.save_path)
        self.path_button.grid(row=column, column=1, padx=540, pady=5, sticky="e")
        column += 1

                                
        # Update inner_frame size and configure canvas to scroll
        self.inner_frame.bind("<Configure>", lambda event, canvas=self.canvas: self.update_scroll_region(canvas))
        
    def update_scroll_region(self, canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")
        
    def save_path(self):
        raw_path = self.path_var.get()
        normalized_path = raw_path.replace('\\', '\\')
        settings.sciezka_do_danych = normalized_path
        settings.to_json()
                

class NumberPicker:
    def __init__(self, parent, label, number_var, min_value, max_value):
        self.frame = tk.Frame(parent, width=700, height=50)
        self.frame.grid_propagate(0)
        self.label = label
        self.number_var = number_var
        self.min_value = min_value
        self.max_value = max_value
        self.create_widgets()

    def create_widgets(self):
        display_label = self.label.replace('_', ' ')
        self.label_widget = tk.Label(self.frame, text=display_label)
        self.label_widget.place(x=0, y=15, anchor='w')

        self.spin_box = tk.Spinbox(self.frame, from_=self.min_value, to=self.max_value, textvariable=self.number_var, command=self.update_setting)
        self.spin_box.place(x=300, y=12)
        
    def update_setting(self):
        setattr(settings, self.label, int(self.number_var.get()))
        settings.to_json()


class ColorPicker:
    def __init__(self, parent, label, color_var, default_color, column):
        self.frame = tk.Frame(parent, width=700, height=50)
        self.frame.grid_propagate(0)
        self.label = label
        self.color_var = color_var
        self.default_color = default_color
        self.column = column
        self.create_widgets()

    def create_widgets(self):
        display_label = self.label.replace('_', ' ')
        self.label_widget = tk.Label(self.frame, text=display_label)
        self.label_widget.place(x=10, y=15)

        self.color_button = tk.Button(self.frame, text="Wybierz kolor", command=self.choose_color)
        self.color_button.place(x=300, y=10)

        self.default_button = tk.Button(self.frame, text="Domyślny", command=self.set_default_color)
        self.default_button.place(x=400, y=10)

        self.color_display = tk.Label(self.frame, width=15, textvariable=self.color_var)
        self.color_display.place(x=480, y=12)

        self.color_rect = tk.Label(self.frame, width=10, height=1)
        self.color_rect.place(x=570, y=12)
        self.color_rect.bind("<Button-1>", self.input_color)

        self.update_display()

    def update_display(self):
        self.color_rect.config(bg=self.color_var.get())

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Wybierz kolor", initialcolor=self.color_var.get())[1]
        if color_code:
            self.color_var.set(color_code)
            self.update_display()
            setattr(settings, self.label, color_code)
            settings.to_json()

    def set_default_color(self):
        self.color_var.set(self.default_color)
        self.update_display()
        setattr(settings, self.label, self.default_color)
        settings.to_json()

    def input_color(self, event):
        new_color = tk.simpledialog.askstring("Wprowadź kolor", "Podaj kod koloru:")
        if new_color and new_color.startswith("#") and len(new_color) == 7:
            self.color_var.set(new_color)
            self.update_display()
            setattr(settings, self.label, new_color)
            settings.to_json()

