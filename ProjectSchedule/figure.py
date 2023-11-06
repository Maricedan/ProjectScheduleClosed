import tkinter as tk
import json
from turtle import color
import holidays
import os
from tkinter import ttk, font
from datetime import datetime, timedelta
from datetime import date as dt_date
from settings import settings
from state_manager import state_manager



class User:
    def __init__(self, name):
        self.name = name
        self.tasks = []


    def add_task(self, task):
        self.tasks.append(task)


    def earliest_start_date(self):
        return min((task.start_date for task in self.tasks if task.start_date is not None), default=datetime(2023, 1, 1))


    def latest_end_date(self):
        return max((task.end_date for task in self.tasks if task.end_date is not None), default=datetime.min)

        
    def draw(self, user_canvas, timeline_canvas, x, y, pixel_per_day, start_date):
        user_canvas.create_text(x, y+20, text=self.name, anchor='nw', font='Helvetica 10 bold')
        base_y_task = y - 50

        # Create a dictionary for each day between start_date and end_date
        day_dict = {}
        for task in self.tasks:
            if task.start_date and task.end_date:
                for d in range((task.end_date - task.start_date).days):
                    current_day = task.start_date + timedelta(days=d)
                    if current_day not in day_dict:
                        day_dict[current_day] = {'count': 0, 'y_positions': []}
                    day_dict[current_day]['count'] += 1

        sorted_tasks = sorted(self.tasks, key=lambda task: task.start_date if task.start_date else datetime.min)

        for task in sorted_tasks:
            if task.start_date and task.end_date:
                # Find maximum number of tasks for this task's period
                try:
                    max_tasks = max(day_dict[task.start_date + timedelta(days=d)]['count'] for d in range((task.end_date - task.start_date).days))
                except ValueError:
                    max_tasks = 1  # Or any default value you prefer

                max_task_height = 150
                task_height = max_task_height / max_tasks

                # Find the lowest available y position for this task
                y_task = base_y_task
                for d in range((task.end_date - task.start_date).days):
                    current_day = task.start_date + timedelta(days=d)
                    occupied_y = day_dict[current_day]['y_positions']

                    while any(y_task <= oy < y_task + task_height / 2 for oy in occupied_y):
                        y_task += 1

                    # Calculate the available height
                    available_height = min([oy for oy in occupied_y if oy >= y_task] + [y_task + task_height]) - y_task

                    # Update task height if available space is less than original task_height
                    if available_height < task_height:
                        task_height = available_height

                # Draw the task
                task.draw(timeline_canvas, x, y_task, pixel_per_day, start_date, task_height,
                          unique_id=task.unique_id, text=task.text, description=task.description, start_date_str=task.start_date, end_date_str=task.end_date, 
                          status=task.status, user=task.user, item_type=task.item_type, dependency=task.dependency)

                # Update the y positions in the day_dict
                for d in range((task.end_date - task.start_date).days):
                    current_day = task.start_date + timedelta(days=d)
                    day_dict[current_day]['y_positions'].extend(range(int(y_task), int(y_task + task_height)))


# Funkcja do generowania menu kontekstowego
def generate_context_menu(canvas, unique_id):
    project_editor_frame = state_manager.get_project_editor()
    figure = state_manager.get_figure()
    notebook = state_manager.get_notebook()
    task_card = state_manager.get_task_card()
    
    def change_status(new_status):
        project_editor_frame.save_changes(unique_id, 5, new_status)
        figure.refresh_schedule()
                    
    def go_to_project_editor(unique_id):
        # Pobieramy instancje Notebook i ProjectEditor z state_manager

        project_editor_frame = state_manager.get_project_editor()

        # Zmieniamy zakładkę na 'Edycja projektu'
        notebook.select(project_editor_frame)

        # Ustawiamy fokus na element o zadanym unique_id
        project_editor_frame.focus_on_tree_item(unique_id)

    def go_to_task_card(unique_id):
        project_id = state_manager.get_project_editor().project_id
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data', 'projects', str(project_id))
        task_path = os.path.join(data_folder_path, str(unique_id))

        # Wczytanie danych podstawowych zadania z pliku JSON
        task_data_path = os.path.join(task_path, f'{unique_id}_basic_data.json')
        with open(task_data_path, 'r') as file:
            basic_data = json.load(file)

        task_card_instance = state_manager.get_task_card()
        task_card_instance.populate_file_list(task_path)
        task_card_instance.update_label(basic_data)
        
        notebook.select(task_card)
        
        

    # Tworzenie menu kontekstowego
    context_menu = tk.Menu(canvas, tearoff=0)

    # Dodanie opcji zmiany statusu
    for status_option in ['zrealizowane', 'nierozpoczęte', 'do testowania', 'w realizacji', 'zakończone']:
        context_menu.add_command(label=status_option, command=lambda status_option=status_option: change_status(status_option))

    # Dodanie separatora
    context_menu.add_separator()

    # Dodanie nowych opcji z lambda funkcją dla przekazania unique_id
    context_menu.add_command(label="do edycji projektu", command=lambda unique_id=unique_id: go_to_project_editor(unique_id))
    context_menu.add_command(label="do karty zadania", command=lambda: go_to_task_card(unique_id))  # Replace with your actual function

    def on_right_click(event):
        context_menu.tk_popup(event.x_root, event.y_root)

    canvas.tag_bind(f"task{unique_id}", "<Button-3>", on_right_click)


class Task:
    toggle_shade = True  # Zmienna do przełączania odcienia
    
    def __init__(self, unique_id, text, description, start_date, end_date, status, user, item_type, dependency=""):
        self.unique_id = unique_id
        self.text = text
        self.description = description
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        self.status = status
        self.user = user
        self.item_type = item_type
        self.dependency = dependency
        self.y_task = None
        
    def get_path_from_file(self, unique_id):
        project_id = state_manager.get_project_editor().project_id

        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data', 'projects', str(project_id), unique_id)
        data_path = os.path.join(data_folder_path, f'{unique_id}_basic_data.json')
    
        try:
            with open(data_path, 'r') as file:
                data = json.load(file)
                return data.get('path_in_tree', '')
        except FileNotFoundError:
            return ''

    def draw(self, canvas, x, y, pixel_per_day, start_date, height, unique_id=None, text=None, description=None, start_date_str=None, end_date_str=None, status=None, user=None, item_type=None, dependency=None):
        x_start = (self.start_date - start_date).days * pixel_per_day - 8
        x_end = (self.end_date - start_date).days * pixel_per_day - 12
        y_top = y + 1
        y_bottom = y - 1 + height - 5
        radius = 5
        
        # Convert today to datetime object for consistent comparison
        today = datetime.combine(dt_date.today(), datetime.min.time())
        # Obliczenie koloru
        if self.status == "zrealizowane":
            color = settings.kolor_kafelka_zrealizowane_1 if Task.toggle_shade else settings.kolor_kafelka_zrealizowane_2
        elif self.status == "nierozpoczęte" and (self.end_date >= today):
            color = settings.kolor_kafelka_zaplanowany_1 if Task.toggle_shade else settings.kolor_kafelka_zaplanowany_2
        elif self.status == "do testowania" and (self.end_date >= today):
            color = settings.kolor_kafelka_w_trakcie_testow_1 if Task.toggle_shade else settings.kolor_kafelka_w_trakcie_testow_2
        elif self.status == "w realizacji" and (self.end_date >= today):
            color = settings.kolor_kafelka_w_realizacji_1 if Task.toggle_shade else settings.kolor_kafelka_w_realizacji_2
        elif self.status == "zakończone":
            color = settings.kolor_kafelka_zakonczone_1 if Task.toggle_shade else settings.kolor_kafelka_zakonczone_2
        elif self.end_date < today:
            if (today - self.end_date).days < settings.liczba_dni_do_czerwieni_kafelka:
                color = settings.kolor_kafelka_spozniony_troche_1 if Task.toggle_shade else settings.kolor_kafelka_spozniony_troche_2
            else:
                color = settings.kolor_kafelka_spozniony_bardzo_1 if Task.toggle_shade else settings.kolor_kafelka_spozniony_bardzo_2

        # Przełączanie odcienia dla kolejnych kafelków
        Task.toggle_shade = not Task.toggle_shade

        points = [x + x_start + radius, y_top,
                  x + x_end - radius, y_top,
                  x + x_end, y_top + radius,
                  x + x_end, y_bottom - radius,
                  x + x_end - radius, y_bottom,
                  x + x_start + radius, y_bottom,
                  x + x_start, y_bottom - radius,
                  x + x_start, y_top + radius]
        
        canvas.create_polygon(points, fill=color, tags=f"task{self.unique_id}")
        
        # Dodanie wywołania generate_context_menu
        generate_context_menu(canvas, self.unique_id)

        # Adding external edge
        edge_color = "light blue"
        edge_thickness = 1

        # Draw lines between each pair of points
        for i in range(0, len(points) - 2, 2):
            canvas.create_line(points[i], points[i + 1], points[i + 2], points[i + 3], fill=edge_color, width=edge_thickness)
    
        # Close the shape by drawing a line between the last and the first point
        canvas.create_line(points[-2], points[-1], points[0], points[1], fill=edge_color, width=edge_thickness)


        # Wyświetlanie prostokąta z danymi
        info_box = canvas.create_rectangle(0, 0, 0, 0, fill="white", tags=f"info{self.unique_id}")
        max_line_length = 450
        info_text = canvas.create_text(
            0, 0, 
            text="", 
            width=max_line_length,  # wrap text
            anchor='nw',            # anchor text at the top left corner
            tags=f"info{self.unique_id}"
        )
        
        def generate_show_info(canvas, info_box, info_text, unique_id, text, description, start_date_str, end_date_str, status, user, item_type, dependency):
            def show_info(event):
                x_scroll_pos = canvas.canvasx(0)
                y_scroll_pos = canvas.canvasy(0)
                adjusted_x = event.x + x_scroll_pos
                adjusted_y = event.y + y_scroll_pos

                # Określenie wymiarów okienka informacyjnego
                box_height = 450
                box_width = 500

                # Sprawdzenie, czy okienko nie wyjdzie poza dolną krawędź
                canvas_height = canvas.winfo_height()
                if adjusted_y + box_height + 10 > canvas_height + y_scroll_pos:
                    adjusted_y = canvas_height + y_scroll_pos - box_height - 10

                # Ustawienie wymiarów i pozycji okienka
                canvas.coords(info_box, adjusted_x + 10, adjusted_y + 10, adjusted_x + box_width, adjusted_y + box_height)

                # Zwiększenie czcionki do 16
                canvas.itemconfig(info_text, font=("TkDefaultFont", 14))
        
                # Uaktualnienie pozycji tekstu
                canvas.coords(info_text, adjusted_x + 30, adjusted_y + 30)  
                
                path_in_tree = self.get_path_from_file(unique_id)
        
                info_content = f"ID: {unique_id}\nText: {text}\nDescription: {description}\nStart Date: {start_date_str}\nEnd Date: {end_date_str}\nStatus: {status}\nUser: {user}\nType: {item_type}\nDependency: {dependency}\nPath: {path_in_tree}"
                canvas.itemconfig(info_text, text=info_content)

                canvas.tag_raise(info_box)
                canvas.tag_raise(info_text)

            def hide_info(event):
                canvas.coords(info_box, 0, 0, 0, 0)
                canvas.coords(info_text, 0, 0)
                canvas.itemconfig(info_text, text="")

            return show_info, hide_info


        show_info, hide_info = generate_show_info(canvas, info_box, info_text, self.unique_id, self.text, self.description, self.start_date, self.end_date, self.status, self.user, self.item_type, self.dependency)
        canvas.tag_bind(f"task{self.unique_id}", "<Enter>", show_info)
        canvas.tag_bind(f"task{self.unique_id}", "<Leave>", hide_info)


        # Text parameters
        text_padding_left = 5  # Increased from 5 to 10
        text_padding_right = 3  # Added right padding
        max_width = x_end - x_start - (text_padding_left + text_padding_right)  # Now considers both left and right padding
        font_type = 'Helvetica'
        font_weight = 'bold'
        x_text = x + x_start + text_padding_left
        y_text = y_top + (height / 2)
        y_offset = -3

        # Estimate text dimensions for different font sizes
        estimated_lines = {}
        bottom_padding = 20  # Increased from 2 to 5

        for size in range(3, 11):  # Reduced max size to 11
            text_id = canvas.create_text(x_text, y_text, text=self.text, anchor='w', fill='black', font=(font_type, size, font_weight))
            text_width = canvas.bbox(text_id)[2] - canvas.bbox(text_id)[0]
            text_height = canvas.bbox(text_id)[3] - canvas.bbox(text_id)[1]
            canvas.delete(text_id)

            # Calculate the number of lines required for this font size
            lines_required = int(text_width / max_width) + 1
            total_height_required = lines_required * text_height + bottom_padding

            # Save the number of lines and total height required for this font size
            estimated_lines[size] = {'lines': lines_required, 'total_height': total_height_required}

        # Choose the font size that fits best within the task height
        chosen_size = 0
        for size, info in sorted(estimated_lines.items(), key=lambda x: x[1]['total_height']):
            if info['total_height'] <= height:
                chosen_size = size

        # If no size fits, choose the smallest available font size
        if chosen_size == 0:
            chosen_size = min(estimated_lines.keys())

        # Wrap the text based on chosen font size
        words = self.text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            test_line = current_line + ' ' + word if current_line else word
            text_id = canvas.create_text(x_text, y_text, text=test_line, anchor='w', fill='black', font=(font_type, chosen_size, font_weight))
            text_width = canvas.bbox(text_id)[2] - canvas.bbox(text_id)[0]
            canvas.delete(text_id)

            if text_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)
        final_text = '\n'.join(lines)

        # Create the text with the chosen font size
        canvas.create_text(x_text, y_text + y_offset, text=final_text, anchor='w', fill='black', font=(font_type, chosen_size, font_weight))



class Figure(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.project_id = None
        self.pixel_per_day = 180
        self.users = []
        self.vertical_line_length = 0
        
        # Dodanie paska na górze
        self.top_bar = ttk.Frame(self)
        self.top_bar.pack(side='top', fill='x')

        # Przycisk "Odśwież"
        self.refresh_button = ttk.Button(self.top_bar, text="Odśwież", command=self.refresh_schedule)
        self.refresh_button.pack(side='left', padx = 10, pady = 10)

        # Napis z numerem projektu
        self.project_label = ttk.Label(self.top_bar, text="", anchor='e')
        self.project_label.pack(side='left', fill='x', padx = 5)
        
        self.today_button = ttk.Button(self.top_bar, text="Dziś", command=self.set_scrollbar_to_today)
        self.today_button.pack(side='left', padx=10, pady=10)
                
        # Left panel with users
        self.user_canvas = tk.Canvas(self, bg='white', width=100)
        self.user_canvas.pack(side='left', fill='y')
        
        # Right panel with timeline
        self.right_panel = ttk.Frame(self)
        self.right_panel.pack(side='left', fill='both', expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.right_panel, orient='horizontal')
        self.scrollbar.pack(side='bottom', fill='x')
        self.timeline_canvas = tk.Canvas(self.right_panel, bg='white', xscrollcommand=self.scrollbar.set)
        self.timeline_canvas.pack(side='top', fill='both', expand=True)
        self.timeline_canvas.bind('<Control-MouseWheel>', self.on_zoom)
        self.scrollbar.config(command=self.timeline_canvas.xview)

        # self.zoom_in_button = ttk.Button(self.right_panel, text="Zoom In", command=self.zoom_in)
        # self.zoom_in_button.pack(side='left')
        # self.zoom_out_button = ttk.Button(self.right_panel, text="Zoom Out", command=self.zoom_out)
        # self.zoom_out_button.pack(side='right')

        self.start_date = datetime(2023, 1, 1)  # Default start date
        self.end_date = self.start_date + timedelta(days=365)  # Default end date
        
        # # Pionowy suwak
        # self.v_scrollbar = ttk.Scrollbar(self.right_panel, orient='vertical', command=self.timeline_canvas.yview)
        # self.v_scrollbar.pack(side='right', fill='y')
        # self.timeline_canvas.config(yscrollcommand=self.v_scrollbar.set)

        # Obsługa kółka myszy - przewijanie pionowe
        self.timeline_canvas.bind('<MouseWheel>', self.on_scroll_vertical)

        # Obsługa kółka myszy z wciśniętym Shift - przewijanie poziome
        self.timeline_canvas.bind('<Shift-MouseWheel>', self.on_scroll_horizontal)

        self.init_bool = True

        self.draw_timeline()
        self.after(3000, self.set_scrollbar_to_today)
        

    def set_scrollbar_to_today(self):
        today = dt_date.today()
        days_to_today = (today - self.start_date.date()).days
        x_position = days_to_today * self.pixel_per_day
    
        canvas_width = self.timeline_canvas.winfo_width()

        if canvas_width != 1:  # Avoid div by zero or setting xview when canvas not yet drawn
            half_canvas = canvas_width / 2
            position_in_canvas = (x_position - half_canvas + self.pixel_per_day / 2) / self.canvas_width
            self.timeline_canvas.xview_moveto(position_in_canvas)

        
    def on_scroll_vertical(self, event):
        delta = -1 * (event.delta // 120)
        self.timeline_canvas.yview_scroll(delta, 'units')
        self.user_canvas.yview_scroll(delta, 'units')


    def on_scroll_horizontal(self, event):
        self.timeline_canvas.xview_scroll(-1*(event.delta//120), 'units')


    def refresh_schedule(self, event = None):
        self.load_project_by_id()
        self.draw_timeline()    
        if self.init_bool:
               self.set_scrollbar_to_today()
               self.init_bool = False

        
    def set_project_id(self, project_id):
        self.project_id = project_id
        self.project_label.config(text=f"Aktualnie wybrany projekt: {self.project_id}")
        self.load_project_by_id()


    def load_project_by_id(self):
        data_folder_path = os.path.join(settings.sciezka_do_danych, 'data', 'projects')
        project_data_path = os.path.join(data_folder_path, f'project_{self.project_id}.json')
        
        user_dict = {}
        data = {}
    
        try:
            with open(project_data_path, 'r') as f:
                data = json.load(f)
            self.users = []  # Reset users list

            # Creating a dictionary to keep track of users
            user_dict = {username: User(username) for username in self.get_users(data)}
            def extract_tasks(item, user, unique_id=None):
                if "values" in item:
                    task_user = item["values"].get("user", "")
                    if task_user == user.name:
                        task = Task(
                            unique_id=unique_id,
                            text=item.get("text", ""),
                            description=item["values"].get("description", ""),
                            start_date=item["values"].get("start_date", ""),
                            end_date=item["values"].get("end_date", ""),
                            status=item["values"].get("status", ""),
                            user=item["values"].get("user", ""),
                            item_type=item["values"].get("item_type", ""),
                            dependency=item["values"].get("dependency", "")
                        )
                        user.add_task(task)
                # Recursively go through children (if needed)
                for unique_id, child in item.get('children', {}).items():
                    extract_tasks(child, user, unique_id)
                
        # except FileNotFoundError:
        #     print("Project file not found.")

            for username, user_obj in user_dict.items():
                for item in data.values():
                    extract_tasks(item, user_obj) # Recursively extract tasks from all items, not just those assigned to the user
                
            self.users = list(user_dict.values())
            self.update_project_data(data)

            # Determine the earliest start date and latest end date in the project
            earliest_start_date = min(user.earliest_start_date() for user in self.users) if self.users else datetime(2023, 1, 1)
            latest_end_date = max(user.latest_end_date() for user in self.users) if self.users else earliest_start_date

            # Update the start and end dates of the timeline, adding a buffer of 3 days
            self.start_date = earliest_start_date - timedelta(days=3)
            self.end_date = latest_end_date + timedelta(days=3)

            self.draw_timeline()

        except FileNotFoundError:
            # Handle the situation when the project file does not exist
            print(f"File for project {self.project_id} not found.")  # Debug print
            pass
        
    def get_users(self, data):
        users = set()
        def extract_users(item):
            if 'user' in item['values'] and item['values']['user']:
                users.add(item['values']['user'])
            for child in item['children'].values():
                extract_users(child)

        for item in data.values():
            extract_users(item)

        return sorted(list(users))


    def update_project_data(self, data):
        # Aktualizuj dane i przerysuj wykres
        self.project_data = data
        self.draw_timeline()


    def on_zoom(self, event):
        delta = event.delta
        mouse_position_x = event.x  # Extract the mouse's X position from the event

        if delta < 0:
            self.zoom(-10, mouse_position_x)
        elif delta > 0:
            self.zoom(10, mouse_position_x)
        

    def zoom_in(self):
        # Simulate mouse position at the center of the canvas or any other position you prefer
        mouse_position_x = self.timeline_canvas.winfo_width() // 2
        self.zoom(10, mouse_position_x)


    def zoom_out(self):
        if self.pixel_per_day > 10:
            # Simulate mouse position at the center of the canvas or any other position you prefer
            mouse_position_x = self.timeline_canvas.winfo_width() // 2
            self.zoom(-10, mouse_position_x)


    def zoom(self, delta, mouse_position_x=None):
        new_pixel_per_day = self.pixel_per_day + delta
        if new_pixel_per_day <= 0:
            return  # Prevent zooming out further if it leads to zero or negative pixels per day
    
        # Step 1: Get the current scroll position
        current_scroll_position = self.timeline_canvas.xview()[0]
        canvas_width = self.timeline_canvas.winfo_width()

        if mouse_position_x is None:
            mouse_position_x = canvas_width // 2  # Default to center if not provided

        # Step 2: Calculate the date under the mouse cursor
        current_scroll_pixel = current_scroll_position * self.canvas_width
        date_under_cursor = self.start_date + timedelta(days=(current_scroll_pixel + mouse_position_x) / self.pixel_per_day)

        # Step 3: Apply Zoom
        self.pixel_per_day = new_pixel_per_day
        self.draw_timeline()  # Also reconfigure the scroll region if necessary

        # Step 4: Calculate the new scroll position
        new_pixel_position = (date_under_cursor - self.start_date).days * self.pixel_per_day

        # Check if the canvas width is zero to avoid division by zero
        if self.canvas_width != 0:
            new_scroll_position = (new_pixel_position - mouse_position_x) / self.canvas_width
        else:
            new_scroll_position = 0  # Or set it to a value that makes sense in your context

        # Step 5: Set the scrollbar's position
        self.timeline_canvas.xview_moveto(new_scroll_position)


    def draw_timeline(self):
        # Clear the canvas
        self.timeline_canvas.delete('all')
        
        Task.toggle_shade = False
    
        # Canvas width and scroll region configuration
        canvas_width = (self.end_date - self.start_date).days * self.pixel_per_day
        self.canvas_width = canvas_width
        canvas_height = self.vertical_line_length 
        self.timeline_canvas.config(scrollregion=(0, 0, self.canvas_width, canvas_height))

        # Set the scroll region for user_canvas, no horizontal scroll needed
        self.user_canvas.config(scrollregion=(0, 2, 100, canvas_height + 19))  # Width is fixed at 100
    
        #self.timeline_canvas.config(scrollregion=self.timeline_canvas.bbox("all"))
    
        self.draw_date_labels(self.start_date, self.end_date)
        self.draw_lines(self.start_date, self.end_date)
        if settings.czy_weekend_na_wierzchu:
            self.draw_users(self.start_date, self.end_date)
        
        self.draw_date_labels(self.start_date, self.end_date, True)
        self.draw_lines(self.start_date, self.end_date, True)
        if not settings.czy_weekend_na_wierzchu:
            self.draw_users(self.start_date, self.end_date)
        self.draw_users_line(self.start_date, self.end_date)


    def draw_users(self, start_date, end_date):
        self.user_canvas.delete('all')  # Always clear the user canvas
        self.timeline_canvas.delete('line') # Clear previous lines

        if not self.users:  # Return early if no users
            return

        # Gap between users
        user_gap = 100

        # Distance from the top (adjust this to change the position of users)
        top_distance = 30

        # Initial vertical offset, equal to half the gap between users plus top distance
        y_offset = user_gap / 2 + top_distance

        user_y = y_offset
        num_days = (end_date - start_date).days
        line_width = (num_days + 1) * self.pixel_per_day

        # Draw a line for the first user (outside the loop)
        self.user_canvas.create_line(0, user_y - (user_gap / 2) + 2, 100, user_y - (user_gap / 2) + 2)
        self.timeline_canvas.create_line(0, user_y - (user_gap / 2), line_width, user_y - (user_gap / 2), tags='line')
        
        for user in self.users:
            user.draw(self.user_canvas, self.timeline_canvas, 10, user_y, self.pixel_per_day, start_date)  # Pass both canvases
            user_y += user_gap + 50


        # Length of vertical lines
        self.vertical_line_length = user_y - y_offset + top_distance
        

    def draw_users_line(self, start_date, end_date):

        if not self.users:  # Return early if no users
            return

        # Gap between users
        user_gap = 100

        # Distance from the top (adjust this to change the position of users)
        top_distance = 30

        # Initial vertical offset, equal to half the gap between users plus top distance
        y_offset = user_gap / 2 + top_distance

        user_y = y_offset
        num_days = (end_date - start_date).days
        line_width = (num_days + 1) * self.pixel_per_day

        # Draw a line for the first user (outside the loop)
        self.user_canvas.create_line(0, user_y - (user_gap / 2) + 2, 100, user_y - (user_gap / 2) + 2, fill=settings.kolor_linii_dzielacych, width=2)
        self.timeline_canvas.create_line(0, user_y - (user_gap / 2), line_width, user_y - (user_gap / 2), tags='line', fill=settings.kolor_linii_dzielacych, width=2)
        
        for user in self.users:            
            user_y += user_gap + 50

            # Draw horizontal line between users in user_canvas at the bottom of user section (+1 to align with timeline)
            self.user_canvas.create_line(0, user_y - (user_gap / 2) + 2, 100, user_y - (user_gap / 2) + 2, fill=settings.kolor_linii_dzielacych)

            # Draw horizontal line between users in timeline_canvas at the bottom of user section
            self.timeline_canvas.create_line(0, user_y - (user_gap / 2), line_width, user_y - (user_gap / 2), tags='line', fill=settings.kolor_linii_dzielacych)


    def draw_date_labels(self, start_date, end_date, only_holidays_and_weekends=False):
        today = dt_date.today()
        polish_holidays = holidays.Poland(years=[start_date.year, end_date.year])
        label_interval = 1
        font_color = 'black'

        for day in range((end_date - start_date).days + 1):
            x = day * self.pixel_per_day
            date = start_date + timedelta(days=day)
            date_as_date = date.date()  # Convert datetime to date

            is_holiday_or_weekend = date in polish_holidays or date.weekday() >= 5

            if only_holidays_and_weekends and not is_holiday_or_weekend:
                continue
            if not only_holidays_and_weekends and is_holiday_or_weekend:
                continue

            # Check if the date is today
            if date_as_date == today:
                font_color = 'red'
                background_color = settings.kolor_obecnego_dnia
            else:
                font_color = 'black'
                background_color = settings.kolor_tla_wykresu_dni_wolnych if is_holiday_or_weekend else \
                    settings.kolor_tla_wykresu_harmonogramu_1 if day % 2 == 0 else \
                    settings.kolor_tla_wykresu_harmonogramu_2

            x_end = x + self.pixel_per_day
            self.timeline_canvas.create_rectangle(x, 0, x_end, self.vertical_line_length, fill=background_color, outline="")

            if day % label_interval == 0:
                date_label = date.strftime('%Y-%m-%d')
                font_size = 9 - (7 - (self.pixel_per_day / 10)) if self.pixel_per_day < 70 else 10
                my_font = font.Font(family='Helvetica', size=int(font_size), weight='bold')
                text_width = my_font.measure(date_label)
                x_text = x + self.pixel_per_day / 2 - text_width / 2
                self.timeline_canvas.create_text(x_text, 10, text=date_label, anchor='nw', font=my_font, fill=font_color)

    def draw_lines(self, start_date, end_date, only_holidays_and_weekends=False):
        polish_holidays = holidays.Poland(years=[start_date.year, end_date.year])

        for day in range((end_date - start_date).days + 2):
            x = day * self.pixel_per_day
            date = start_date + timedelta(days=day)

            is_holiday_or_weekend = date in polish_holidays or date.weekday() >= 5

            if only_holidays_and_weekends and not is_holiday_or_weekend:
                continue
            if not only_holidays_and_weekends and is_holiday_or_weekend:
                continue

            self.timeline_canvas.create_line(x, 0, x, self.vertical_line_length, fill=settings.kolor_linii_dzielacych, width=1)





