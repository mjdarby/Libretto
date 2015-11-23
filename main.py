from tkinter import *
from tkinter.ttk import *

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.buildWidgets()

    def buildWidgets(self):
        scrollbar = Scrollbar(self)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.text_entry = Text(self, yscrollcommand=scrollbar.set)
        self.text_entry.pack(side="top")

        self.quit = Button(self,
                           text="Quit",
                           command=root.destroy)
        self.quit.pack(side="bottom")


if __name__ == "__main__":
    root = Tk()
    app = Application(master=root)
    app.master.title("Libretto")
    app.mainloop()
