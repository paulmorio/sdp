from Tkinter import *


class Launcher(Frame):
    """
    The launcher GUI
    """
    def __init__(self):
        self.gui_root = Tk()

        self.gui_root.resizable(width=FALSE, height=FALSE)
        self.gui_root.wm_title("Launcher")

        Label(self.gui_root, text="Group 7 - SDP - Launcher", height=2).grid(
            row=0, column=0, columnspan=2)
        self.gui_root.bind('<Escape>', lambda e: self.gui_root.quit())

        self.launching = False

        Frame.__init__(self, self.gui_root)

        self.pitch = StringVar(self.gui_root)
        self.colour = StringVar(self.gui_root)
        self.side = StringVar(self.gui_root)
        self.profile = StringVar(self.gui_root)
        self.comms = BooleanVar(self.gui_root)
        self.create_widgets()

    def create_widgets(self):
        """
        Creates a drop-down menu for:
        Pitch, Colour, Side, Profile, and Comms
        Creates buttons to:
        Launch the system, calibrate the pitch
        """
        # Launcher controls/values for...
        # Pitch
        Label(self.gui_root, text="Pitch:").grid(row=1, column=0)
        self.pitch.set("0")  # default value
        pitch_select = OptionMenu(self.gui_root, self.pitch, "0", "1")
        pitch_select.grid(row=1, column=1)

        # Colour
        Label(self.gui_root, text="Colour:").grid(row=2, column=0)
        self.colour.set("yellow")
        colour_select = OptionMenu(self.gui_root, self.colour, "yellow", "blue")
        colour_select.grid(row=2, column=1)

        # Side
        Label(self.gui_root, text="Side:").grid(row=3, column=0)
        self.side.set("left")
        side_select = OptionMenu(self.gui_root, self.side, "left", "right")
        side_select.grid(row=3, column=1)

        # Profile
        Label(self.gui_root, text="Profile:").grid(row=4, column=0)
        self.profile.set("attacker")
        profile_select = OptionMenu(self.gui_root, self.profile,
                                    "attacker", "penalty", "None")
        profile_select.grid(row=4, column=1)

        # Comms
        Label(self.gui_root, text="Comms:").grid(row=5, column=0)
        self.comms.set(True)
        comms_select = OptionMenu(self.gui_root, self.comms, True, False)
        comms_select.grid(row=5, column=1)

        # Pitch calibration
        calibrate = Button(self.gui_root)
        calibrate["text"] = "Calibrate Pitch"
        calibrate["command"] = self.calibrate_table
        calibrate.grid(row=7, column=1)

        # Launch
        launch = Button(self.gui_root)
        launch["text"] = "Launch"
        launch["command"] = self.clean_launch
        launch.grid(row=7, column=0)

    def clean_launch(self):
        """
        Sets a flag to true, and then closes the launcher
        """
        self.launching = True
        self.gui_root.destroy()

    def calibrate_table(self):
        """
        Run the table calibration tool from the launcher
        """
        from pc.vision.table_setup import TableSetup
        self.gui_root.destroy()
        table_setup = TableSetup(int(self.pitch.get()))
        table_setup.run()
