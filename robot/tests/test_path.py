from typing import List
from movement import Movement, MovementInCm
from path import Path
import pytest

def test_combine_results_nothing_to_combine():
    movements: List[Movement] = [Movement.climb, Movement.left, Movement.climb, Movement.climb, Movement.right, Movement.climb]
    path: Path = Path(movements=movements, movements_in_cm = 5)

    print(f"aggregated_path: {path.aggregated_movements}")
    assert path.aggregated_movements == [MovementInCm(Movement.climb, 0), MovementInCm(Movement.left, 5), MovementInCm(Movement.climb, 0),MovementInCm(Movement.climb, 0), MovementInCm(Movement.right, 5), MovementInCm(Movement.climb, 0)]

def test_combine_results_combine_2_movements_left():
    movements: List[Movement] = [Movement.climb, Movement.left, Movement.left, Movement.climb, Movement.left]
    path: Path = Path(movements=movements, movements_in_cm = 5)
    print(f"aggregated_path: {path.aggregated_movements}")

    assert path.aggregated_movements == [MovementInCm(Movement.climb, 0), MovementInCm(Movement.left, 10), MovementInCm(Movement.climb, 0), MovementInCm(Movement.left, 5)]

def test_combine_results_combine_3_movements_left():
    movements: List[Movement] = [Movement.climb, Movement.left, Movement.left, Movement.left, Movement.climb]
    path: Path = Path(movements=movements, movements_in_cm = 5)

    assert path.aggregated_movements == [MovementInCm(Movement.climb, 0), MovementInCm(Movement.left, 15), MovementInCm(Movement.climb, 0)]

def test_combine_results_combine_3_movements_left_2_movements_right():
    movements: List[Movement] = [Movement.right, Movement.right, Movement.climb, Movement.left, Movement.left, Movement.left, Movement.climb, Movement.left]
    path: Path = Path(movements=movements, movements_in_cm = 5)
    print(f"aggregated_path: {path.aggregated_movements}")

    assert path.aggregated_movements == [MovementInCm(Movement.right, 10), MovementInCm(Movement.climb, 0), MovementInCm(Movement.left, 15), MovementInCm(Movement.climb, 0), MovementInCm(Movement.left, 5)]