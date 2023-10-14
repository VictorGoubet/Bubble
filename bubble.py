import time
from typing import List

import numpy as np


class Bubble:
    """A class representing a bubble in a simulation."""

    def __init__(
        self,
        radius: float,
        position: np.ndarray,
        speed: np.ndarray,
        borders_max: np.ndarray,
        borders_min: np.ndarray,
        min_radius: float,
        max_speed: float,
        mode: str,
    ) -> None:
        """Initialize a Bubble instance.

        :param float radius: The radius of the bubble.
        :param np.ndarray position: A 2D array representing the position of the bubble.
        :param np.ndarray speed: A 2D array representing the speed vector of the bubble.
        :param np.ndarray borders_max: A 2D array representing the maximum boundary for the bubble's position.
        :param np.ndarray borders_min: A 2D array representing the minimum boundary for the bubble's position.
        :param float min_radius: The minimum allowable radius of the bubble.
        :param float max_speed: The maximum allowable speed of the bubble.
        :param str mode: The mode of interaction between bubbles (e.g., "split").
        """
        self.max_speed = max_speed
        self.position = position
        self.speed = speed
        self.radius = radius
        self.min_radius = min_radius

        self.t0 = time.time()
        self.t = time.time()
        self.last_split_time = time.time()

        self.mode = mode
        self.to_split = False

        self.borders_max = borders_max
        self.borders_min = borders_min

        self.density = 7874  # iron
        self.set_weight()
        self.set_resistance()

    def get_norm_speed(self) -> float:
        """Compute and return the magnitude of the bubble's speed vector.

        :return float: The magnitude of the speed vector.
        """
        return np.linalg.norm(self.speed)

    def set_resistance(self) -> None:
        """Compute and set the resistance of the bubble based on its density and radius."""
        self.resistance = 0.005 * self.density * (self.radius**1)
        self.energy = 10 * self.resistance
        self.remaining_energy = self.energy

    def set_weight(self) -> None:
        """Compute and set the weight of the bubble based on its density and radius."""
        self.weight = self.density * 3.14 * self.radius**2

    def update_pos(self, bubbles: "List[Bubble]") -> None:
        """Update the position of the bubble, handling boundaries and collisions.

        :param List[Bubble] bubbles: A list of all bubbles in the simulation.
        """
        now = time.time()
        dt = now - self.t

        # Update position
        new_position = self.position + dt * self.speed

        # Check for collisions with borders
        if (new_position[0] + self.radius >= self.borders_max[0]) or (
            new_position[0] - self.radius <= self.borders_min[0]
        ):
            self.speed[0] *= -1

        if (new_position[1] + self.radius >= self.borders_max[1]) or (
            new_position[1] - self.radius <= self.borders_min[1]
        ):
            self.speed[1] *= -1

        # Check for collisions with other bubbles
        if self.mode != "overlap":
            for other in bubbles:
                if other != self:
                    distance = np.linalg.norm(self.position - other.position)
                    if distance <= (self.radius + other.radius):
                        # Bubbles are colliding, update their velocities
                        self.handle_collision(other, distance)

        # Update position after collisions
        self.position += dt * self.speed
        self.t = now

    def handle_collision(self, other: "Bubble", distance: float) -> None:
        """Handle collisions with another bubble, updating velocities.

        :param Bubble other: Another bubble instance.
        :param float distance: Distance between the two bubbles.
        """
        relative_velocity = self.speed - other.speed
        if distance > 0:
            normal_vector = (self.position - other.position) / distance
        else:
            normal_vector = np.array([0, 0])

        # Check if bubbles are moving towards each other
        if np.dot(relative_velocity, normal_vector) < 0:
            m1 = self.weight
            m2 = other.weight
            v1 = np.linalg.norm(self.speed)
            v2 = np.linalg.norm(other.speed)

            # Calculate new velocities using conservation of momentum and kinetic energy
            new_speed_a = self.speed - (2 * m2 / (m1 + m2)) * np.dot(relative_velocity, normal_vector) * normal_vector
            new_speed_b = other.speed + (2 * m1 / (m1 + m2)) * np.dot(relative_velocity, normal_vector) * normal_vector
            new_speed_a = np.clip(new_speed_a, -self.max_speed, self.max_speed)
            new_speed_b = np.clip(new_speed_b, -other.max_speed, other.max_speed)

            # Additional logic for "split" mode
            if self.mode == "split":
                # Calculating transferred energy
                e_transferred_a_b = 0.5 * m1 * (v1**2 - np.linalg.norm(new_speed_a) ** 2)
                e_transferred_b_a = 0.5 * m2 * (v2**2 - np.linalg.norm(new_speed_b) ** 2)

                # Calculating resistances
                # Handling splitting depending on energy and resistance
                for b, e in [(self, e_transferred_b_a), (other, e_transferred_a_b)]:
                    self.remaining_energy -= e
                    if (
                        b.radius > self.min_radius
                        and self.remaining_energy < b.resistance
                        and time.time() - b.t0 > 0.5
                        and time.time() - b.last_split_time > 0.5
                    ):
                        b.to_split = True
            # Additional logic for "merge" mode could be added here

            self.speed = new_speed_a
            other.speed = new_speed_b

    def split(self) -> "Bubble":
        """Split the bubble into two smaller bubbles and return the new bubble.

        :return Bubble: A new bubble resulting from the split.
        """
        self.last_split_time = time.time()

        # Calculate new properties for the split bubbles
        new_radius = self.radius / np.sqrt(2)
        rotate_45_up = np.array([[np.sqrt(2) / 2, -np.sqrt(2) / 2], [np.sqrt(2) / 2, np.sqrt(2) / 2]])
        rotate_45_down = np.array([[np.sqrt(2) / 2, np.sqrt(2) / 2], [-np.sqrt(2) / 2, np.sqrt(2) / 2]])

        # Calculate a perpendicular vector to the speed vector
        perp_vector = np.array([self.speed[1], -self.speed[0]])

        # Normalize the perpendicular vector and scale by the radius
        offset = perp_vector / np.linalg.norm(perp_vector) * new_radius

        # Create new bubble
        new_bubble = Bubble(
            radius=new_radius,
            position=self.position + offset,
            speed=np.dot(rotate_45_up, self.speed),
            borders_max=self.borders_max,
            borders_min=self.borders_min,
            min_radius=self.min_radius,
            max_speed=self.max_speed,
            mode=self.mode,
        )

        # Update properties of original bubble
        self.radius = new_radius
        self.position = self.position - offset
        self.remaining_energy = self.energy
        self.speed = np.dot(rotate_45_down, self.speed)
        self.set_weight()
        self.set_resistance()

        # Notify the simulation to add new bubbles
        self.to_split = False
        return new_bubble

    def __str__(self) -> str:
        return (
            f"Bubble: \n"
            f"\tPosition: {self.position}, \n"
            f"\tSpeed: {self.speed} | {self.get_norm_speed()}, \n"
            f"\tRadius: {self.radius:.2f}, \n"
            f"\tWeight: {self.weight:.2f}"
        )
