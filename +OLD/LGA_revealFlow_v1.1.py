"""
_____________________________________________________________________________________________________

  LGA_revealFlow v2.0 | 2024 | Lega
  Abre la URL de la task Comp del shot, tomando la informacion del nombre del script
  
  Para el login en Windows hay que guardar la informacion del sitio variables de entorno:

  1- Abrir el cmd como administrador.

  2- Usar los siguientes comandos para establecer las variables de entorno (ponerlos uno por uno):

  setx SHOTGRID_URL "https://pagina.shotgrid.autodesk.com"
  setx SHOTGRID_LOGIN "tu_usuario"
  setx SHOTGRID_PASSWORD "tu_contrasena"

  (el usuario es el mail que se usa para login)  
_____________________________________________________________________________________________________
"""



import os
import re
import shotgun_api3
import nuke
import webbrowser
import threading

# Variables globales para definir la ruta del browser custom o si usamos el browser por defecto
browser_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
use_default_browser = False  # Si esta en ON, usa el navegador por defecto, si esta en OFF, usa browser_path


DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)
        

class ShotGridManager:
    def __init__(self, url, login, password):
        self.sg = shotgun_api3.Shotgun(url, login=login, password=password)

    def find_shot_and_tasks(self, project_name, shot_code):
        debug_print(f"Buscando proyecto: {project_name}, shot: {shot_code}")
        projects = self.sg.find("Project", [['name', 'is', project_name]], ['id', 'name'])
        if projects:
            project_id = projects[0]['id']
            debug_print(f"Proyecto encontrado: {project_id}")
            filters = [
                ['project', 'is', {'type': 'Project', 'id': project_id}],
                ['code', 'is', shot_code]
            ]
            fields = ['id', 'code', 'description']
            shots = self.sg.find("Shot", filters, fields)
            if shots:
                shot_id = shots[0]['id']
                debug_print(f"Shot encontrado: {shot_id}")
                tasks = self.find_tasks_for_shot(shot_id)
                return shots[0], tasks
            else:
                debug_print("No se encontro el shot.")
        else:
            debug_print("No se encontro el proyecto en ShotGrid.")
        return None, None

    def find_tasks_for_shot(self, shot_id):
        debug_print(f"Buscando tareas para el shot: {shot_id}")
        filters = [['entity', 'is', {'type': 'Shot', 'id': shot_id}]]
        fields = ['id', 'content', 'sg_status_list']
        tasks = self.sg.find("Task", filters, fields)
        debug_print(f"Tareas encontradas: {tasks}")
        return tasks

    def get_task_url(self, task_id):
        return f"{self.sg.base_url}/detail/Task/{task_id}"

class NukeOperations:
    def __init__(self, shotgrid_manager):
        self.sg_manager = shotgrid_manager

    def parse_nuke_script_name(self, file_name):
        base_name = re.sub(r'_%04d\.nk$', '', file_name)
        version_match = re.search(r'_v(\d+)', base_name)
        version_number = version_match.group(1) if version_match else 'Unknown'
        return base_name, version_number

    def process_current_script(self):
        file_path = nuke.root().name()
        debug_print(f"Nuke script file path: {file_path}")
        if file_path:
            nuke_script_name = os.path.basename(file_path)
            debug_print(f"Nuke script name: {nuke_script_name}")
            base_name, nuke_version_number = self.parse_nuke_script_name(nuke_script_name)
            debug_print(f"Parsed base name: {base_name}, version number: {nuke_version_number}")
            project_name = base_name.split('_')[0]
            parts = base_name.split('_')
            shot_code = '_'.join(parts[:5])
            debug_print(f"Project name: {project_name}, shot code: {shot_code}")

            shot, tasks = self.sg_manager.find_shot_and_tasks(project_name, shot_code)
            if shot:
                for task in tasks:
                    if task['content'] == 'Comp':
                        task_url = self.sg_manager.get_task_url(task['id'])
                        debug_print(f"  - Task: {task['content']} (Status: {task['sg_status_list']}) URL: {task_url}")
                        if use_default_browser:
                            webbrowser.open(task_url)
                        else:
                            webbrowser.get(browser_path).open(task_url)
            else:
                debug_print("No se encontro el shot correspondiente en ShotGrid.")
        else:
            debug_print("No se encontro un script activo en Nuke.")

def threaded_function():
    sg_url = os.getenv('SHOTGRID_URL')
    sg_login = os.getenv('SHOTGRID_LOGIN')
    sg_password = os.getenv('SHOTGRID_PASSWORD')

    if not sg_url or not sg_login or not sg_password:
        debug_print("Las variables de entorno SHOTGRID_URL, SHOTGRID_LOGIN y SHOTGRID_PASSWORD deben estar configuradas.")
        return

    sg_manager = ShotGridManager(sg_url, sg_login, sg_password)
    nuke_ops = NukeOperations(sg_manager)
    nuke_ops.process_current_script()

def main():
    thread = threading.Thread(target=threaded_function)
    thread.start()

if __name__ == "__main__":
    main()
