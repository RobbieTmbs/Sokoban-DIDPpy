import didppy as dp
import matplotlib.pyplot as plt
import os

#Basic Sokoban model

def convert_sokoban_to_array(level_lines):
    char_to_tile = {
        '#': 0,              # wall
        '.': 1, '+': 1, '*': 1,  # goal (with or without player/box)
        ' ': 2, '@': 2, '$': 2   # empty/navigable (with or without player/box)
    }

    player_pos = None
    box_positions = []

    max_width = max(len(line.rstrip()) for line in level_lines)
    puzzle = []

    for y, line in enumerate(level_lines):
        row = []
        for x, char in enumerate(line.rstrip().ljust(max_width)):
            row.append(char_to_tile.get(char, 2))  # default to 2/empty

            if char in ('@', '+'):
                player_pos = (x, y)
            if char in ('$', '*'):
                box_positions.append((x, y))
        puzzle.append(row)

    return puzzle, player_pos, box_positions

def pad_puzzle_to_square(puzzle, pad_value=0):
    height = len(puzzle)
    width = max(len(row) for row in puzzle)
    size = max(width, height)

    # Pad out rows
    padded = [row + [pad_value] * (size - len(row)) for row in puzzle]

    # Add additional rows
    while len(padded) < size:
        padded.append([pad_value] * size)

    return padded

def solve_sokoban(puzzle_lines):
    puzzle, player_position, box_coords = convert_sokoban_to_array(puzzle_lines)
    puzzle = pad_puzzle_to_square(puzzle)

    height = len(puzzle)
    width = len(puzzle[0])
    n = height * width

    model = dp.Model(maximize=False, float_cost=False)
    square = model.add_object_type(number=n)

    def to_index(x, y):
        return y * width + x

    goal_positions = {to_index(x, y) for y in range(height) for x in range(width) if puzzle[y][x] == 1}
    goals = model.add_set_var(object_type=square, target=goal_positions)

    player_pos = model.add_element_var(object_type=square, target=to_index(player_position[0], player_position[1]))

    box_indices = [to_index(x, y) for (x, y) in box_coords]
    box_pos = model.add_set_var(object_type=square, target=box_indices)

    puzzle_map = model.add_element_table(puzzle)
    
    #Move transitions

    move_up = dp.Transition(
        name="move up",
        cost=2 + dp.IntExpr.state_cost(),
        effects=[(player_pos, player_pos - width)],
        preconditions=[
            (~(puzzle_map[(player_pos - width) // width, (player_pos - width) % width] == 0)) &
            ~(box_pos.contains(player_pos - width))
        ],
    )

    move_down = dp.Transition(
        name="move down",
        cost=2 + dp.IntExpr.state_cost(),
        effects=[(player_pos, player_pos + width)],
        preconditions=[
            (~(puzzle_map[(player_pos + width) // width, (player_pos + width) % width] == 0)) &
            ~(box_pos.contains(player_pos + width))
        ],
    )

    move_left = dp.Transition(
        name="move left",
        cost=2 + dp.IntExpr.state_cost(),
        effects=[(player_pos, player_pos - 1)],
        preconditions=[
            (~(puzzle_map[(player_pos - 1) // width, (player_pos - 1) % width] == 0)) &
            ~(box_pos.contains(player_pos - 1))
        ],
    )

    move_right = dp.Transition(
        name="move right",
        cost=2 + dp.IntExpr.state_cost(),
        effects=[(player_pos, player_pos + 1)],
        preconditions=[
            (~(puzzle_map[(player_pos + 1) // width, (player_pos + 1) % width] == 0)) &
            ~(box_pos.contains(player_pos + 1))
        ],
    )

    # Push transitions

    push_up = dp.Transition(
        name="push up",
        cost=1 + dp.IntExpr.state_cost(),
        effects=[
            (player_pos, player_pos - width),
            (box_pos, box_pos.add(player_pos - 2 * width).remove(player_pos - width)),
        ],
        preconditions=[
            box_pos.contains(player_pos - width) &
            ~box_pos.contains(player_pos - 2 * width) &
            ~(puzzle_map[(player_pos - 2 * width) // width, (player_pos - 2 * width) % width] == 0)
        ],
    )

    push_down = dp.Transition(
        name="push down",
        cost=1 + dp.IntExpr.state_cost(),
        effects=[
            (player_pos, player_pos + width),
            (box_pos, box_pos.add(player_pos + 2 * width).remove(player_pos + width)),
        ],
        preconditions=[
            box_pos.contains(player_pos + width) &
            ~box_pos.contains(player_pos + 2 * width) &
            ~(puzzle_map[(player_pos + 2 * width) // width, (player_pos + 2 * width) % width] == 0)
        ],
    )

    push_left = dp.Transition(
        name="push left",
        cost=1 + dp.IntExpr.state_cost(),
        effects=[
            (player_pos, player_pos - 1),
            (box_pos, box_pos.add(player_pos - 2).remove(player_pos - 1)),
        ],
        preconditions=[
            box_pos.contains(player_pos - 1) &
            ~box_pos.contains(player_pos - 2) &
            ~(puzzle_map[(player_pos - 2) // width, (player_pos - 2) % width] == 0)
        ],
    )

    push_right = dp.Transition(
        name="push right",
        cost=1 + dp.IntExpr.state_cost(),
        effects=[
            (player_pos, player_pos + 1),
            (box_pos, box_pos.add(player_pos + 2).remove(player_pos + 1)),
        ],
        preconditions=[
            box_pos.contains(player_pos + 1) &
            ~box_pos.contains(player_pos + 2) &
            ~(puzzle_map[(player_pos + 2) // width, (player_pos + 2) % width] == 0)
        ],
    )

    model.add_transition(move_up)
    model.add_transition(move_down)
    model.add_transition(move_left)
    model.add_transition(move_right)

    model.add_transition(push_up)
    model.add_transition(push_down)
    model.add_transition(push_left)
    model.add_transition(push_right)

    model.add_base_case([box_pos.issubset(goals)])

    #solver = dp.CABS(model, time_limit=100, keep_all_layers=True)
    #solver = dp.CAASDy(model, time_limit=10)
    #solver = dp.WeightedAstar(model, weight = 1.5, time_limit=10)
    #solver = dp.LNBS(model, keep_all_layers = True, time_limit=10)
    solver = dp.DFBB(model, time_limit=10)
    solution = solver.search()

    if solution.is_infeasible:
        return {
            "status": "infeasible",
            "moves": 0,
            "pushes": 0,
            "total_steps": 0,
            "cost": None,
            "optimal": False,
            "time": solution.time
        }
    
    if solution.cost == None:
        return {
            "status": "unsolved",
            "moves": 0,
            "pushes": 0,
            "total_steps": 0,
            "cost": None,
            "optimal": False,
            "time": solution.time
        }

    push = sum(1 for t in solution.transitions if "push" in t.name)
    move = sum(1 for t in solution.transitions if "move" in t.name)

    return {
        "status": "solved",
        "moves": move,
        "pushes": push,
        "total_steps": push + move,
        "cost": solution.cost,
        "optimal": solution.is_optimal,
        "time": solution.time
    }

#Main loop

if __name__ == "__main__":
    folder_path = "Microban"
    i = 1
    results = []

    solved_count = 0
    optimal_count = 0
    total_time = 0.0

    while True:
        file_path = os.path.join(folder_path, f"screen.{i}")
        if not os.path.exists(file_path):
            break

        with open(file_path, "r") as file:
            content = file.readlines()

        print(f"Solving screen.{i}...")

        try:
            result = solve_sokoban(content)
        except Exception as e:
            result = {
                "status": "error",
                "moves": 0,
                "pushes": 0,
                "total_steps": 0,
                "cost": None,
                "optimal": False,
                "time": 0.0
            }
            print(f"Error solving screen.{i}: {e}")

        result["screen"] = i
        total_time += result["time"]
        results.append(result)

        if result["status"] == "solved":
            solved_count += 1
            if result.get("optimal", False):
                optimal_count += 1

        print(f"Result for screen.{i}: {result}\n")
        i += 1

    #Summary

    print("\n=== Summary ===")
    for r in results:
        print(f"Screen {r['screen']:3}: {r['status']} - Moves: {r['moves']}, Pushes: {r['pushes']}, Total: {r['total_steps']}, Cost: {r['cost']}, Optimal: {r.get('optimal', False)}, Time: {r['time']:.3f}s")

    average_time = total_time / solved_count if solved_count > 0 else 0

    print("\n=== Totals ===")
    print(f"Total puzzles processed: {len(results)}")
    print(f"Puzzles solved:          {solved_count}")
    print(f"Puzzles proved optimal:  {optimal_count}")
    print(f"Total time:        {total_time:.2f} seconds")
    print(f"Average solve time:      {average_time:.3f} seconds per puzzle")

    solved = [r for r in results if r['status'] == 'solved']
    puzzle_numbers = [r['screen'] for r in solved]
    solve_times = [r['time'] for r in solved]

    plt.figure(figsize=(10, 5))
    plt.hist(solve_times, bins=15, color='skyblue', edgecolor='black')
    plt.title('Distribution of Solve Times')
    plt.xlabel('Solve Time (seconds)')
    plt.ylabel('Number of Puzzles')
    plt.tight_layout()
    plt.show()