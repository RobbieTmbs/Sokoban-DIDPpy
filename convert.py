def split_xsb_levels(input_path):
    with open(input_path, 'r') as f:
        lines = f.readlines()

    levels = []
    current_level = []

    for line in lines:
        line = line.rstrip('\n')

        if line.startswith(';'):
            continue

        if line.strip() == "":
            if current_level:
                levels.append('\n'.join(current_level))
                current_level = []
        else:
            current_level.append(line)

    if current_level:
        levels.append('\n'.join(current_level))

    for i, level in enumerate(levels, start=1):
        filename = f"screen.{i}"
        with open(filename, 'w') as out:
            out.write(level + '\n')
        print(f"Wrote {filename}")

split_xsb_levels("Microban/Microban_155.xsb")