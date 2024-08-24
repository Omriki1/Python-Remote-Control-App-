import GUI

try:
    from GUI import Graphic
    graphic_module_exist = True
except (ModuleNotFoundError, ImportError):
    graphic_module_exist = False

try:
    from CentralApplication import ScreenShareServer
    central_module_exist = True
except (ModuleNotFoundError, ImportError):
    central_module_exist = False

try:
    from Peer import RemoteControlClient
    peer_module_exist = True
except (ModuleNotFoundError, ImportError):
    peer_module_exist = False

def _create_help_message() -> str:
    """
    Creates a message indicating which modules failed to import.

    :return: A string message indicating missing modules.
    """
    msg = ''
    if not graphic_module_exist:
        msg += 'You miss the graphic_module\n'
    if not peer_module_exist:
        msg += 'You miss the peer module\n'
    if not central_module_exist:
        msg += 'You miss the central_module\n'
    return msg

def main():
    """
    Main function to start the GUI application if all required modules are available.
    """
    if central_module_exist and graphic_module_exist and peer_module_exist:
        start = GUI.Graphic()
        start.mainloop()
    else:
        print(_create_help_message())

if __name__ == "__main__":
    main()
