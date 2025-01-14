from quart import Blueprint
from core.lifecyclehooks import apply_lifecycle_hooks
import os
import importlib.util

def find_blueprints(folder) -> list[Blueprint]:
    """
    Scans a folder for Python files and dynamically retrieves Quart blueprint objects 
    named 'bp' from each file.

    This function explores the specified folder, identifies all Python files, and 
    dynamically loads each as a module. It inspects each module to check if a 
    blueprint variable named 'bp' is defined. If the blueprint is found, it adds 
    the blueprint object to a list. This allows the function to automatically 
    detect and include new blueprints as they are added to the folder without 
    requiring manual updates.

    Args:
        folder (str): The path to the folder containing Python files with Quart 
                      blueprints.

    Returns:
        list[Blueprint]: A list of Quart blueprint objects found in the folder. 
                         Each blueprint corresponds to a variable named 'bp' in 
                         one of the Python files.

    Example:
        If the folder contains files like:
        
        - `user.py` with a blueprint `bp`
        - `product.py` with a blueprint `bp`
        
        Then calling `find_blueprints('api')` will return a list of blueprints 
        from `user.py` and `product.py`.

    Notes:
        - The function only checks Python files (i.e., files ending with `.py`).
        - The function expects each file to define a blueprint using the variable 
          name 'bp'. Blueprints with different variable names won't be included.
        - Dynamically importing each module allows for flexibility in adding new 
          blueprints without modifying this function.
    """
    blueprints = []
    
    # Iterate over all files in the specified folder
    for filename in os.listdir(folder):
        # We are only interested in Python files
        if filename.endswith(".py"):
            filepath = os.path.join(folder, filename)
            
            # Load the module
            module_name = filename[:-3]  # Remove the .py extension
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if 'bp' exists in the module
            if hasattr(module, 'bp'):
                blueprints.append(module.bp)

    return blueprints



def get_blueprints() -> list[Blueprint]:
    """
    Retrieves a list of Quart blueprint objects, applying lifecycle hooks to each blueprint.
    
    This function consolidates the application's route blueprints into a list, allowing 
    for the dynamic application of lifecycle hooks before the blueprints are registered
    with the Quart application. The lifecycle hooks augment the functionality of the 
    blueprints by adding pre- or post-processing behavior.
    
    Returns:
        list[Blueprint]: A list of Quart blueprint objects, each modified with the 
        appropriate lifecycle hooks.
    """    
    updated_blueprints = []
    
    # Specify the folder containing Quart blueprints
    blueprint_folder = "api"
    blueprint_list = find_blueprints(blueprint_folder)

    for blueprint in blueprint_list:
        updated_blueprints.append(apply_lifecycle_hooks(blueprint))

    return updated_blueprints