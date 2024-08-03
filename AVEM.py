import os
import subprocess
import json
import shutil
from flask import Flask, render_template, request, redirect, url_for

BANNER = """
      __      ________ __  __ 
     /\ \    / /  ____|  \/  |
    /  \ \  / /| |__  | \  / |
   / /\ \ \/ / |  __| | |\/| |
  / ____ \  /  | |____| |  | |
 /_/    \_\/   |______|_|  |_|
                              
"""

MENU = """
1. Create new container
2. Manage all virtual containers
3. See all logs of container
4. Open a Web UI
5. Exit
"""

CONTAINERS_FILE = 'containers.json'

app = Flask(__name__)

def load_containers():
    if os.path.exists(CONTAINERS_FILE):
        with open(CONTAINERS_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_containers(containers):
    with open(CONTAINERS_FILE, 'w') as file:
        json.dump(containers, file, indent=4)

def create_container(name):
    try:
        os.makedirs(name, exist_ok=True)
        subprocess.run(['python', '-m', 'venv', name], check=True)
        modify_activation_script(name)
        containers[name] = {'status': 'offline', 'logs': []}
        save_containers(containers)
        print(f"Container '{name}' created.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating container '{name}': {e}")

def modify_activation_script(name):
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(name, 'Scripts', 'activate.bat')
        with open(activate_script, 'a') as file:
            file.write(f'\nset PS1=[{name}] $P$G\n')
    else:  # Unix-based
        activate_script = os.path.join(name, 'bin', 'activate')
        with open(activate_script, 'a') as file:
            file.write(f'\nexport PS1="[{name}] \\u@\\h:\\w\\$ "\n')

def manage_containers():
    print("+---Container---+")
    for name in containers:
        print(f"| {name} |")
    print("+---------------+")
    choice = input("Enter container name to manage or 'back' to return: ")
    if choice in containers:
        manage_container(choice)
    elif choice.lower() == 'back':
        return
    else:
        print("Invalid choice.")

def manage_container(name):
    while True:
        print(f"\nManaging container: {name}")
        print("1. Delete container")
        print("2. Rename container")
        print("3. Toggle status (online/offline)")
        print("4. Open terminal")
        print("5. Back")
        choice = input("Enter your choice: ")
        if choice == '1':
            delete_container(name)
            break
        elif choice == '2':
            rename_container(name)
        elif choice == '3':
            toggle_status(name)
        elif choice == '4':
            open_terminal(name)
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

def delete_container(name):
    try:
        shutil.rmtree(name)
        del containers[name]
        save_containers(containers)
        print(f"Container '{name}' deleted.")
    except OSError as e:
        print(f"Error deleting container '{name}': {e}")

def rename_container(name):
    new_name = input("Enter new container name: ")
    if new_name in containers:
        print("Container with this name already exists.")
    else:
        containers[new_name] = containers.pop(name)
        os.rename(name, new_name)
        save_containers(containers)
        print(f"Container '{name}' renamed to '{new_name}'.")

def toggle_status(name):
    containers[name]['status'] = 'online' if containers[name]['status'] == 'offline' else 'offline'
    save_containers(containers)
    print(f"Container '{name}' is now {containers[name]['status']}.")

def open_terminal(name):
    log_file = os.path.join(name, 'terminal.log')
    if os.name == 'nt':  # Windows
        subprocess.run(['start', 'cmd', '/K', f'{name}\\Scripts\\activate && cd {name} && script -f {log_file}'], shell=True)
    else:  # Unix-based
        subprocess.run(['gnome-terminal', '--', 'bash', '-c', f'script -f {log_file} -c "source {name}/bin/activate; exec bash"'])

def show_logs():
    print("+---Container---+")
    for name in containers:
        print(f"| {name} |")
    print("+---------------+")
    choice = input("Enter container name to see logs or 'back' to return: ")
    if choice in containers:
        log_file = os.path.join(choice, 'terminal.log')
        if os.path.exists(log_file):
            with open(log_file, 'r') as file:
                print(file.read())
        else:
            print(f"No logs found for container '{choice}'.")
    elif choice.lower() == 'back':
        return
    else:
        print("Invalid choice.")

containers = load_containers()

@app.route('/')
def index():
    return render_template('index.html', containers=containers)

@app.route('/create', methods=['POST'])
def create():
    name = request.form['name']
    create_container(name)
    return redirect(url_for('index'))

@app.route('/manage/<name>')
def manage(name):
    return render_template('manage.html', name=name, container=containers[name])

@app.route('/delete/<name>')
def delete(name):
    delete_container(name)
    return redirect(url_for('index'))

@app.route('/rename/<name>', methods=['POST'])
def rename(name):
    new_name = request.form['new_name']
    rename_container(name)
    return redirect(url_for('index'))

@app.route('/toggle/<name>')
def toggle(name):
    toggle_status(name)
    return redirect(url_for('index'))

@app.route('/logs/<name>')
def logs(name):
    log_file = os.path.join(name, 'terminal.log')
    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            logs = file.read()
    else:
        logs = f"No logs found for container '{name}'."
    return render_template('logs.html', name=name, logs=logs)

@app.route('/open_terminal/<name>')
def open_terminal_route(name):
    open_terminal(name)
    return redirect(url_for('manage', name=name))

def main():
    print(BANNER)
    while True:
        print(MENU)
        choice = input("Enter your choice: ")
        if choice == '1':
            name = input("Enter container name: ")
            create_container(name)
        elif choice == '2':
            manage_containers()
        elif choice == '3':
            show_logs()
        elif choice == '4':
            app.run(host='0.0.0.0', port=5000)
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
