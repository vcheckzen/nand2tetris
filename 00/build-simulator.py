import os
import subprocess
import shutil
from pathlib import Path

INSTALL_DIR = Path("InstallDir")
BIN_LIB_DIR = INSTALL_DIR / "bin" / "lib"
BIN_CLASSES_DIR = INSTALL_DIR / "bin" / "classes"
BUILTIN_CHIPS_DIR = INSTALL_DIR / "builtInChips"
BUILTIN_VM_CODE_DIR = INSTALL_DIR / "builtInVMCode"

# Ensure destination directories exist
BIN_LIB_DIR.mkdir(parents=True, exist_ok=True)
BIN_CLASSES_DIR.mkdir(parents=True, exist_ok=True)
BUILTIN_CHIPS_DIR.mkdir(parents=True, exist_ok=True)
BUILTIN_VM_CODE_DIR.mkdir(parents=True, exist_ok=True)

# JAR package sources: name -> jar name
jar_packages = {
    "HackPackageSource": "Hack.jar",
    "HackGUIPackageSource": "HackGUI.jar",
    "CompilersPackageSource": "Compilers.jar",
    "SimulatorsPackageSource": "Simulators.jar",
    "SimulatorsGUIPackageSource": "SimulatorsGUI.jar",
}

# Non-jar packages: name -> (destination, exclude_from_cp)
other_packages = {
    "BuiltInChipsSource": (BUILTIN_CHIPS_DIR, False),
    "BuiltInVMCodeSource": (BUILTIN_VM_CODE_DIR, True),  # Exclude from classpath
    "MainClassesSource": (BIN_CLASSES_DIR, False),
}

def compile_java_sources(source_dir: Path, cp: str = ""):
    java_files = [str(p) for p in source_dir.rglob("*.java")]
    if not java_files:
        print(f"No Java files found in {source_dir}")
        return False
    cmd = ["javac", "-nowarn", "-Xlint:none"]
    if cp:
        cmd += ["-cp", cp]
    cmd += java_files
    print(f"Compiling {source_dir}...")
    return subprocess.run(cmd).returncode == 0

def create_jar(source_dir: Path, jar_name: str, output_dir: Path):
    jar_path = output_dir / jar_name
    cmd = ["jar", "cf", str(jar_path), "-C", str(source_dir), "."]
    print(f"Creating JAR {jar_path}...")
    return subprocess.run(cmd).returncode == 0

# Build full classpath
all_dirs = [Path(p) for p in jar_packages] + [
    Path(p) for p, (_, exclude) in other_packages.items() if not exclude
]
full_classpath = ";".join(str(d) for d in all_dirs)

# Process JAR packages
for src, jar_name in jar_packages.items():
    src_path = Path(src)
    if not compile_java_sources(src_path, cp=full_classpath):
        print(f"Failed to compile {src}")
        continue
    if not create_jar(src_path, jar_name, BIN_LIB_DIR):
        print(f"Failed to create JAR for {src}")
        continue

# Process other packages
for src, (dest, exclude) in other_packages.items():
    src_path = Path(src)
    if src == "MainClassesSource":
        partial_cp_dirs = [Path(p) for p in jar_packages] + [
            Path(p) for p, (_, ex) in other_packages.items() if not ex and p != "BuiltInVMCodeSource"
        ]
        classpath = ";".join(str(d) for d in partial_cp_dirs)
    else:
        classpath = full_classpath

    if not compile_java_sources(src_path, cp=classpath):
        print(f"Failed to compile {src}")
        continue

    print(f"Copying class files from {src} to {dest}...")
    for class_file in src_path.rglob("*.class"):
        rel_path = class_file.relative_to(src_path)
        target_path = dest / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(class_file, target_path)

print("Build completed.")
