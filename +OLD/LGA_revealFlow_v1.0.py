import os
import re
import shotgun_api3
import nuke
import webbrowser

class ShotGridManager:
    def __init__(self, url, login, password):
        self.sg = shotgun_api3.Shotgun(url, login=login, password=password)

    def find_shot_and_tasks(self, project_name, shot_code):
        print(f"Buscando proyecto: {project_name}, shot: {shot_code}")
        projects = self.sg.find("Project", [['name', 'is', project_name]], ['id', 'name'])
        if projects:
            project_id = projects[0]['id']
            print(f"Proyecto encontrado: {project_id}")
            filters = [
                ['project', 'is', {'type': 'Project', 'id': project_id}],
                ['code', 'is', shot_code]
            ]
            fields = ['id', 'code', 'description']
            shots = self.sg.find("Shot", filters, fields)
            if shots:
                shot_id = shots[0]['id']
                print(f"Shot encontrado: {shot_id}")
                tasks = self.find_tasks_for_shot(shot_id)
                return shots[0], tasks
            else:
                print("No se encontro el shot.")
        else:
            print("No se encontro el proyecto en ShotGrid.")
        return None, None

    def find_tasks_for_shot(self, shot_id):
        print(f"Buscando tareas para el shot: {shot_id}")
        filters = [['entity', 'is', {'type': 'Shot', 'id': shot_id}]]
        fields = ['id', 'content', 'sg_status_list']
        tasks = self.sg.find("Task", filters, fields)
        print(f"Tareas encontradas: {tasks}")
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
        print(f"Nuke script file path: {file_path}")
        if file_path:
            nuke_script_name = os.path.basename(file_path)
            print(f"Nuke script name: {nuke_script_name}")
            base_name, nuke_version_number = self.parse_nuke_script_name(nuke_script_name)
            print(f"Parsed base name: {base_name}, version number: {nuke_version_number}")
            project_name = base_name.split('_')[0]
            parts = base_name.split('_')
            shot_code = '_'.join(parts[:5])
            print(f"Project name: {project_name}, shot code: {shot_code}")

            shot, tasks = self.sg_manager.find_shot_and_tasks(project_name, shot_code)
            if shot:
                for task in tasks:
                    if task['content'] == 'Comp':
                        task_url = self.sg_manager.get_task_url(task['id'])
                        print(f"  - Task: {task['content']} (Status: {task['sg_status_list']}) URL: {task_url}")
                        webbrowser.open(task_url)
            else:
                print("No se encontro el shot correspondiente en ShotGrid.")
        else:
            print("No se encontro un script activo en Nuke.")

def main():
    sg_url = os.getenv('SHOTGRID_URL')
    sg_login = os.getenv('SHOTGRID_LOGIN')
    sg_password = os.getenv('SHOTGRID_PASSWORD')

    if not sg_url or not sg_login or not sg_password:
        print("Las variables de entorno SHOTGRID_URL, SHOTGRID_LOGIN y SHOTGRID_PASSWORD deben estar configuradas.")
        return

    sg_manager = ShotGridManager(sg_url, sg_login, sg_password)
    nuke_ops = NukeOperations(sg_manager)
    nuke_ops.process_current_script()

if __name__ == "__main__":
    main()
