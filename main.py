import re
import sys
from tkinter import *
from tkinter import font
from tkinter.ttk import *
from mixin import ModifiedMixin

import fpdf

global thefont

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

        self.text_entry = ModifiedText(self, font=(thefont, 12), yscrollcommand=self.scrollbar.set, width=96, height=40, wrap=WORD)
        self.scrollbar.config(command=self.text_entry.yview)
        self.text_entry.beenModified = self.callback
        self.text_entry.pack(side="left")

class ViewingFrame(Frame):
    def __init__(self,  scrollbar, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.scrollbar = scrollbar
        self.buildWidgets()

    def buildWidgets(self):
        self.text_entry = Text(self, font=(thefont, 12), width=60, height=40, wrap=WORD)
        self.text_entry.pack(side="left", fill=BOTH, expand=1)

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.buildWidgets()
        self.old_line_count = 0
        self.text_data = {}
        self.tag_data = {}

    def wipe_tags(self, text_entry):
        text_entry.tag_delete("scene_heading")
        text_entry.tag_delete("transition")
        text_entry.tag_delete("character")
        text_entry.tag_delete("parenthetical")
        text_entry.tag_delete("dialogue")
        text_entry.tag_delete("action")

    def wipe_tags_line(self, text_entry, line):
        start = str(line) + ".0"
        end = str(line) + ".end"
        text_entry.tag_remove("scene_heading", start, end)
        text_entry.tag_remove("transition", start, end)
        text_entry.tag_remove("character", start, end)
        text_entry.tag_remove("parenthetical", start, end)
        text_entry.tag_remove("dialogue", start, end)
        text_entry.tag_remove("action", start, end)

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
            pos = text_entry.search(r'^(\..+|[Ii][Nn][Tt]|[Ee][Xx][Tt]|[Ee][Ss][Tt]|[Ii][Nn][Tt]\.?/[Ee][Xx][Tt]|[Ii]/[Ee])[\. ].+$', start, regexp=True, stopindex=END)
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
            pos = text_entry.search(r'^(@.*|[A-Z \(\)\'\.,]+)$', start, regexp=True, stopindex=END)
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
        end_line_no = text_entry.index(END)
        end_line_no = int(end_line_no[0:end_line_no.index(".")])
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

            start = str(int(this_line_no) + 1) + ".0"
            next_line_no = int(this_line_no) + 1
            if next_line_no >= end_line_no:
                break

    def format_the_rest(self, text_entry):
        start = "1.0"
        end_line_no = text_entry.index(END)
        end_line_no = int(end_line_no[0:end_line_no.index(".")])
        while 1:
            this_line_no = str(int(start[0:start.index(".")]))
            my_start = this_line_no+".0"
            my_end = this_line_no+".end"
            text=text_entry.get(my_start, my_end)
            tags=text_entry.tag_names(my_start) if text != "" else []
            self.text_data[int(this_line_no)] = text
            self.tag_data[int(this_line_no)] = tags

            next_line_no = int(this_line_no) + 1
            if next_line_no >= end_line_no:
                break
            start = str(next_line_no) + ".0"

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
        self.my_tag_lower(text_entry, "dialogue")
        self.my_tag_lower(text_entry, "action")

    def configure_tags(self, text_entry):
        text_entry.tag_configure("scene_heading", font=(thefont, 12, "bold"), lmargin1="1.5i", lmargin2="1.5i", rmargin="1i")
        text_entry.tag_configure("character", font=(thefont, 12, "bold"), lmargin1="4.2i", lmargin2="4.2i", rmargin="1i")
        text_entry.tag_configure("parenthetical", font=(thefont, 12), lmargin1="3.6i", lmargin2="3.6i", rmargin="2.9i")
        text_entry.tag_configure("dialogue", font=(thefont, 12), lmargin1="2.9i", lmargin2="2.9i", rmargin="2.3i")
        text_entry.tag_configure("transition", font=(thefont, 12, "bold"), lmargin1="6i", lmargin2="6i", rmargin="1i")
        text_entry.tag_configure("action", font=(thefont, 12), lmargin1="1.5i", lmargin2="1.5i", rmargin="1i")

    def format_line(self, text_entry, line, already_called_previous=False, already_called_next=False):
        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        current_tags = self.tag_data.get(line_no, [])
        current_text = self.text_data.get(line_no, "")
        self.wipe_tags_line(text_entry, str(line_no))

        self.format_transitions_line(text_entry, line)
        self.format_scene_headings_line(text_entry, line)
        self.format_characters_line(text_entry, line)
        self.format_dialogue_and_parentheticals_line(text_entry, line)

        text_entry.tag_add("action", start, end)

        self.order_tags(text_entry)

        self.tag_data[line_no] = [x for x in text_entry.tag_names(start)] if text_entry.get(start, end) != "" else []
        self.text_data[line_no] = text_entry.get(start, end)
        print(str(line_no))
        print(self.text_data[line_no])
        print(current_text)
        print(self.tag_data[line_no])
        print(current_tags)

        last_line_no = text_entry.index(END)
        last_line_no = int(last_line_no[0:last_line_no.index(".")])

        # Check if we needed to change the tags on this line. If so, check for next and previous lines too.
        # Also need to check on new-lines, which won't change tags.
        if current_tags != self.tag_data[line_no] or self.text_data[line_no] != current_text:
            if (line_no > 1):
                self.format_line(text_entry, str(line_no-1) + ".0", already_called_previous=True)
            if (line_no + 1 < last_line_no):
                self.format_line(text_entry, str(line_no+1) + ".0", already_called_next=True)


    def format_transitions_line(self, text_entry, line):
        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        pos = text_entry.search(r'^[A-Z ]+:$', start, regexp=True, stopindex=end)
        if not pos:
            return
        if not text_entry.tag_names(index=start):
            text_entry.tag_add("transition", start, end)

    def format_scene_headings_line(self, text_entry, line):
        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        pos = text_entry.search(r'^(\..+|[Ii][Nn][Tt]|[Ee][Xx][Tt]|[Ee][Ss][Tt]|[Ii][Nn][Tt]\.?/[Ee][Xx][Tt]|[Ii]/[Ee])[\. ].+$', start, regexp=True, stopindex=end)
        if not pos:
            return
        if not text_entry.tag_names(index=start):
            text_entry.tag_add("scene_heading", start, end)

    def character_candidate(self, text_entry, line):
        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        pos = text_entry.search(r'^(@.*|[A-Z \(\)\'\.,]+)$', start, regexp=True, stopindex=end)
        return pos

    def format_characters_line(self, text_entry, line):
        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        pos = text_entry.search(r'^(@.*|[A-Z \(\)\'\.,]+)$', start, regexp=True, stopindex=end)
        if not pos:
            return
        next_start = str(line_no+1)+".0"
        next_end = str(line_no+1)+".end"
        # Only a character if the next line is non-empty
        if not text_entry.get(next_start, next_end) == "":
            # and not text_entry.tag_names(index=start) and not text_entry.tag_names(index=next_start):
            text_entry.tag_add("character", start, end)

    def format_dialogue_and_parentheticals_line(self, text_entry, line):
        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        last_line_no = text_entry.index(END)
        last_line_no = int(last_line_no[0:last_line_no.index(".")])
        # Check previous line was dialogue, parenthetical or character
        previous_line_no = str(line_no - 1)
        previous_line_start = previous_line_no + ".0"
        previous_line_end = previous_line_no + ".end"
        previous_line_tags = text_entry.tag_names(previous_line_no+".0") if text_entry.get(previous_line_start, previous_line_end) != "" else []
        print(str(previous_line_no))
        print(previous_line_tags)
        candidate = ("character" in previous_line_tags or
                     "parenthetical" in previous_line_tags or
                     "dialogue" in previous_line_tags)
        if (candidate):
            parenthetical = text_entry.search(r'^\(', start, regexp=True, stopindex=end)
            if parenthetical:
                text_entry.tag_add("parenthetical", start, end)
            else:
                text_entry.tag_add("dialogue", start, end)

    def process_text_new(self, event):
        text_entry = self.containing_frame.writing_frame.text_entry
        new_line_count = text_entry.index(END)
        new_line_count = int(new_line_count[0:new_line_count.index(".")])

        # Try and guess how many lines were modified. If it's a lot, process whole file.
        # Else just the modified line and anything branching off that
        if abs(new_line_count - self.old_line_count):
            self.process_text(event)
        else:
            current_line_start = text_entry.index(INSERT + " linestart")
            next_line_start = text_entry.index(INSERT + " lineend")
            next_line_start = text_entry.index(next_line_start + "+1c")
            previous_line_start = text_entry.index(current_line_start + "-1c linestart")
            self.format_line(text_entry, current_line_start)
            self.configure_tags(text_entry)

        self.old_line_count = new_line_count

    def process_text(self, event):
        text_entry = self.containing_frame.writing_frame.text_entry

        self.wipe_tags(text_entry)

        self.format_transitions(text_entry)
        self.format_scene_headings(text_entry)
        self.format_characters(text_entry)
        self.format_dialogue_and_parentheticals(text_entry)
        self.format_the_rest(text_entry)

        self.order_tags(text_entry)
        self.configure_tags(text_entry)

    def tag_to_left_margin(self, tag):
        if tag == "scene_heading":
            return 1.5
        if tag == "character":
            return 3.7
        if tag == "parenthetical":
            return 3.1
        if tag == "dialogue":
            return 2.5
        if tag == "transition":
            return 6
        if tag == "action":
            return 1.5
        return 1.5

    def tag_to_width(self, tag):
        if tag == "scene_heading":
            return 6.0
        if tag == "character":
            return 3.8
        if tag == "parenthetical":
            return 2.5
        if tag == "dialogue":
            return 3.7
        if tag == "transition":
            return 1.5
        if tag == "action":
            return 6.0
        return 6.0

    def tag_to_align(self, tag):
        if tag == "transition":
            return 'R'
        return 'L'


    def pdf(self):
        def remove_leading_special_characters(text):
            new_text = text
            if text and text[0] in [".", "!", "@", "~", ">"]:
                new_text = text[1:]
            return new_text

        text_entry = self.containing_frame.writing_frame.text_entry

        pdf = fpdf.FPDF('P', 'in', format='letter')
        pdf.add_font("CourierPrime", fname='CourierPrime.ttf', uni=True)
        pdf.set_margins(0, 1, 1)


        pdf.add_page()
        pdf.set_font("CourierPrime", size=12)

        start = "1.0"
        while 1:
            this_line_no = str(int(start[0:start.index(".")]))
            tags = text_entry.tag_names(start)
            best_tag = tags[-1] if tags else []
            width = 6
            left_margin = 1.5
            align='L'
            if (best_tag):
                width = self.tag_to_width(best_tag)
                left_margin = self.tag_to_left_margin(best_tag)
                align = self.tag_to_align(best_tag)
                if (best_tag == "character" or best_tag == "scene_heading"):
                    if (pdf.y + 0.17 * 2 > pdf.page_break_trigger):
                        pdf.multi_cell(width, 0.17*2, txt="", align=align)
            text=text_entry.get(start, this_line_no+".end")
            text=remove_leading_special_characters(text)
            pdf.set_x(left_margin)
            pdf.multi_cell(width, 0.17, txt=text, align=align)
            start = text_entry.index(start + " lineend +1c")
            next_line_no = int(start[0:start.index(".")])
            last_line_no = text_entry.index(END)
            last_line_no = int(last_line_no[0:last_line_no.index(".")])
            if next_line_no >= last_line_no:
                break

        pdf.output("output.pdf")

        # Pop up
        top = Toplevel()
        top.minsize(width=100, height=50)
        top.transient(self)
        top.title("Info")

        msg = Message(top, text="Script saved")
        msg.pack()

        button = Button(top, text="Dismiss", command=top.destroy)
        button.pack()

    def buildWidgets(self):
        self.containing_frame = Frame(self)
        self.containing_frame.writing_frame = WritingFrame(self.containing_frame)

        text_entry = self.containing_frame.writing_frame.text_entry
        text_entry.beenModified = self.process_text_new
        self.configure_tags(text_entry)
        text_entry.tag_add("action", "1.0", END)

        self.containing_frame.writing_frame.pack(side="left")

        self.containing_frame.pack(side="top")

        self.quit = Button(self,
                           text="Quit",
                           command=root.destroy)
        self.pdf = Button(self,
                          text="PDF",
                          command=self.pdf)
        self.quit.pack(side="bottom")
        self.pdf.pack(side="bottom")


import cProfile as profile
if __name__ == "__main__":
    sys.stdout = open("output.log", "w")
    sys.stderr = open("errors.log", "w")

    root = Tk()
    thefont = "Courier Prime" if "Courier Prime" in font.families() and sys.platform.startswith("win32") else "Courier New"
    app = Application(master=root)
    app.master.title("Scripter")
    app.master.minsize(400, 400)
#    profile.run('app.mainloop()')
    app.mainloop()
