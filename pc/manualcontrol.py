import Tkinter as tk

class ManualControl():
    """
    A graphical window which allows for manual control of the robot. This
    allows for easy partial testing of the robot's construction and code etc.
    """

    def on_key_press(self, event):
        print "You pressed %s" % event.char

    def start(self):
        # Grab control text from file
        controls_file = open("manual_controls.txt")
        controls = controls_file.read()
        controls_file.close()

        # Compose window elements
        root = tk.Tk()
        text = tk.Label(root, background='white', text=controls)
        text.pack()

        # Set up key bindings
        root.bind('<Left>', self.on_key_press)
        root.bind('<Right>', self.on_key_press)
        root.bind('<Up>', self.on_key_press)
        root.bind('<Down>', self.on_key_press)
        root.bind('g', self.on_key_press)
        root.bind('<space>', self.on_key_press)

        # Set window attributes and start
        # TODO force proper focus on new window. root.focus_force insufficient
        root.geometry('300x200')
        root.wm_title("Manual Control")
        root.wm_attributes("-topmost", 1)
        root.mainloop()
