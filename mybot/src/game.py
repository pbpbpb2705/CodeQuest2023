import random
import math
import numpy as np
import comms
from object_types import ObjectTypes


class Game:
    """
    Stores all information about the game and manages the communication cycle.
    Available attributes after initialization will be:
    - tank_id: your tank id
    - objects: a dict of all objects on the map like {object-id: object-dict}.
    - width: the width of the map as a floating point number.
    - height: the height of the map as a floating point number.
    - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
        is called and will be available to be used in `respond_to_turn` if needed.
    """

    def __init__(self):
        tank_id_message: dict = comms.read_message()
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"]

        self.current_turn_message = None

        # We will store all game objects here
        self.objects = {}

        next_init_message = comms.read_message()
        while next_init_message != comms.END_INIT_SIGNAL:
            # At this stage, there won't be any "events" in the message. So we only care about the object_info.
            object_info: dict = next_init_message["message"]["updated_objects"]

            # Store them in the objects dict
            self.objects.update(object_info)

            # Read the next message
            next_init_message = comms.read_message()

        # Keep track of destructible walls
        self.destructibles_key = [
            obj
            for obj in self.objects
            if self.objects[obj]["type"] == ObjectTypes.DESTRUCTIBLE_WALL.value
        ]

        # Keep track of bullet
        self.bullet_key = [
            obj
            for obj in self.objects
            if self.objects[obj]["type"] == ObjectTypes.BULLET.value
        ]

        # Keep track of center point
        self.center = [900, 500]

        # We are outside the loop, which means we must've received the END_INIT signal

        # Let's figure out the map size based on the given boundaries

        # Read all the objects and find the boundary objects
        boundaries = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)

        # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

        # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
        biggest_x, biggest_y = [
            max(
                [
                    max(
                        map(
                            lambda single_position: single_position[i],
                            boundary["position"],
                        )
                    )
                    for boundary in boundaries
                ]
            )
            for i in range(2)
        ]

        self.width = biggest_x
        self.height = biggest_y

    def read_next_turn_data(self):
        """
        It's our turn! Read what the game has sent us and update the game info.
        :returns True if the game continues, False if the end game signal is received and the bot should be terminated
        """
        # Read and save the message
        self.current_turn_message = comms.read_message()

        if self.current_turn_message == comms.END_SIGNAL:
            return False

        # Delete the objects that have been deleted
        # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
        # is already deleted, etc.
        for deleted_object_id in self.current_turn_message["message"][
            "deleted_objects"
        ]:
            # Update destructibles_key dict
            if deleted_object_id in self.destructibles_key:
                self.destructibles_key.remove(deleted_object_id)
            try:
                del self.objects[deleted_object_id]
            except KeyError:
                pass

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])

        return True

    def find_center(self):
        #Window width = 1800, height = 1000 => center = [900, 500]
        # Idea: If the init center is not reachable -> Replace the center with the nearest destructible wall
        # # To keep the next center optimal -> Only choose points that are not further from the tank from the init center
        # nearest_dist = 100000
        # nearest_obj = None
        # if (len(self.destructibles_key) > 0):
        #     nearest_obj = self.objects[self.destructibles_key[0]]
        # distance_tank_to_first_center = np.linalg.norm(
        #     np.array(self.center[0]) - np.array(self.objects[self.tank_id]["position"])
        # )
        # for obj in self.destructibles_key:
        #     distance_to_center = np.linalg.norm(
        #         np.array(self.objects[obj]["position"]) - np.array(self.center[-1])
        #     )
        #     distance_to_tank = np.linalg.norm(
        #         np.array(self.objects[obj]["position"])
        #         - np.array(self.objects[self.tank_id]["position"])
        #     )
        #     if (
        #         nearest_dist > distance_to_center
        #         and self.objects[obj]["position"] in self.center
        #         and distance_to_tank < distance_tank_to_first_center
        #     ):
        #         nearest_dist = distance_to_center
        #         nearest_obj = self.objects[obj]
        # self.center.append(nearest_obj["position"])
        tank_position = self.objects[self.tank_id]['position']
        angle = 0
        sub_x = self.center[0] - tank_position[0]
        sub_y = self.center[1] - tank_position[1]
        if (sub_x == 0):
            angle = math.pi / 2 if tank_position[1] > self.center[1] else 3 * math.pi / 2
        elif (sub_y == 0):
            angle = 0 if tank_position[0] > self.center[1] else math.pi
        else:
            angle = math.pi / 4
        self.center[0] += math.cos(angle) * 18
        self.center[1] += math.sin(angle) * 18

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        # Write your code here... For demonstration, this bot just shoots randomly every turn.
        message = {}
        tank_position = self.objects[self.tank_id]["position"]

        # Constantly stay away from boundary
        message["path"] = self.center

        # Random bullet
        message["shoot"] = random.random() * 360
        if (message["shoot"] % 90 == 0):
            message["shoot"] = message["shoot"] + 10 if (message["shoot"] < 360) else message["shoot"] - 10

        # Direct shot
        enemy_tank_position = self.objects[self.enemy_tank_id]["position"]
        tank_sub_x = enemy_tank_position[0] - tank_position[0]
        tank_sub_y = enemy_tank_position[1] - tank_position[1]
        if tank_sub_x == 0:
            angle = (
                math.pi / 2
                if (tank_sub_y > 0)
                else 3 * math.pi / 2
            )
        else:
            angle = math.atan(
                tank_sub_y
                / tank_sub_x
            )
            if (tank_sub_x < 0):
                angle += math.pi
            elif (tank_sub_y < 0):
                angle = 2 * math.pi + angle
        message["shoot"] = np.rad2deg(angle)
        if (message["shoot"] % 90 == 0):
            message["shoot"] = message["shoot"] + 1 if (message["shoot"] < 360) else message["shoot"] - 10

        # If no destructible
        if (len(self.destructibles_key) == 0):
            comms.post_message(message)

        # Only keep the tank near the optimal center (No exact position)
        stopped_at_center = (
            np.linalg.norm(np.array(tank_position) - np.array(self.center))
            <= 36
        )

        #Reset center
        if (stopped_at_center):
            self.center = [900, 500]

        #If no path and not standing at center => Find way
        if (
            self.current_turn_message["message"]["updated_objects"].get(self.tank_id)
            == None
            and not stopped_at_center
        ):
            # Find second-optimal center
            self.find_center()

            # Find the nearest destructible wall
            nearest_dist = 100000
            if (len(self.destructibles_key) > 0):
                nearest_obj = self.objects[self.destructibles_key[0]]
            for obj in self.destructibles_key:
                distance = np.linalg.norm(
                    np.array(self.objects[obj]["position"]) - np.array(tank_position)
                ) ** 2 + np.linalg.norm(
                    np.array(self.objects[obj]["position"])
                    - np.array(self.center)
                )
                if nearest_dist > distance:
                    nearest_dist = distance
                    nearest_obj = self.objects[obj]
            if nearest_obj["position"][0] - tank_position[0] == 0:
                angle = (
                    math.pi / 2
                    if (nearest_obj["position"][1] - tank_position[1] > 0)
                    else 3 * math.pi / 2
                )
            else:
                #sub_y = y_des_wall - y_tank
                sub_y = nearest_obj["position"][1] - tank_position[1]
                if (sub_y > 0):
                    sub_y -= 10
                elif (sub_y < 0):
                    sub_y += 10
                angle = math.atan(
                    sub_y
                    / (nearest_obj["position"][0] - tank_position[0])
                )
                if ((nearest_obj["position"][0] - tank_position[0]) < 0):
                    angle += math.pi
                elif (sub_y < 0):
                    angle = 2 * math.pi + angle


            # Shoot the nearest destructible wall
            message["shoot"] = np.rad2deg(angle)

        comms.post_message(message)
