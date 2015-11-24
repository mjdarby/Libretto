import re
from tkinter import *
from tkinter.ttk import *

class ModifiedMixin:
    '''
    Class to allow a Tkinter Text widget to notice when it's modified.

    To use this mixin, subclass from Tkinter.Text and the mixin, then write
    an __init__() method for the new class that calls _init().

    Then override the beenModified() method to implement the behavior that
    you want to happen when the Text is modified.
    '''

    def _init(self):
        '''
        Prepare the Text for modification notification.
        '''

        # Clear the modified flag, as a side effect this also gives the
        # instance a _resetting_modified_flag attribute.
        self.clearModifiedFlag()

        # Bind the <<Modified>> virtual event to the internal callback.
        self.bind('<<Modified>>', self._beenModified)

    def _beenModified(self, event=None):
        '''
        Call the user callback. Clear the Tk 'modified' variable of the Text.
        '''

        # If this is being called recursively as a result of the call to
        # clearModifiedFlag() immediately below, then we do nothing.
        if self._resetting_modified_flag: return

        # Clear the Tk 'modified' variable.
        self.clearModifiedFlag()

        # Call the user-defined callback.
        self.beenModified(event)

    def beenModified(self, event=None):
        '''
        Override this method in your class to do what you want when the Text
        is modified.
        '''
        pass

    def clearModifiedFlag(self):
        '''
        Clear the Tk 'modified' variable of the Text.

        Uses the _resetting_modified_flag attribute as a sentinel against
        triggering _beenModified() recursively when setting 'modified' to 0.
        '''

        # Set the sentinel.
        self._resetting_modified_flag = True

        try:

            # Set 'modified' to 0.  This will also trigger the <<Modified>>
            # virtual event which is why we need the sentinel.
            self.tk.call(self._w, 'edit', 'modified', 0)

        finally:
            # Clean the sentinel.
            self._resetting_modified_flag = False

class MyFace(ModifiedMixin, Text):
    def __init__(self, *a, **b):
        # Create self as a Text.
        Text.__init__(self, *a, **b)

        # Initialize the ModifiedMixin.
        self._init()

class WritingFrame(Frame):
    def __init__(self, master=None, callback=lambda e: print(e)):
        Frame.__init__(self, master)
        self.callback = callback
        self.pack()
        self.buildWidgets()

    def buildWidgets(self):
        self.scrollbar = Scrollbar(self)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.text_entry = MyFace(self, yscrollcommand=self.scrollbar.set, width=60, height=40)
        self.scrollbar.config(command=self.text_entry.yview)
        self.text_entry.beenModified = self.callback
        self.text_entry.pack(side="left", fill=BOTH, expand=1)

class ViewingFrame(Frame):
    def __init__(self,  scrollbar, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.scrollbar = scrollbar
        self.buildWidgets()

    def buildWidgets(self):
        self.text_entry = Text(self, width=60, height=40)
        self.text_entry.pack(side="left", fill=BOTH, expand=1)

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.buildWidgets()

    def process_text(self, event):
        text_entry = self.containing_frame.viewing_frame.text_entry

        text_entry.config(state=NORMAL)
        self.containing_frame.viewing_frame.text_entry.delete("1.0", "end-1c")
        self.containing_frame.viewing_frame.text_entry.insert(INSERT, self.containing_frame.writing_frame.text_entry.get("1.0", "end-1c"))
        text_entry.mark_set(INSERT, self.containing_frame.writing_frame.text_entry.index(INSERT))
        text_entry.config(state=DISABLED)

        start = "1.0"
        while 1:
            pos = text_entry.search(r'^[A-Z]+$', start, regexp=True, stopindex=END)
            if not pos:
                break
            line_no = pos[0:pos.index(".")]
            my_start = line_no+".0"
            my_end = line_no+".end"
            print(pos)
            print(my_start)
            text_entry.tag_configure("character", font=("Courier New", 12, "bold"), justify="center")
            text_entry.tag_add("character", my_start, my_end)
            start = pos + "+1c"

    def buildWidgets(self):
        self.containing_frame = Frame(self)
        self.containing_frame.writing_frame = WritingFrame(self.containing_frame)

        self.containing_frame.viewing_frame = ViewingFrame(self.containing_frame.writing_frame.scrollbar,
                                                           self.containing_frame)
        self.containing_frame.writing_frame.text_entry.beenModified = self.process_text
        self.containing_frame.writing_frame.pack(side="left")
        self.containing_frame.viewing_frame.pack(side="left")


        self.containing_frame.pack(side="top")

        self.quit = Button(self,
                           text="Quit",
                           command=root.destroy)
        self.quit.pack(side="bottom")


if __name__ == "__main__":
    root = Tk()
    app = Application(master=root)
    app.master.title("Libretto")
    app.master.minsize(400, 400)
    app.mainloop()
