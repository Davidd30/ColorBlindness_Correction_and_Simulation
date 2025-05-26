import datetime
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import cv2 as cv
import numpy as np

class CameraApp:
    def __init__(self, window):
        self.window = window
        self.window.title('Color Blindness Correction Camera')
        self.window.minsize(1440, 845)
        self.window.maxsize(1440, 845)
        self.window.configure(bg='#2E3440')
        
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            print("Unable to read camera feed")
            self.window.destroy()
            return
        
        # Define color blindness matrices
        self.color_blindness_matrices = {
            "Protanopia (Red-Blind)": np.array([[0.567, 0.433, 0],
                                              [0.558, 0.442, 0],
                                              [0, 0.242, 0.758]]),

            "Deuteranopia (Green-Blind)": np.array([[0.625, 0.375, 0],
                                                  [0.7, 0.3, 0],
                                                  [0, 0.3, 0.7]]),

            "Tritanopia (Blue-Blind)": np.array([[0.95, 0.05, 0],
                                               [0, 0.433, 0.567],
                                               [0, 0.475, 0.525]])
        }
        
        self.current_filter = "None"
        self.correction_enabled = BooleanVar(value=False)
        self.setup_ui()
        self.update_frame()
        
    def setup_ui(self):
        
        self.main_frame = Frame(self.window, bg='#2E3440')
        self.main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.sidebar = Frame(self.main_frame, bg='#3B4252', width=200)
        self.sidebar.pack(side=LEFT, fill=Y, padx=5, pady=5)
        
        # Sidebar title
        Label(self.sidebar, text="Color Blindness Filters", font=("Arial", 12, "bold"), 
              bg='#3B4252', fg='white').pack(pady=10)
        
        # Filter options
        filters = [
            ("Normal View", "None"),
            ("Protanopia (Red-Blind)", "Protanopia (Red-Blind)"),
            ("Deuteranopia (Green-Blind)", "Deuteranopia (Green-Blind)"),
            ("Tritanopia (Blue-Blind)", "Tritanopia (Blue-Blind)")
        ]
        
        self.filter_var = StringVar(value="None")
        
        for text, value in filters:
            rb = Radiobutton(self.sidebar, text=text, value=value, variable=self.filter_var,
                           bg='#3B4252', fg='white', selectcolor='#5E81AC',
                           activebackground='#3B4252', activeforeground='white',
                           command=self.update_filter)
            rb.pack(anchor=W, padx=10, pady=5)
            
        # Correction checkbox
        self.correction_checkbox = Checkbutton(self.sidebar, text="Apply Correction", 
                                              variable=self.correction_enabled,
                                              bg='#3B4252', fg='white', selectcolor='#5E81AC',
                                              activebackground='#3B4252', activeforeground='white',
                                              command=self.update_filter)
        self.correction_checkbox.pack(anchor=W, padx=10, pady=(20, 5))
        
        # Camera frame
        self.camera_frame = Frame(self.main_frame, bg='#2E3440')
        self.camera_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        
        # Camera view
        self.camera_label = Label(self.camera_frame, bg='black')
        self.camera_label.pack(padx=5, pady=5, fill=BOTH, expand=True)
        
        # Buttons frame
        self.button_frame = Frame(self.camera_frame, bg='#2E3440')
        self.button_frame.pack(fill=X, pady=10)

        self.capture_button = Button(self.button_frame, text='Capture Image', 
                                   bg='#5E81AC', fg='black', font=("Arial", 11),
                                   activebackground='#81A1C1', activeforeground='white',
                                   relief=FLAT, command=self.capture_image, padx=15, pady=8)
        self.capture_button.pack(side=LEFT, padx=500)
        
        # Status bar
        self.status_bar = Label(self.window, text="   Ready | Normal View applied", 
                              bd=1, relief=SUNKEN, anchor=W, bg='#4C566A', fg='white')
        self.status_bar.pack(side=BOTTOM, fill=X)

    def simulate_color_blindness(self, image, matrix):

        img_float = image.astype(float) / 255.0
        simulated = np.dot(img_float, matrix.T)
        simulated = np.clip(simulated, 0, 1)
        return (simulated * 255).astype(np.uint8)
        
    def apply_daltonization(self, original_image, simulated_image):

        original = original_image.astype(float) / 255.0
        simulated = simulated_image.astype(float) / 255.0
        
        # Calculate error between what normal vision sees and what colorblind vision sees
        error = original - simulated
        
        
        if self.current_filter == "Protanopia (Red-Blind)":
            
            correction = np.zeros_like(error)
            correction[:,:,1] = 0.7 * error[:,:,0]  # Add red error to green channel
            correction[:,:,2] = 0.7 * error[:,:,0]  # Add red error to blue channel
            
        elif self.current_filter == "Deuteranopia (Green-Blind)":

            correction = np.zeros_like(error)
            correction[:,:,0] = 0.7 * error[:,:,1]  # Add green error to red channel
            correction[:,:,2] = 0.7 * error[:,:,1]  # Add green error to blue channel
            
        elif self.current_filter == "Tritanopia (Blue-Blind)":

            correction = np.zeros_like(error)
            correction[:,:,0] = 0.7 * error[:,:,2]  # Add blue error to red channel
            correction[:,:,1] = 0.7 * error[:,:,2]  # Add blue error to green channel
            
        else:
            return original_image  
        
        # Apply correction to the original image
        corrected = original + correction
        corrected = np.clip(corrected, 0, 1)
        
        return (corrected * 255).astype(np.uint8)
        
    def apply_filter(self, frame, filter_type):
        if filter_type == "None":
            return frame
            
        matrix = self.color_blindness_matrices[filter_type]
        
        # Simulate color blindness
        simulated = self.simulate_color_blindness(frame, matrix)
        
        # Apply correction if enabled
        if self.correction_enabled.get():
            return self.apply_daltonization(frame, simulated)
        else:
            return simulated
        
    def update_filter(self):
        self.current_filter = self.filter_var.get()
        
        if self.current_filter == "None":
            status = "No filter applied"
        else:
            status = f"Filter: {self.current_filter}"
            if self.correction_enabled.get():
                status += " with correction"
                
        self.status_bar.config(text=f"   Ready | {status}")
    
    def capture_image(self):
        # Save both original and filtered images
        timestamp = str(datetime.datetime.now().today()).replace(':', "_")
        
        # Save original
        orig_filename = f"original_{timestamp}.jpg"
        Image.fromarray(self.original_frame).save(orig_filename)
        
        # Save filtered if a filter is applied
        if self.current_filter != "None":
            filtered_filename = f"{self.current_filter}_{timestamp}.jpg"
            Image.fromarray(self.filtered_frame).save(filtered_filename)
            self.status_bar.config(text=f"Images saved as {orig_filename} and {filtered_filename}")
        else:
            self.status_bar.config(text=f"Image saved as {orig_filename}")
    
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv.flip(frame, 1)  # Mirror effect
            self.original_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            
            # Apply selected filter
            self.filtered_frame = self.apply_filter(self.original_frame, self.current_filter)
            
            # Display the filtered frame
            img = ImageTk.PhotoImage(Image.fromarray(self.filtered_frame))
            self.camera_label.configure(image=img)
            self.camera_label.image = img
            
        self.window.after(10, self.update_frame)
    
    def exit_window(self):
        self.cap.release()
        cv.destroyAllWindows()
        self.window.destroy()
        self.window.quit()

if __name__ == "__main__":
    root = Tk()
    app = CameraApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_window)
    root.mainloop()










