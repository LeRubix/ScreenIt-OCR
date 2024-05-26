import tkinter as tk
from tkinter import scrolledtext, ttk
import pyautogui
import time
import threading
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from googletrans import Translator

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

translator = Translator()

class ScreenTranslateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ScreenTranslate OCR")
        root.iconbitmap("assets/icon.ico")

        self.root.configure(bg='#2e2e2e')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', background='#555555', foreground='#ffffff', borderwidth=1, focusthickness=3, focuscolor='none')
        style.configure('TLabel', background='#2e2e2e', foreground='#ffffff')
        style.configure('TFrame', background='#2e2e2e')
        style.configure('TScrolledText', background='#2e2e2e', foreground='#ffffff')
        style.configure('TSeparator', background='#444444')

        font_family = "Arial Rounded MT"
        font_size = 12

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, bg='#1e1e1e', fg='#ffffff', insertbackground='white', font=(font_family, font_size))
        self.text_area.pack(padx=10, pady=10)

        self.start_button = ttk.Button(root, text="Start", command=self.start_translation)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_translation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.running = False
        self.region = None

    def capture_screen(self, region):
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save("assets/screenshot.png")

    def preprocess_image(self, image_path):
        image = Image.open(image_path)
        image = image.convert('L')
        image = ImageOps.invert(image)
        image = image.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)
        image.save("assets/preprocessed_screenshot.png")
        return "assets/preprocessed_screenshot.png"

    def extract_text(self, image_path):
        preprocessed_image_path = self.preprocess_image(image_path)
        text = pytesseract.image_to_string(Image.open(preprocessed_image_path), lang='rus')
        print(f"Extracted Text: {text}")
        return text

    def translate_text(self, text):
        try:
            if ':' in text:
                prefix, text_to_translate = text.split(':', 1)
            else:
                text_to_translate = text

            translation = translator.translate(text_to_translate.strip(), src='ru', dest='en')
            return translation.text
        except Exception as e:
            print(f"Translation Error: {e}")
            return ""

    def select_area(self):
        self.region = None
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes("-fullscreen", True)
        self.selection_window.attributes("-alpha", 0.3)
        self.selection_window.configure(background='gray')
        self.selection_window.bind("<Button-1>", self.on_button_press)
        self.selection_window.bind("<B1-Motion>", self.on_mouse_drag)
        self.selection_window.bind("<ButtonRelease-1>", self.on_button_release)

        self.start_x = None
        self.start_y = None
        self.rect = None

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = tk.Canvas(self.selection_window, cursor="cross", bg='gray')
        self.rect.place(x=self.start_x, y=self.start_y)

    def on_mouse_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.rect.place_forget()
        self.rect = tk.Canvas(self.selection_window, cursor="cross", bg='gray')
        self.rect.place(x=min(self.start_x, cur_x), y=min(self.start_y, cur_y), width=abs(cur_x - self.start_x), height=abs(cur_y - self.start_y))

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        self.region = (min(self.start_x, end_x), min(self.start_y, end_y), abs(end_x - self.start_x), abs(end_y - self.start_y))
        self.selection_window.destroy()

    def start_translation(self):
        self.select_area()
        self.root.wait_window(self.selection_window)
        if self.region:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.translation_thread = threading.Thread(target=self.translation_loop)
            self.translation_thread.start()

    def stop_translation(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.translation_thread.join()

    def translation_loop(self):
        while self.running:
            self.capture_screen(self.region)
            text = self.extract_text("assets/screenshot.png")
            if text.strip():
                translated_text = self.translate_text(text)
                self.text_area.insert(tk.END, "----\n" + translated_text + "\n----\n\n")
                self.text_area.see(tk.END)
            time.sleep(5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenTranslateApp(root)
    root.mainloop()
