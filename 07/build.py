import os


def filter_vm_files(root_dir):
    vm_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.vm'):
                vm_files.append(os.path.join(dirpath, filename))
    return vm_files


# Example usage
root_directory = '.'
vm_files = filter_vm_files(root_directory)
for f in vm_files:
    os.system(f"python vmtranslator.py {f}")
