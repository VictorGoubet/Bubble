import time

import numpy as np
from vispy import app, gloo

from bubble import Bubble

app.use_app("glfw")


class Simulation(app.Canvas):
    """Simulation of bubbles"""

    def __init__(self) -> None:
        """Initialize the simulation.

        This method initializes the simulation, setting up initial parameters
        like the number of bubbles, dimensions, speed, mode, and shaders.
        It also initializes the position and GUI canvas.
        """
        self.n = 15
        self.width = 1000
        self.height = 1000
        self.min_radius = 0.03
        self.max_radius = 0.15
        self.max_speed = 1
        self.t0 = time.time()
        self.mode = "split"  # split / merge / overlap / bounce
        self.loading_shaders()
        super().__init__(size=(self.width, self.height), keys="interactive")
        self.init_pos()

    def init_pos(self) -> None:
        """Initialize the position of bubbles.

        This method initializes the bubble's position, speed, and boundary limits.
        It sets up the OpenGL Program, vertices for rendering, circle textures, and
        initiates an update timer.
        """
        self.program = gloo.Program(self.vertex, self.fragment)
        self.program["a_position"] = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        self.program["num_circles"] = self.n
        self.program["u_resolution"] = (self.width, self.height)

        self.bubbles = [
            Bubble(
                radius=np.random.choice(list(np.arange(self.min_radius, self.max_radius, self.min_radius))),
                position=np.array([0.5, 0.5]),
                speed=np.random.uniform(-self.max_speed / 3, self.max_speed / 3, size=2),
                borders_max=np.array([1, 1]),
                borders_min=np.array([0, 0]),
                min_radius=self.min_radius,
                mode=self.mode,
                max_speed=self.max_speed,
            )
            for _ in range(self.n)
        ]
        self.update_circle_data()
        self._timer = app.Timer("auto", connect=self.on_timer, start=True)

    def update_circle_data(self) -> None:
        """Update the data of circles to be rendered by the shader.

        This method computes the new data for each bubble, creates a texture
        from this data, and updates the shader uniform variables accordingly.
        """
        new_data = [[b.position[0], b.position[1], b.radius, b.get_norm_speed()] for b in self.bubbles]
        maxSpeed = max(new_data, key=lambda x: x[3])[3]
        circle_data = np.array(new_data, dtype=np.float32)
        texture = gloo.Texture1D(circle_data[:, :4].copy(), internalformat="rgba32f")
        self.program["circles"] = texture
        self.program["num_circles"] = self.n
        self.program["maxSpeed"] = maxSpeed

    def on_timer(self, event) -> None:
        """Handle timer events to update bubble positions and render the scene.

        :param event: Event indicating a timer tick.
        """
        new_bubbles = []  # List to store new bubbles during this update

        for b in self.bubbles:
            b.update_pos(self.bubbles)
        for b in self.bubbles:
            if b.to_split:
                new_b = b.split()
                self.n += 1
                new_bubbles.append(new_b)

        self.bubbles.extend(new_bubbles)
        self.update_circle_data()
        self.program["u_time"] = time.time() - self.t0
        self.update()

    def loading_shaders(self) -> None:
        """Load vertex and fragment shaders from file.

        This method reads shader source code from files and stores them
        as attributes for later use in OpenGL.
        """
        with open("./shaders/vertex.glsl", "r") as f:
            self.vertex = f.read()
        with open("./shaders/fragment.glsl", "r") as f:
            self.fragment = f.read()

    def on_draw(self, event):
        """Handle draw events to clear the buffer and redraw the scene.

        :param event: Event indicating a request to redraw the scene.
        """
        gloo.clear()
        self.program.draw("triangle_strip")

    def on_resize(self, event):
        """Handle resize events to adjust the viewport dimensions.

        :param event: Event containing new size data.
        """
        gloo.set_viewport(0, 0, *event.physical_size)


if __name__ == "__main__":
    sim = Simulation()
    sim.show()
    app.run()
