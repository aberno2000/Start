from importlib import import_module


GREEN = "\033[1m\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m\033[1m"


def check_and_install_packages(packages_list: list) -> None:
    """
    Check for the presence of packages in the given list and install them if not found.

    Args:
    - packages_list (list): List of packages to check and install if not found

    Returns:
    - None
    """
    for package in packages_list:
        try:
            import_module(package)  # Try to import the package
            # print(f"{BLUE}{package}{GREEN} is already installed{RESET}")
        except ImportError:
            # If the package is not found, attempt to install it
            print(f"{BLUE}{package}{RESET} is not installed. Installing...")
            try:
                from subprocess import check_call

                check_call(["pip", "install", package])
                print(f"{BLUE}{package}{GREEN} has been successfully installed{RESET}")
            except Exception as e:
                print(f"{RED}Error installing {package}: {str(e)}{RESET}")
