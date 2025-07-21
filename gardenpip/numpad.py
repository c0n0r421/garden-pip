from kivy.uix.modalview import ModalView
from kivy.properties import ObjectProperty
from kivy.metrics import dp


class Numpad(ModalView):
    """Simple numeric keypad for entering floating point values."""

    target = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(240), dp(320))
        self.auto_dismiss = False

    def key_press(self, key: str) -> None:
        if not self.target:
            return
        if key == "Enter":
            self.dismiss()
        elif key == "\u2190":  # left arrow/backspace
            self.target.text = self.target.text[:-1]
        else:
            self.target.text += key

