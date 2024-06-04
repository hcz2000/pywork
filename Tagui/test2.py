import tkinter as tk

root=tk.Tk()
checkbox_var=tk.IntVar()
checkbox=tk.checkbutton(root,text='中银',variable=checkbox_var)

def button_click():
    checkbox_var
