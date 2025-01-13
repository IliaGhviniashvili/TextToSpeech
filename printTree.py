from pathlib import Path

def print_directory_tree(directory, indent=""):
    directory = Path(directory)
    
    # Print the root directory
    print(f"{indent}📁 {directory.name}/")
    indent += "  "
    
    # Sort entries: directories first, then files
    entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    
    for entry in entries:
        if entry.is_dir():
            print_directory_tree(entry, indent)
        else:
            print(f"{indent}📄 {entry.name}")

# Example usage
print("\nDirectory Structure:")
print_directory_tree("C:/Users/Lingwing/Desktop/splitSentencePy")