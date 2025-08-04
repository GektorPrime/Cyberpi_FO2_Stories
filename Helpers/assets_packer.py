import cyberpi  # type: ignore
import gc
import os


def ensure_directory_exists(filepath):
    """
    Ensure the directory for the filepath exists
    MicroPython compatible version using os.mkdir()
    """
    # Extract directory from filepath
    if '/' in filepath:
        # Find the last slash to separate path and filename
        last_slash = filepath.rfind('/')
        directory = filepath[:last_slash]
        # Split path into parts and create each level
        if directory != "":
            path_parts = directory.split('/')
            current_path = ""
            for part in path_parts:
                if part != "":  # Skip empty parts
                    if current_path == "":
                        current_path = part
                    else:
                        current_path = current_path + "/" + part
                    try:
                        os.mkdir(current_path)
                    except OSError:
                        # Directory might already exist, that's okay
                        pass


def save_all_arrays_as_single_module(filepath="fo2_stories_pixel_arrays.py"):
    """
    Alternative 1: Save all arrays to a single .py module file
    """
    current_vars = globals()
    arrays = {name: value for name, value in current_vars.items() 
              if isinstance(value, list) and name.isupper() and not name.startswith('_')}
    if not arrays:
        cyberpi.console.print("No arrays found to save!")
        return None
    try:
        ensure_directory_exists(filepath)
        with open(filepath, 'w') as f:
            f.write("# Auto-generated arrays module\n")
            f.write("# Contains " + str(len(arrays)) + " arrays\n\n")
            for i, (array_name, array_data) in enumerate(arrays.items()):
                if i > 0:
                    f.write("\n")  # Blank line between arrays
                f.write("# " + array_name + " - " + str(len(array_data)) + " elements\n")
                f.write(array_name + " = " + repr(array_data) + "\n")
            all_names = ', '.join(arrays.keys())
            f.write("all_arrays = [" + all_names + "]\n")
        cyberpi.console.print("V All " + str(len(arrays)) + " arrays saved to " + filepath)
    except Exception as e:
        cyberpi.console.print("X Error: " + str(e))
    return True


def save_all_arrays_as_single_module_dict(filepath="fo2_stories_pixel_arrays.py"):
    """
    Alternative 2: Creates a .py file containing only a single dictionary named <filename>_all with arrays
    """
    try:
        ensure_directory_exists(filepath)
        filename = filepath.split("/")[-1]
        dict_name = (filename[:-3] if filename.endswith(".py") else filename) + "_all"
        arrays = {
            name: val for name, val in globals().items()
            if isinstance(val, list) and name.isupper() and not name.startswith('_')
        }
        with open(filepath, "w") as f:
            f.write(dict_name + " = {\n")
            for name, val in arrays.items():
                key = name.lower()
                f.write("    \"" + key + "\": [")
                for i, v in enumerate(val):
                    if i > 0:
                        f.write(", ")
                    f.write(str(v))
                f.write("],\n")
            f.write("}\n")
        cyberpi.console.print("V Saved " + str(len(arrays)) + " arrays to " + filepath)
    except Exception as e:
        cyberpi.console.print("X Error: " + str(e))
    return True


def save_arrays_as_binary(base_path=""):
    """
    Alternative 3: Save arrays as binary files
    """
    current_vars = globals()
    arrays = {name: value for name, value in current_vars.items() 
              if isinstance(value, list) and name.isupper() and not name.startswith('_')}
    cyberpi.console.print("Saving " + str(len(arrays)) + " arrays as binary files:")
    # Ensure base path ends with '/' if not empty and doesn't already end with '/'
    if base_path != "" and not base_path.endswith('/'):
        base_path = base_path + "/"
    for array_name, array_data in arrays.items():
        try:
            filename = array_name.lower() + ".bin"
            filepath = base_path + filename
            # Ensure the directory exists
            if base_path != "":
                ensure_directory_exists(filepath)
            with open(filepath, 'wb') as f:
                # Write array length first (4 bytes)
                length = len(array_data)
                f.write(length.to_bytes(4, 'little'))
                # Write each element (assuming 4-byte integers)
                for value in array_data:
                    f.write(value.to_bytes(4, 'little'))
            cyberpi.console.print("V " + array_name + " saved to " + filepath + " (" + str(len(array_data)) + " elements)")
            print("V " + array_name + " saved to " + filepath + " (" + str(len(array_data)) + " elements)")
        except Exception as e:
            print("X Error saving " + array_name + ": " + str(e))
            cyberpi.console.print("X Error saving " + array_name + ": " + str(e))
    return True


def load_binary_array(filepath):
    """
    Helper function to load binary array files
    """
    try:
        with open(filepath, 'rb') as f:
            # Read array length
            length_bytes = f.read(4)
            if len(length_bytes) != 4:
                return None
            length = int.from_bytes(length_bytes, 'little')
            # Read array elements
            array = []
            for _ in range(length):
                value_bytes = f.read(4)
                if len(value_bytes) != 4:
                    return None
                value = int.from_bytes(value_bytes, 'little')
                array.append(value)
            return array
    except Exception as e:
        cyberpi.console.print("Error loading " + filepath + ": " + str(e))
        return None


def demonstrate_usage():
    """
    Shows how to use the saved arrays with path examples
    """
    print("\nUsage examples:")
    print("=" * 15)
    print("# To use single module with all arrays:")
    print("save_all_arrays_as_single_module('data/my_arrays.py')")
    print("import sys")
    print("sys.path.append('data')")
    print("import my_arrays")
    print("data1 = my_arrays.ADV_PA_FRONT_1")
    print("")
    print("# To save binary arrays in subfolder:")
    print("save_arrays_as_binary('data/arrays')")
    print("")
    print("# To load binary array with full path:")
    print("data = load_binary_array('data/arrays/adv_pa_front_1.bin')")


# Place arrays here:
#-----------------------------------------------------
ADV_PA_FRONT_2 = []
#-----------------------------------------------------

cyberpi.screen.disable_autorender()
cyberpi.display.set_brush(0, 128, 0)
cyberpi.console.print("Store pixel arrays\n")

# Choose your preferred method:
cyberpi.console.println("A: to *.py")
cyberpi.console.println("B: to *.bin's")

finished = False
while not finished:
    if cyberpi.controller.is_press('a'):   
        cyberpi.console.print("\nSaving as single module:")
        # Example with path - you can modify this as needed
        if save_all_arrays_as_single_module_dict("fo2_stories_assets/pixel_array_modules/adv_power_armor.py"):
            finished = True
    elif cyberpi.controller.is_press('b'): 
        cyberpi.console.print("\nSaving as binary files:")
        # Example with path - you can modify this as needed
        if save_arrays_as_binary("fo2_stories_assets/pixel_arrays"):
            finished = True
    
# Clean up memory
gc.collect()
print("Finished")
