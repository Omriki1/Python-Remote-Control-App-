import socket
import pickle
import threading
from zlib import decompress
import pygame
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener, Key
import rsa
import pyaes

class InputHandler:
    def __init__(self, connection, aes_key):
        self.connection = connection
        self.aes = pyaes.AESModeOfOperationCTR(aes_key)
        self.special_keys_map = {
            Key.alt_l: 'alt',
            Key.alt_r: 'alt gr',
            Key.ctrl_l: 'ctrl',
            Key.ctrl_r: 'right ctrl',
            Key.shift_l: 'shift',
            Key.shift_r: 'right shift',
            Key.enter: 'enter',
            Key.esc: 'esc',
            Key.cmd: 'win',
            Key.cmd_r: 'right win',
            Key.space: 'space',
            Key.backspace: 'backspace',
            Key.delete: 'delete',
        }

    def on_move(self, x, y):
        data = ('move', (x, y))
        self.send_data(data)

    def on_click(self, x, y, button, pressed):
        data = ('click', (x, y, str(button), pressed))
        self.send_data(data)

    def on_scroll(self, x, y, dx, dy):
        data = ('scroll', (x, y, dx, dy))
        self.send_data(data)

    def on_press(self, key):
        key_data = self.process_key(key)
        data = ('keypress', key_data)
        self.send_data(data)

    def on_release(self, key):
        key_data = self.process_key(key)
        data = ('keyrelease', key_data)
        self.send_data(data)

    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        encrypted_data = self.aes.encrypt(serialized_data)
        self.connection.sendall(encrypted_data)

    def process_key(self, key):
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            elif key in self.special_keys_map:
                return self.special_keys_map[key]
            else:
                return key.name
        except AttributeError:
            return None

class ScreenDisplay:
    def __init__(self, connection, aes_key, width=1920, height=1080):
        self.connection = connection
        self.aes = pyaes.AESModeOfOperationCTR(aes_key)
        self.width = width
        self.height = height

    def display_screen(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        clock = pygame.time.Clock()
        watching = True
        try:
            while watching:
                size_len = int.from_bytes(self.connection.recv(1), byteorder='big')
                size = int.from_bytes(self.connection.recv(size_len), byteorder='big')
                encrypted_pixels = self.recvall(size)
                pixels = self.aes.decrypt(encrypted_pixels)
                pixels = decompress(pixels)
                img = pygame.image.fromstring(pixels, (self.width, self.height), 'RGB')
                img = pygame.transform.scale(img, (self.width, self.height))
                screen.blit(img, (0, 0))
                pygame.display.flip()
                clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        watching = False
        finally:
            pygame.quit()

    def recvall(self, length):
        buf = b''
        while len(buf) < length:
            data = self.connection.recv(length - len(buf))
            if not data:
                return data
            buf += data
        return buf

class RemoteControlClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.control_sock = socket.socket()
        self.screen_sock = socket.socket()
        self.aes = None  # Initialize the AES attribute
        self.lock = threading.Lock()

    def start(self):
        self.control_sock.connect((self.host, self.port + 1))
        self.screen_sock.connect((self.host, self.port))

        # Receive server's public key and send encrypted AES key
        public_key_data = self.screen_sock.recv(2048)
        public_key = rsa.PublicKey.load_pkcs1(public_key_data, format='DER')

        aes_key = b'This_key_for_demo_purposes_only!'
        encrypted_aes_key = rsa.encrypt(aes_key, public_key)
        self.screen_sock.send(encrypted_aes_key)
        self.control_sock.send(encrypted_aes_key)

        # Set AES key for encryption/decryption
        self.aes = pyaes.AESModeOfOperationCTR(aes_key)

        mouse_listener = MouseListener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
        keyboard_listener = KeyboardListener(on_press=self.on_press, on_release=self.on_release)
        screen_thread = threading.Thread(target=self.display_screen, args=(aes_key,))

        mouse_listener.start()
        keyboard_listener.start()
        screen_thread.start()

        mouse_listener.join()
        keyboard_listener.join()
        screen_thread.join()

    def display_screen(self, aes_key):
        screen_display = ScreenDisplay(self.screen_sock, aes_key)
        screen_display.display_screen()

    def on_move(self, x, y):
        self.send_data(('move', (x, y)))

    def on_click(self, x, y, button, pressed):
        self.send_data(('click', (x, y, str(button), pressed)))

    def on_scroll(self, x, y, dx, dy):
        self.send_data(('scroll', (x, y, dx, dy)))

    def on_press(self, key):
        key_data = self.process_key(key)
        self.send_data(('keypress', key_data))

    def on_release(self, key):
        key_data = self.process_key(key)
        self.send_data(('keyrelease', key_data))

    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        encrypted_data = self.aes.encrypt(serialized_data)
        self.control_sock.sendall(encrypted_data)

    def process_key(self, key):
        special_keys_map = {
            Key.alt_l: 'alt',
            Key.alt_r: 'alt gr',
            Key.ctrl_l: 'ctrl',
            Key.ctrl_r: 'right ctrl',
            Key.shift_l: 'shift',
            Key.shift_r: 'right shift',
            Key.enter: 'enter',
            Key.esc: 'esc',
            Key.cmd: 'win',
            Key.cmd_r: 'right win',
            Key.space: 'space',
            Key.backspace: 'backspace',
            Key.delete: 'delete',
        }
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            elif key in special_keys_map:
                return special_keys_map[key]
            else:
                return key.name
        except AttributeError:
            return None
