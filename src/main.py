# type: ignore
from gui import *
from tkinter import Tk


def main() -> None:
    root = Tk()
    AutomatonGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
