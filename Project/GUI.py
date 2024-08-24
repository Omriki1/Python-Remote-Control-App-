import sys
import customtkinter as CTk
import threading
import ipaddress
from PIL import Image
import CentralApplication
import Peer


class ConnectWindowHelper(CTk.CTkToplevel):
    def __init__(self, conn, main_app):
        super().__init__()
        self.geometry("400x300")
        self.title("Connect window helper")
        self.protocol("WM_DELETE_WINDOW", self.close_connection)
        self.main_app = main_app
        self.conn = conn

    def close_connection(self):
        if self.conn:
            self.conn.shutdown_system()
        self.main_app.exit_application()


class HostWindow(CTk.CTkToplevel):
    def __init__(self, main_app):
        super().__init__()
        self.error_label = CTk.CTkLabel(self, text="Port number is wrong", width=30, height=20,
                                        font=('Comic Sans MS', 18), text_color="#FF0000")
        self.geometry("600x400")
        self.title("Host Screen")
        self.main_app = main_app

        self.host_window_text = CTk.CTkLabel(self, text="Host Menu\nEnter Info", width=30, height=20,
                                             font=('Comic Sans MS', 36))
        self.host_window_text.place(relx=0.3, rely=0.1)

        self.port_entry = CTk.CTkEntry(self, placeholder_text="Enter port", corner_radius=36)
        self.port_entry.place(relx=0.35, rely=0.45)

        self.host_button_submit = CTk.CTkButton(self, text="Host", hover_color='#C0C0C0',
                                                fg_color='#06CDFF', font=('Comic Sans MS', 24), corner_radius=36,
                                                width=120, height=80, command=self.start_server)
        self.host_button_submit.place(relx=0.35, rely=0.65)

    def check_port(self, port):
        if port == "":
            return False
        if not port.isnumeric():
            self.error_label.place(relx=0.4, rely=0.3)
            return False
        return True

    def start_server(self):
        self.port = self.port_entry.get()
        if self.check_port(self.port):
            self.Central = CentralApplication.ScreenShareServer(int(self.port))
            self.server_thread = threading.Thread(target=self.Central.start)
            self.server_thread.start()
            self.destroy()


class ConnectWindow(CTk.CTkToplevel):
    def __init__(self, main_app):
        super().__init__()
        self.geometry("600x400")
        self.title = ("Connect Screen")
        self.connect_window_helper = None
        self.main_app = main_app
        self.conn = None

        self.connect_welcome_text = CTk.CTkLabel(self, text="Enter Info ", width=30, height=20,
                                                 font=('Comic Sans MS', 36))
        self.connect_welcome_text.place(relx=0.4, rely=0.1)

        self.ip_entry = CTk.CTkEntry(self, placeholder_text="Enter IP", corner_radius=36)
        self.ip_entry.place(relx=0.075, rely=0.3)

        self.port_entry = CTk.CTkEntry(self, placeholder_text="Port", corner_radius=36)
        self.port_entry.place(relx=0.075, rely=0.5)

        self.connect_button_submit = CTk.CTkButton(self, text_color="#000000", text="Connect", hover_color='#C0C0C0',
                                                   fg_color='#06CDFF', font=('Comic Sans MS', 24), corner_radius=36,
                                                   width=120, height=80, command=self.get_connect_window_entry)
        self.connect_button_submit.place(relx=0.7, rely=0.4)

    def check_submited_data(self, data):
        if "" in data:
            self.error_label = CTk.CTkLabel(self, text="One or more fields are empty", width=30, height=20,
                                            font=('Comic Sans MS', 18), text_color="#FF0000")
            self.error_label.place(relx=0.4, rely=0.3)
            return False
        if data[0] != "":
            try:
                ip_obj = ipaddress.ip_address(data[0])
            except ValueError:
                self.error_label = CTk.CTkLabel(self, text="      IP address is wrong               ",
                                                width=30, height=20,
                                                font=('Comic Sans MS', 18), text_color="#FF0000")
                self.error_label.place(relx=0.4, rely=0.3)
                return False
        if data[1] != "":
            if not data[1].isnumeric():
                self.error_label = CTk.CTkLabel(self, text="      Port number is wrong              ",
                                                width=30, height=20,
                                                font=('Comic Sans MS', 18), text_color="#FF0000")
                self.error_label.place(relx=0.4, rely=0.3)
                return False
        self.error_label = CTk.CTkLabel(self, text="      Good trying to connect               ",
                                        width=30, height=20,
                                        font=('Comic Sans MS', 18), text_color="#FF0000")
        self.error_label.place(relx=0.4, rely=0.3)
        return True

    def connect(self, data):
        try:
            self.conn = Peer.RemoteControlClient(data[0], int(data[1]))
            self.client_thread = threading.Thread(target=self.conn.start)
            self.client_thread.start()
            self.connect_button_submit.destroy()
            self.destroy()
        except Exception as e:
            print(f"Error: {e}")

    def get_connect_window_entry(self):
        data = self.ip_entry.get(), self.port_entry.get()
        if self.check_submited_data(data):
            self.connect(data)


class Graphic(CTk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("860x600")
        self.title("ConCtrl")

        self.welcome_text = CTk.CTkLabel(self, text="Choose ", width=30, height=20, font=('Comic Sans MS', 36))
        self.welcome_text.place(relx=0.4, rely=0.1)

        self.connect_button = CTk.CTkButton(self, text_color="#000000", text="Connect", hover_color='#C0C0C0',
                                            fg_color='#FFD700', font=('Comic Sans MS', 24), corner_radius=36,
                                            command=self.connect_button_click)
        self.connect_button.place(relx=0.2, rely=0.6)

        self.host_button = CTk.CTkButton(self, text_color="#000000", text="Host", hover_color='#C0C0C0',
                                         fg_color='#FFD700', font=('Comic Sans MS', 24), corner_radius=36,
                                         command=self.host_button_click)
        self.host_button.place(relx=0.6, rely=0.6)

        self.connect_window = None
        self.host_window = None
        self.server_thread = None

    def exit_application(self):
        # Perform any necessary cleanup
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.server.stop_all_clients()
        self.quit()  # Quit the mainloop
        self.destroy()  # Destroy all widgets
        exit()

    def connect_button_click(self):
        if self.connect_window is None or not self.connect_window.winfo_exists():
            self.connect_window = ConnectWindow(self)  # create window if its None or destroyed
        else:
            self.connect_window.focus()  # if window exists focus it
        self.state(newstate='iconic')

    def host_button_click(self):
        if self.host_window is None or not self.host_window.winfo_exists():
            self.host_window = HostWindow(self)  # create window if its None or destroyed
        else:
            self.host_window.focus()  # if window exists focus it
        self.state(newstate='iconic')

