import tkinter as tk

root=tk.Tk()
checkbox_var=tk.IntVar()
checkbox=tk.checkbutton(root,text='中银',variable=checkbox_var)

def button_click():
    checkbox_value=checkbox_var.get()
    print(checkbox_value)


button=tk.Button(root,text='确定',command=button_click)
label=tk.Label(root,text='label')
checkbox.pack()
button.pack()
label.pack()
root.mainloop()