class Section:
    def __init__(self, title, description):
        self.title = title
        self.description = description  # Nowe pole
        self.subsections = []
        self.tasks = []

    def add_subsection(self, title, description):
        self.subsections.append(Section(title, description))  # Dodajemy opis podsekcji

    def add_task(self, task, description):
        self.tasks.append(Task(task, description))  # Dodajemy opis zadania


class Project:
    def __init__(self, project_number, project_title, project_status, project_description):
        self.id = project_number
        self.title = project_title
        self.status = project_status
        self.description = project_description  # Nowe pole
        self.sections = []

    def add_section(self, title, description):
        self.sections.append(Section(title, description))  # Dodajemy opis sekcji

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status,
            'description': self.description,
        }


