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

class ModifiedText(ModifiedMixin, Text):
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

        self.text_entry = ModifiedText(self, font=("Courier New", 12), yscrollcommand=self.scrollbar.set, width=96, height=40, wrap=WORD)
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
        self.text_entry = Text(self, font=("Courier New", 12), width=60, height=40, wrap=WORD)
        self.text_entry.pack(side="left", fill=BOTH, expand=1)

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.buildWidgets()

    def wipe_tags(self, text_entry):
        text_entry.tag_delete("scene_heading")
        text_entry.tag_delete("transition")
        text_entry.tag_delete("character")
        text_entry.tag_delete("parenthetical")
        text_entry.tag_delete("dialogue")
        text_entry.tag_delete("action")

    def format_transitions(self, text_entry):
        start = "1.0"
        while 1:
            pos = text_entry.search(r'^[A-Z ]+:$', start, regexp=True, stopindex=END)
            if not pos:
                break
            line_no = pos[0:pos.index(".")]
            my_start = line_no+".0"
            my_end = line_no+".end"
            if not text_entry.tag_names(index=my_start):
                text_entry.tag_add("transition", my_start, my_end)
            start = pos + "+1c"

    def format_scene_headings(self, text_entry):
        start = "1.0"
        while 1:
            pos = text_entry.search(r'^(\..+|[Ii][Nn][Tt]|[Ee][Xx][Tt]|[Ee][Ss][Tt]|[Ii][Nn][Tt]\.?/[Ee][Xx][Tt]|[Ii]/[Ee]).+$', start, regexp=True, stopindex=END)
            if not pos:
                break
            line_no = pos[0:pos.index(".")]
            my_start = line_no+".0"
            my_end = line_no+".end"
            if not text_entry.tag_names(index=my_start):
                text_entry.tag_add("scene_heading", my_start, my_end)
            start = pos + "+1c"

    def format_characters(self, text_entry):
        start = "1.0"
        while 1:
            pos = text_entry.search(r'^[A-Z ]+$', start, regexp=True, stopindex=END)
            if not pos:
                break
            line_no = pos[0:pos.index(".")]
            my_start = line_no+".0"
            my_end = line_no+".end"
            my_next_start = str(int(line_no)+1)+".0"
            my_next_end = str(int(line_no)+1)+".end"
            # Only a character if the next line is non-empty
            if not text_entry.get(my_next_start, my_next_end) == "" and not text_entry.tag_names(index=my_start) and not text_entry.tag_names(index=my_next_start):
                text_entry.tag_add("character", my_start, my_end)
            start = pos + "+1c"

    def format_dialogue_and_parentheticals(self, text_entry):
        start = "2.0"
        while 1:
            # Check previous line was dialogue, parenthetical or character
            this_line_no = int(start[0:start.index(".")])
            last_line_no = str(this_line_no - 1)
            this_line_no = str(this_line_no)
            candidate = (text_entry.tag_nextrange("character", last_line_no+".0", last_line_no+".end") or
                         text_entry.tag_nextrange("parenthetical", last_line_no+".0", last_line_no+".end") or
                         text_entry.tag_nextrange("dialogue", last_line_no+".0", last_line_no+".end"))
            if (candidate):
                my_start = this_line_no+".0"
                my_end = this_line_no+".end"
                parenthetical = text_entry.search(r'^\(', my_start, regexp=True, stopindex=my_end)
                if parenthetical:
                    text_entry.tag_add("parenthetical", my_start, my_end)
                else:
                    text_entry.tag_add("dialogue", my_start, my_end)

            start = text_entry.index(start + " lineend +1c")
            next_line_no = int(start[0:start.index(".")])
            last_line_no = text_entry.index(END)
            last_line_no = int(last_line_no[0:last_line_no.index(".")])
            if next_line_no >= last_line_no:
                break

    def format_the_rest(self, text_entry):
        start = "1.0"
        while 1:
            this_line_no = str(int(start[0:start.index(".")]))
            my_start = this_line_no+".0"
            my_end = this_line_no+".end"
            candidate = not text_entry.tag_names(start)
            if (candidate):
                text_entry.tag_add("action", my_start, my_end)
            start = text_entry.index(start + " lineend +1c")
            next_line_no = int(start[0:start.index(".")])
            last_line_no = text_entry.index(END)
            last_line_no = int(last_line_no[0:last_line_no.index(".")])
            if next_line_no >= last_line_no:
                break
        text_entry.tag_add("action", "1.0", END)

    def my_tag_lower(self, text_entry, tag):
        try:
            text_entry.tag_lower(tag)
        except:
            pass

    def order_tags(self, text_entry):
        # Scene first, then character, then dialogue, then parentheses
        self.my_tag_lower(text_entry, "scene_heading")
        self.my_tag_lower(text_entry, "character")
        self.my_tag_lower(text_entry, "action")

    def configure_tags(self, text_entry):
        text_entry.tag_configure("scene_heading", font=("Courier New", 12, "bold"), lmargin1="1.5i", lmargin2="1.5i", rmargin="1i")
        text_entry.tag_configure("character", font=("Courier New", 12, "bold"), lmargin1="4.2i", lmargin2="4.2i", rmargin="1i")
        text_entry.tag_configure("parenthetical", font=("Courier New", 12), lmargin1="3.6i", lmargin2="3.6i", rmargin="2.9i")
        text_entry.tag_configure("dialogue", font=("Courier New", 12), lmargin1="2.9i", lmargin2="2.9i", rmargin="2.3i")
        text_entry.tag_configure("transition", font=("Courier New", 12, "bold"), lmargin1="6i", lmargin2="6i", rmargin="1i")
        text_entry.tag_configure("action", font=("Courier New", 12), lmargin1="1.5i", lmargin2="1.5i", rmargin="1i")

    def process_text(self, event):
#        text_entry = self.containing_frame.viewing_frame.text_entry

#        text_entry.config(state=NORMAL)
#        self.containing_frame.viewing_frame.text_entry.delete("1.0", "end-1c")
#        self.containing_frame.viewing_frame.text_entry.insert(INSERT, self.containing_frame.writing_frame.text_entry.get("1.0", "end-1c"))
#        text_entry.mark_set(INSERT, self.containing_frame.writing_frame.text_entry.index(INSERT))
#        text_entry.config(state=DISABLED)

        text_entry = self.containing_frame.writing_frame.text_entry

        self.wipe_tags(text_entry)
        self.configure_tags(text_entry)

        self.format_transitions(text_entry)
        self.format_scene_headings(text_entry)
        self.format_characters(text_entry)
        self.format_dialogue_and_parentheticals(text_entry)
        self.format_the_rest(text_entry)
        self.order_tags(text_entry)

    def buildWidgets(self):
        self.containing_frame = Frame(self)
        self.containing_frame.writing_frame = WritingFrame(self.containing_frame)

        text_entry = self.containing_frame.writing_frame.text_entry
        text_entry.beenModified = self.process_text
        self.configure_tags(text_entry)
        text_entry.tag_add("action", "1.0", END)

        self.containing_frame.writing_frame.pack(side="left")

#        self.containing_frame.viewing_frame = ViewingFrame(self.containing_frame.writing_frame.scrollbar,
#                                                           self.containing_frame)
#        self.containing_frame.viewing_frame.pack(side="left")


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
