import os

def print_tree(startpath, ignore_dirs=None, level=0, max_depth=3):
    if ignore_dirs is None:
        ignore_dirs = {"venv", "__pycache__", ".git"}

    for item in sorted(os.listdir(startpath)):
        path = os.path.join(startpath, item)
        if os.path.isdir(path):
            if item not in ignore_dirs and level < max_depth:
                print("    " * level + f"📁 {item}")
                print_tree(path, ignore_dirs, level + 1, max_depth)
        else:
            print("    " * level + f"📄 {item}")

print_tree("./design-projects/distributed-tracing-with-open-telemetry", ignore_dirs={"venv", "__pycache__", ".git"}, max_depth=3)
