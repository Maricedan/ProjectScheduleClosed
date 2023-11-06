# state_manager.py
class StateManager:
    def __init__(self):
        self.project_editor = None
        self.project_list = None
        self.figure = None
        self.notebook = None  # Dodanie atrybutu dla Notebook

    def set_project_editor(self, project_editor_instance):
        self.project_editor = project_editor_instance

    def get_project_editor(self):
        return self.project_editor

    def set_project_list(self, project_list_instance):
        self.project_list = project_list_instance

    def get_project_list(self):
        return self.project_list

    def set_figure(self, figure_instance):
        self.figure = figure_instance

    def get_figure(self):
        return self.figure

    def set_notebook(self, notebook_instance): 
        self.notebook = notebook_instance

    def get_notebook(self):
        return self.notebook
    
    def set_task_card(self, task_card):
        self.task_card = task_card
    
    def get_task_card(self):
        return self.task_card

# Inicjalizacja globalnej instancji
state_manager = StateManager()