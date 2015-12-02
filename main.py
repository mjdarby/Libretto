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
        text_entry.tag_delete("centered_text")
        text_entry.tag_delete("underline")
        text_entry.tag_delete("italics")
        text_entry.tag_delete("bold")
        text_entry.tag_delete("bold_italics")
        text_entry.tag_delete("bold_underline")
        text_entry.tag_delete("italic_underline")
        text_entry.tag_delete("bold_italic_underline")

        text_entry.tag_delete("scene_heading")
        text_entry.tag_delete("transition")
        text_entry.tag_delete("character")
        text_entry.tag_delete("parenthetical")
        text_entry.tag_delete("dialogue")
        text_entry.tag_delete("action")

    def wipe_tags_line(self, text_entry, line):
        start = str(line) + ".0"
        end = str(line) + ".end"
        text_entry.tag_remove("centered_text", start, end)
        text_entry.tag_remove("underline", start, end)
        text_entry.tag_remove("italics", start, end)
        text_entry.tag_remove("bold", start, end)
        text_entry.tag_remove("bold_italics", start, end)
        text_entry.tag_remove("bold_underline", start, end)
        text_entry.tag_remove("italic_underline", start, end)
        text_entry.tag_remove("bold_italic_underline", start, end)

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
            prev_line_start_idx = str(int(line_no) - 1) + ".0"
            prev_line_end_idx = str(int(line_no) - 1) + ".end"
            next_line_start_idx = str(int(line_no) + 1) + ".0"
            next_line_end_idx = str(int(line_no) + 1) + ".end"
            my_start = line_no+".0"
            my_end = line_no+".end"
            if (not text_entry.tag_names(index=my_start) and
                text_entry.get(prev_line_start_idx, prev_line_end_idx) == "" and
                text_entry.get(next_line_start_idx, next_line_end_idx) == ""):
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

    def format_centered_text(self, text_entry):
        start = "1.0"
        while 1:
            pos = text_entry.search(r'^>.+<$', start, regexp=True, stopindex=END)
            if not pos:
                break
            line_no = pos[0:pos.index(".")]
            my_start = line_no+".0"
            my_end = line_no+".end"
            if not text_entry.tag_names(index=my_start):
                text_entry.tag_add("centered_text", my_start, my_end)
            start = pos + "+1c"

    def format_emphasis(self, text_entry):
        def already_styled(pos):
            tags = text_entry.tag_names(pos+"+1c")
            styles = ["bold_italic_underline",
                      "bold_italics",
                      "bold",
                      "italics",
                      "underline",
                      "bold_underline",
                      "italic_underline"]
            return any([x in tags for x in styles])

        start = "1.0"
        while 1:
            pos = text_entry.search(r'(_\*{3}|\*{3}_)[^<>]+(_\*{3}|\*{3}_)', start, regexp=True, stopindex=END)
            if pos:
                end_pos = text_entry.search(r'(_\*{3}|\*{3}_)', pos + "+1c", regexp=True, stopindex=END)
                text_entry.tag_add("bold_italic_underline", pos, end_pos + "+4c")
            if not pos:
                break
            start = pos + "+1c"

        start = "1.0"
        while 1:
            pos = text_entry.search(r'\*\*\*[^<>]+\*\*\*', start, regexp=True, stopindex=END)
            end_pos = pos
            if pos and not already_styled(pos):
                end_pos = text_entry.search(r'\*\*\*', pos + "+1c", regexp=True, stopindex=END)
                text_entry.tag_add("bold_italics", pos, end_pos + "+3c")
            if not pos:
                break
            start = end_pos + "+1c"

        start = "1.0"
        while 1:
            pos = text_entry.search(r'(_\*{2}|\*{2}_)[^<>]+(_\*{2}|\*{2}_)', start, regexp=True, stopindex=END)
            end_pos = pos
            if pos and not already_styled(pos):
                end_pos = text_entry.search(r'(_\*{2}|\*{2}_)', pos + "+1c", regexp=True, stopindex=END)
                text_entry.tag_add("bold_underline", pos, end_pos + "+3c")
            if not pos:
                break
            start = end_pos + "+1c"

        start = "1.0"
        while 1:
            pos = text_entry.search(r'(_\*{1}|\*{1}_)[^<>]+(_\*{1}|\*{1}_)', start, regexp=True, stopindex=END)
            end_pos = pos
            if pos and not already_styled(pos):
                end_pos = text_entry.search(r'(_\*{1}|\*{1}_)', pos + "+1c", regexp=True, stopindex=END)
                text_entry.tag_add("italic_underline", pos, end_pos + "+2c")
            if not pos:
                break
            start = end_pos + "+1c"

        start = "1.0"
        while 1:
            pos = text_entry.search(r'\*\*[^\*]+\*\*', start, regexp=True, stopindex=END)
            end_pos = pos
            if pos and not already_styled(pos):
                end_pos = text_entry.search(r'\*\*', pos + "+1c", regexp=True, stopindex=END)
                text_entry.tag_add("bold", pos, end_pos + "+2c")
            if not pos:
                break
            start = end_pos + "+1c"

        start = "1.0"
        while 1:
            pos = text_entry.search(r'\*[^\*]+\*', start, regexp=True, stopindex=END)
            end_pos = pos
            if pos and not already_styled(pos):
                end_pos = text_entry.search(r'\*', pos + "+1c", regexp=True, stopindex=END)
                text_entry.tag_add("italics", pos, end_pos + "+1c")
            if not pos:
                break
            start = end_pos + "+1c"

        start = "1.0"
        while 1:
            pos = text_entry.search(r'_[^_]+_', start, regexp=True, stopindex=END)
            end_pos = pos
            if pos and not already_styled(pos):
                end_pos = text_entry.search(r'_', pos + "+1c", regexp=True, stopindex=END)
                text_entry.tag_add("underline", pos, end_pos + "+1c")
            if not pos:
                break
            start = end_pos + "+1c"

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
        self.my_tag_lower(text_entry, "bold_italic_underline")
        self.my_tag_lower(text_entry, "bold_italic")
        self.my_tag_lower(text_entry, "bold_underline")
        self.my_tag_lower(text_entry, "italic_underline")
        self.my_tag_lower(text_entry, "bold")
        self.my_tag_lower(text_entry, "italic")
        self.my_tag_lower(text_entry, "underline")
        # Scene first, then character, then dialogue, then parentheses
        self.my_tag_lower(text_entry, "scene_heading")
        self.my_tag_lower(text_entry, "character")
        self.my_tag_lower(text_entry, "dialogue")
        self.my_tag_lower(text_entry, "centered_text")
        self.my_tag_lower(text_entry, "action")


    def configure_tags(self, text_entry):
        text_entry.tag_configure("scene_heading", font=(thefont, 12, "bold"), lmargin1="1.5i", lmargin2="1.5i", rmargin="1i")
        text_entry.tag_configure("character", font=(thefont, 12, "bold"), lmargin1="4.2i", lmargin2="4.2i", rmargin="1i")
        text_entry.tag_configure("parenthetical", font=(thefont, 12), lmargin1="3.6i", lmargin2="3.6i", rmargin="2.9i")
        text_entry.tag_configure("dialogue", font=(thefont, 12), lmargin1="2.9i", lmargin2="2.9i", rmargin="2.3i")
        text_entry.tag_configure("transition", font=(thefont, 12, "bold"), lmargin1="6i", lmargin2="6i", rmargin="1i")
        text_entry.tag_configure("action", font=(thefont, 12), lmargin1="1.5i", lmargin2="1.5i", rmargin="1i")

        # Modifiers
        text_entry.tag_configure("centered_text", justify="center")
        text_entry.tag_configure("italics", font=(thefont, 12, "italic"))
        text_entry.tag_configure("bold", font=(thefont, 12, "bold"))
        text_entry.tag_configure("bold_italics", font=(thefont, 12, "bold italic" ))
        text_entry.tag_configure("italic_underline", font=(thefont, 12, "italic underline" ))
        text_entry.tag_configure("bold_underline", font=(thefont, 12, "bold underline" ))
        text_entry.tag_configure("underline", font=(thefont, 12, "underline" ))
        text_entry.tag_configure("bold_italic_underline", font=(thefont, 12, "bold italic underline" ))

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

        self.format_emphasis_line(text_entry, line)
        self.format_centered_text_line(text_entry, line)
        text_entry.tag_add("action", start, end)

        self.order_tags(text_entry)

        self.tag_data[line_no] = [x for x in text_entry.tag_names(start)] if text_entry.get(start, end) != "" else []
        self.text_data[line_no] = text_entry.get(start, end)

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
        prev_line_start_idx = str(line_no - 1) + ".0"
        prev_line_end_idx = str(line_no - 1) + ".end"
        next_line_start_idx = str(line_no + 1) + ".0"
        next_line_end_idx = str(line_no + 1) + ".end"
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        pos = text_entry.search(r'^[A-Z ]+:$', start, regexp=True, stopindex=end)
        if not pos:
            return
        if (not text_entry.tag_names(index=start) and
            text_entry.get(prev_line_start_idx, prev_line_end_idx) == "" and
            text_entry.get(next_line_start_idx, next_line_end_idx) == ""):
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

    def format_centered_text_line(self, text_entry, line):
        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"
        pos = text_entry.search(r'^>.+<$', start, regexp=True, stopindex=end)
        if not pos:
            return
        if not text_entry.tag_names(index=start):
            text_entry.tag_add("centered_text", start, end)

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
        candidate = ("character" in previous_line_tags or
                     "parenthetical" in previous_line_tags or
                     "dialogue" in previous_line_tags)
        if (candidate):
            parenthetical = text_entry.search(r'^\(', start, regexp=True, stopindex=end)
            if parenthetical:
                text_entry.tag_add("parenthetical", start, end)
            else:
                text_entry.tag_add("dialogue", start, end)

    def format_emphasis_line(self, text_entry, line):
        def already_styled(pos):
            tags = text_entry.tag_names(pos+"+1c")
            styles = ["bold_italic_underline",
                      "bold_italics",
                      "bold",
                      "italics",
                      "underline",
                      "bold_underline",
                      "italic_underline"]
            return any([x in tags for x in styles])

        line_no = int(line[0:line.index(".")])
        start = str(line_no) +".0"
        end =  str(line_no) + ".end"

        pos = text_entry.search(r'(_\*{3}|\*{3}_)[^<>]+(_\*{3}|\*{3}_)', start, regexp=True, stopindex=end)
        while pos:
            end_pos = text_entry.search(r'(_\*{3}|\*{3}_)', pos + "+1c", regexp=True, stopindex=end) # Must work
            text_entry.tag_add("bold_italic_underline", pos, end_pos + "+4c")
            pos = text_entry.search(r'(_\*{3}|\*{3}_)[^<>]+(_\*{3}|\*{3}_)', end_pos+"+1c", regexp=True, stopindex=end)

        # Bold italics
        pos = text_entry.search(r'\*\*\*[^<>]+\*\*\*', start, regexp=True, stopindex=end)
        while pos and not already_styled(pos):
            end_pos = text_entry.search(r'\*\*\*', pos + "+1c", regexp=True, stopindex=end) # Must work
            text_entry.tag_add("bold_italics", pos, end_pos + "+3c")
            pos = text_entry.search(r'\*\*\*[^<>]+\*\*\*', end_pos+"+1c", regexp=True, stopindex=end)

        pos = text_entry.search(r'(_\*{2}|\*{2}_)[^<>]+(_\*{2}|\*{2}_)', start, regexp=True, stopindex=end)
        while pos and not already_styled(pos):
            end_pos = text_entry.search(r'(_\*{2}|\*{2}_)', pos + "+1c", regexp=True, stopindex=end) # Must work
            text_entry.tag_add("bold_underline", pos, end_pos + "+3c")
            pos = text_entry.search(r'(_\*{2}|\*{2}_)[^<>]+(_\*{2}|\*{2}_)', end_pos+"+1c", regexp=True, stopindex=end)

        pos = text_entry.search(r'(_\*{1}|\*{1}_)[^<>]+(_\*{1}|\*{1}_)', start, regexp=True, stopindex=end)
        while pos and not already_styled(pos):
            end_pos = text_entry.search(r'(_\*{1}|\*{1}_)', pos + "+1c", regexp=True, stopindex=end) # Must work
            text_entry.tag_add("italic_underline", pos, end_pos + "+2c")
            pos = text_entry.search(r'(_\*{1}|\*{1}_)[^<>]+(_\*{1}|\*{1}_)', end_pos+"+1c", regexp=True, stopindex=end)

        # Bold
        pos = text_entry.search(r'\*\*[^\*]+\*\*', start, regexp=True, stopindex=end)
        while pos and not already_styled(pos):
            end_pos = text_entry.search(r'\*\*', pos + "+1c", regexp=True, stopindex=end) # Must work
            text_entry.tag_add("bold", pos, end_pos + "+2c")
            pos = text_entry.search(r'\*\*[^\*]+\*\*', end_pos+"+1c", regexp=True, stopindex=end)

        # Italics
        pos = text_entry.search(r'\*[^\*]+\*', start, regexp=True, stopindex=end)
        while pos and not already_styled(pos):
            end_pos = text_entry.search(r'\*', pos + "+1c", regexp=True, stopindex=end) # Must work
            text_entry.tag_add("italics", pos, end_pos + "+1c")
            pos = text_entry.search(r'\*[^\*]+\*', end_pos+"+1c", regexp=True, stopindex=end)

        pos = text_entry.search(r'_[^_]+_', start, regexp=True, stopindex=end)
        while pos and not already_styled(pos):
            end_pos = text_entry.search(r'_', pos + "+1c", regexp=True, stopindex=end) # Must work
            text_entry.tag_add("underline", pos, end_pos + "+1c")
            pos = text_entry.search(r'_[^_]+_', end_pos+"+1c", regexp=True, stopindex=end)


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

        self.format_centered_text(text_entry)
        self.format_emphasis(text_entry)
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
        elif tag == "centered_text":
            return 'C'
        return 'L'


    def pdf(self):
        if 0:
            self.pdf_fpdf()
        else:
            self.pdf_reportlab()

    def pdf_reportlab(self):
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.fonts import addMapping
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus.doctemplate import Indenter
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        def remove_leading_special_characters(text):
            new_text = text
            if text and text[0] in [".", "!", "@", "~", ">"]:
                new_text = text[1:]
            return new_text

        def remove_trailing_special_characters(text):
            new_text = text
            if text and text[-1] in ["<"]:
                new_text = text[:-1]
            return new_text

        pdfmetrics.registerFont(TTFont('Courier Prime', 'CourierPrime.ttf'))
        pdfmetrics.registerFont(TTFont('Courier Prime Bold', 'CourierPrimeBold.ttf'))
        pdfmetrics.registerFont(TTFont('Courier Prime Italic', 'CourierPrimeItalic.ttf'))
        pdfmetrics.registerFont(TTFont('Courier Prime Bold Italic', 'CourierPrimeBoldItalic.ttf'))


        addMapping('Courier Prime', 0, 0, "Courier Prime") #normal
        addMapping('Courier Prime', 0, 1, "Courier Prime Italic") #italic
        addMapping('Courier Prime', 1, 0, "Courier Prime Bold") #bold
        addMapping('Courier Prime', 1, 1, "Courier Prime Bold Italic") #italic and bold

        text_entry = self.containing_frame.writing_frame.text_entry

        doc = SimpleDocTemplate("script2.pdf",pagesize=letter,
                                rightMargin=1*inch,leftMargin=1.5*inch,
                                topMargin=inch,bottomMargin=inch)

        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Standard',
                                  fontName='Courier Prime',
                                  fontSize=12,
                                  leading=12))

        styles.add(ParagraphStyle(name='scene_heading',
                                  fontName='Courier Prime',
                                  fontSize=12,
                                  leading=12))

        styles.add(ParagraphStyle(name='character',
                                  fontName='Courier Prime',
                                  fontSize=12,
                                  leading=12))

        styles.add(ParagraphStyle(name='parenthetical',
                                  fontName='Courier Prime',
                                  fontSize=12,
                                  leading=12))

        styles.add(ParagraphStyle(name='dialogue',
                                  fontName='Courier Prime',
                                  fontSize=12,
                                  leading=12))

        styles.add(ParagraphStyle(name='transition',
                                  fontName='Courier Prime',
                                  fontSize=12,
                                  leading=12))

        styles.add(ParagraphStyle(name='centered_text',
                                  fontName='Courier Prime',
                                  fontSize=12,
                                  leading=12,
                                  alignment=TA_CENTER))

        def number_of_characters_to_cut(tag):
            if tag == "bold_italic_underline":
                return 4;
            if tag == "bold_italics":
                return 3;
            if tag == "bold":
                return 2;
            if tag == "italics":
                return 1;
            if tag == "underline":
                return 1;
            if tag == "bold_underline":
                return 3;
            if tag == "italic_underline":
                return 2;

        def get_html(tag):
            if tag == "bold_italic_underline":
                return ["<b><i><u>", "</u></i></b>"];
            if tag == "bold_italics":
                return ["<b><i>", "</i></b>"];
            if tag == "bold":
                return ["<b>", "</b>"];
            if tag == "italics":
                return ["<i>", "</i>"];
            if tag == "underline":
                return ["<u>", "</u>"];
            if tag == "bold_underline":
                return ["<b><u>", "</u></b>"];
            if tag == "italic_underline":
                return ["<i><u>", "</u></i>"];

        def add_formatting_tags(text, tags):
            for tag in tags:
                characters_to_cut = number_of_characters_to_cut(tag[0])
                html_tags = get_html(tag[0])
                start_tag = html_tags[0]
                end_tag = html_tags[1]
                start_idx = tag[1]
                end_idx = tag[2]
                text = text[:end_idx-characters_to_cut] + end_tag + text[end_idx:]
                text = text[:start_idx] + start_tag + text[start_idx+characters_to_cut:]
            return text

        def tag_to_left_margin(tag):
            if tag == "scene_heading":
                return 0
            if tag == "character":
                return 2
            if tag == "parenthetical":
                return 1.5
            if tag == "dialogue":
                return 1
            if tag == "transition":
                return 4
            if tag == "action":
                return 0
            return 0

        def tag_to_right_margin(tag):
            if tag == "scene_heading":
                return 0
            if tag == "character":
                return 0.25
            if tag == "parenthetical":
                return 2.0
            if tag == "dialogue":
                return 1
            if tag == "transition":
                return 0.5
            if tag == "action":
                return 0
            return 0

        def get_ordered_formatting_tags(start, end):
            styles = ["bold_italic_underline",
                      "bold_italics",
                      "bold",
                      "italics",
                      "underline",
                      "bold_underline",
                      "italic_underline"]
            tags = []
            for style in styles:
                tag_range = text_entry.tag_nextrange(style, start, end)
                while tag_range:
                    tag_start = int(tag_range[0][tag_range[0].index(".")+1:])
                    tag_end = int(tag_range[1][tag_range[1].index(".")+1:])
                    tags.append((style, tag_start, tag_end))
                    tag_range = text_entry.tag_nextrange(style, tag_range[1], end)
            return list(reversed(sorted(tags, key = lambda x: x[1])))

        def get_stylesheet(style):
            if style == "scene_heading":
                return "scene_heading"
            if style == "character":
                return "character"
            if style == "parenthetical":
                return "parenthetical"
            if style == "dialogue":
                return "dialogue"
            if style == "transition":
                return "transition"
            if style == "centered_text":
                return "centered_text"
            else:
                return "Standard"

        structure = []

        start = "1.0"
        while 1:
            this_line_no = str(int(start[0:start.index(".")]))
            tags = text_entry.tag_names(start)
            best_tag = tags[-1] if tags else ""
            width = 6
            left_margin = 1.5
            right_margin = 1
            align='L'
            if (best_tag):
                width = self.tag_to_width(best_tag)
                left_margin = tag_to_left_margin(best_tag)
                right_margin = tag_to_right_margin(best_tag)
                align = self.tag_to_align(best_tag)
                # TODO: Fix paginiation for boundary elements, the below
                # is busted
                #if (best_tag == "character" or best_tag == "scene_heading"):
                #    if (pdf.y + 0.17 * 2 > pdf.page_break_trigger):
                #        pdf.multi_cell(width, 0.17*2, txt="", align=align)

            formatting_tags = get_ordered_formatting_tags(start, this_line_no+".end")

            text=text_entry.get(start, this_line_no+".end")
            text=add_formatting_tags(text, formatting_tags)
            text=remove_leading_special_characters(text)
            text=remove_trailing_special_characters(text)
            if text != "":
                structure.append(Indenter(left_margin*inch, right_margin*inch))
                structure.append(Paragraph(text, styles[get_stylesheet(best_tag)]))
                structure.append(Indenter(-left_margin*inch, -right_margin*inch))
            else:
                structure.append(Spacer(1, 12))
            start = text_entry.index(start + " lineend +1c")
            next_line_no = int(start[0:start.index(".")])
            last_line_no = text_entry.index(END)
            last_line_no = int(last_line_no[0:last_line_no.index(".")])
            if next_line_no >= last_line_no:
                break

        def my_page(canv,doc):
            frame = doc.pageTemplates[0].frames[0]
            frame.leftPadding=frame.rightPadding=frame.topPadding=frame.bottomPadding=0
            canv.saveState()

        doc.build(structure, onFirstPage=my_page, onLaterPages=my_page)

        # Pop up
        top = Toplevel()
        top.minsize(width=100, height=50)
        top.transient(self)
        top.title("Info")

        msg = Message(top, text="Script saved")
        msg.pack()

        button = Button(top, text="Dismiss", command=top.destroy)
        button.pack()

    def pdf_fpdf(self):
        def remove_leading_special_characters(text):
            new_text = text
            if text and text[0] in [".", "!", "@", "~", ">"]:
                new_text = text[1:]
            return new_text

        def remove_trailing_special_characters(text):
            new_text = text
            if text and text[-1] in ["<"]:
                new_text = text[:-1]
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

                # TODO: Fix paginiation for boundary elements, the below
                # is busted
                if (best_tag == "character" or best_tag == "scene_heading"):
                    if (pdf.y + 0.17 * 2 > pdf.page_break_trigger):
                        pdf.multi_cell(width, 0.17*2, txt="", align=align)

            text=text_entry.get(start, this_line_no+".end")
            text=remove_leading_special_characters(text)
            text=remove_trailing_special_characters(text)
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
#    sys.stdout = open("output.log", "w")
#    sys.stderr = open("errors.log", "w")

    root = Tk()
    thefont = "Courier Prime" if "Courier Prime" in font.families() and sys.platform.startswith("win32") else "Courier New"
    app = Application(master=root)
    app.master.title("Scripter")
    app.master.minsize(400, 400)
#    profile.run('app.mainloop()')
    app.mainloop()
