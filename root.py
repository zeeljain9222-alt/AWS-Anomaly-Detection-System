import os

IGNORE_FOLDERS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".ipynb_checkpoints"
}

def print_structure(path, prefix=""):
    items = []

    for item in os.listdir(path):
        if item not in IGNORE_FOLDERS:
            items.append(item)

    items.sort()

    for index, item in enumerate(items):
        full_path = os.path.join(path, item)

        is_last = index == len(items) - 1

        connector = "└── " if is_last else "├── "

        print(prefix + connector + item)

        if os.path.isdir(full_path):
            extension = "    " if is_last else "│   "
            print_structure(full_path, prefix + extension)


print("📁 SIH PROJECT STRUCTURE\n")
print_structure(".")