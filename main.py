import OpenGL
import numpy as np
import glfw

from pathlib import Path

# from utils.obj_loader import load_model

width = 1440
height = 810

# model_path = Path("models") / "Cube.obj"

# load_model("Cube")

glfw.init() # Starts GLFW, prepares it to do the things

window = glfw.create_window(width, height, "Test Window", None, None) # returns a "handle" (which we call window) which we use for our future GLFW calls
#                           width, height, name_of_window, which monitor the screen is placed on*, "share"**

#   *this makes the application fullscreen if not None
#   **Supposedly lets you "share resources with another context" whatever that means

glfw.make_context_current(window)   # binds (activates) the context associated with this window
                                    # You can have many windows (and thus contexts) but only 1 can be current per thread

glfw.swap_interval(0) # Enables vsync, which makes the refresh rate match with the refresh rate of the monitor
# Currently disabled (0), set to (1) to enable

while not glfw.window_should_close(window): # Checks if the window should close, if it should, we exit the loop.

    # This is where the magic happens

    glfw.swap_buffers(window) # Swaps the front and rear buffers, takes the calculated screen (rear buffer) and puts it on the display (front buffer)
    glfw.poll_events() # Checks for inputs.

glfw.terminate() # terminates GLFW, effectively closing all windows