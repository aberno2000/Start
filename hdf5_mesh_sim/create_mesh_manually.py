with open("../results/mesh.txt", "r") as file:
    data = file.readlines()

with open("../results/output.geo", "w") as output_file:
    output_file.write("// Declaring points\n")

    point_id = 1
    line_id = 1
    line_loop_id = 1
    surface_id = 1

    for line in data:
        values = line.split()
        x1, y1, z1 = float(values[1]), float(values[2]), float(values[3])
        x2, y2, z2 = float(values[4]), float(values[5]), float(values[6])
        x3, y3, z3 = float(values[7]), float(values[8]), float(values[9])

        output_file.write(f"Point({point_id}) = {{{x1}, {y1}, {z1}, 1.0}};\n")
        output_file.write(f"Point({point_id + 1}) = {{{x2}, {y2}, {z2}, 1.0}};\n")
        output_file.write(f"Point({point_id + 2}) = {{{x3}, {y3}, {z3}, 1.0}};\n")

        output_file.write(f"Line({line_id}) = {{{point_id}, {point_id + 1}}};\n")
        output_file.write(
            f"Line({line_id + 1}) = {{{point_id + 1}, {point_id + 2}}};\n"
        )
        output_file.write(f"Line({line_id + 2}) = {{{point_id + 2}, {point_id}}};\n")

        output_file.write(
            f"Line Loop({line_loop_id}) = {{{line_id}, {line_id + 1}, {line_id + 2}}};\n"
        )
        output_file.write(f"Plane Surface({surface_id}) = {{{line_loop_id}}};\n")

        point_id += 3
        line_id += 3
        line_loop_id += 1
        surface_id += 1
