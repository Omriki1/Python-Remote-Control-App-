import socket
import pickle
import threading
from zlib import decompress, compress

import keyboard
import pygame
from pynput.keyboard import Key
import pyautogui
from mss import mss

import rsa
import pyaes

class InputHandler:
    def __init__(self, connection, aes_key):
        self.connection = connection
        self.aes = pyaes.AESModeOfOperationCTR(aes_key)
        self.special_keys_map = {
            'alt': Key.alt_l,
            'alt gr': Key.alt_r,
            'ctrl': Key.ctrl_l,
            'right ctrl': Key.ctrl_r,
            'shift': Key.shift_l,
            'right shift': Key.shift_r,
            'enter': Key.enter,
            'esc': Key.esc,
            'win': Key.cmd,
            'right win': Key.cmd_r,
            'space': Key.space,
            'backspace': Key.backspace,
            'delete': Key.delete,
        }

    def handle_action(self, action, value):
        if action == 'move':
            x, y = value
            pyautogui.moveTo(x, y)
        elif action == 'click':
            x, y, button, pressed = value
            btn = 'left' if button == 'Button.left' else 'right' if button == 'Button.right' else 'middle'
            if pressed:
                pyautogui.mouseDown(x, y, button=btn)
            else:
                pyautogui.mouseUp(x, y, button=btn)
        elif action == 'scroll':
            x, y, dx, dy = value
            scroll_amount = dy * 50
            pyautogui.scroll(scroll_amount, x, y)
        elif action in ('keypress', 'keyrelease'):
            key = self.process_key(value)
            if action == 'keypress':
                keyboard.press(value)
            else:
                keyboard.release(value)

    def process_key(self, key):
        return self.special_keys_map.get(key, key)

    def receive_actions(self):
        while True:
            try:
                data = self.connection.recv(4096)
                if not data:
                    break

                decrypted_data = self.aes.decrypt(data)
                action, value = pickle.loads(decrypted_data)
                self.handle_action(action, value)
            except pickle.UnpicklingError:
                print("Received corrupt data, waiting for next packet")
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                break

class ScreenShareServer:
    def __init__(self, port=5000):
        self.host = '0.0.0.0'
        self.port = port
        self.clients = []
        self.lock = threading.Lock()
        self.public_key, self.private_key = rsa.newkeys(512)

    def start(self):
        control_thread = threading.Thread(target=self.receive_input)
        screen_thread = threading.Thread(target=self.share_screen)

        control_thread.start()
        screen_thread.start()

        control_thread.join()
        screen_thread.join()

    def share_screen(self):
        sock = socket.socket()
        sock.bind((self.host, self.port))
        sock.listen(5)
        print(f"[LISTENING] Screen sharing on port {self.port}")

        while True:
            conn, addr = sock.accept()
            print(f"[NEW CONNECTION] {addr} connected.")
            self.clients.append(conn)
            conn.send(self.public_key.save_pkcs1(format='DER'))  # Send public key to client
            aes_key_encrypted = conn.recv(1024)  # Receive encrypted AES key
            aes_key = rsa.decrypt(aes_key_encrypted, self.private_key)
            client_thread = threading.Thread(target=self.send_screenshots, args=(conn, aes_key))
            client_thread.start()

    def send_screenshots(self, conn, aes_key):
        aes = pyaes.AESModeOfOperationCTR(aes_key)
        with mss() as sct:
            rect = {'top': 0, 'left': 0, 'width': 1920, 'height': 1080}
            while True:
                img = sct.grab(rect)
                pixels = compress(img.rgb, 6)
                encrypted_pixels = aes.encrypt(pixels)
                size = len(encrypted_pixels)
                size_len = (size.bit_length() + 7) // 8
                conn.send(bytes([size_len]))
                size_bytes = size.to_bytes(size_len, 'big')
                conn.send(size_bytes)
                conn.sendall(encrypted_pixels)

    def receive_input(self):
        sock = socket.socket()
        sock.bind((self.host, self.port + 1))
        sock.listen(5)
        print(f"[LISTENING] Input receiving on port {self.port + 1}")

        while True:
            conn, addr = sock.accept()
            print(f"[NEW CONNECTION] {addr} connected.")
            aes_key_encrypted = conn.recv(1024)  # Receive encrypted AES key
            aes_key = rsa.decrypt(aes_key_encrypted, self.private_key)
            input_handler = InputHandler(conn, aes_key)
            client_thread = threading.Thread(target=input_handler.receive_actions)
            client_thread.start()
