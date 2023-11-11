from movement import Movement, MovementInCm
from typing import List


class Path:
    def __init__(self, movements: List[Movement], movements_in_cm: int) -> None:
        self.movements: List[Movement] = movements
        self.movements_in_cm: int = movements_in_cm
        self.aggregated_movements: List[MovementInCm] = self.__combine_movements(movements)
        self.next_movement_index = 0

    def get_next_movement(self) -> MovementInCm:
        """
        Returns the next Movement to be executed.
        Returns None if no Movement is left.
        """
        if self.next_movement_index < len(self.aggregated_movements):
            movement = self.aggregated_movements[self.next_movement_index]
            self.next_movement_index += 1
            return movement
        return None

    def __combine_movements(self, movements: List[Movement]) -> List[MovementInCm]:
        combined_movements: List[MovementInCm] = []

        combined_distance_in_cm = 0
        last_movement: Movement = None

        for movement in movements:
            if (last_movement != movement) or (movement == Movement.climb):
                if last_movement != None:
                    combined_movements.append(MovementInCm(last_movement, combined_distance_in_cm))

                if movement == Movement.climb:
                    combined_distance_in_cm = 0

                else:
                    combined_distance_in_cm = self.movements_in_cm


            elif movement == last_movement:
                combined_distance_in_cm += self.movements_in_cm
                
            last_movement = movement

        if last_movement is not None:
            combined_movements.append(MovementInCm(last_movement, combined_distance_in_cm))

        return combined_movements

    def __eq__(self, o: object) -> bool:
        if o is None:
            return False
        return self.movements == o.movements

    def __repr__(self) -> str:
        return str(self.movements)

    def __str__(self) -> str:
        return str(self.movements)
