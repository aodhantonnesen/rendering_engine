from pathlib import Path

# This file should have 2 major functions that can be called. The first will take the following input(s):
#
# name <- String of the obj file stored in the "models" folder. This string will not contain ".obj"
#
# This function will have the following output(s):
#
# vertex positions <- list of 3-tuples, (x, y, z)
# face vertices <- list of 3-tuples, (i0, i1, i2), these are the index of the respective vertex
# materials <- see below 
#   EX: "newmtl,Blue,Ns,250.000000,Kd,0.148594,0.146037,0.800126"
#   If a material has multiples values (rgb, or something else), only the first value will be predated with a title.
#   To get a particular materials, split the string on commas, then iterate until you find the title you are looking for, 
#   and then read until another title appears.
#
# The next major function will take the output of the first function as an input, and will return an interleaved numpy array 
# as we will pass it to OpenGL
# The reason we want to hide this all away inside this seperate file 
# is so that we can (temporarily) pretend some of this data (that we should be parsing) is not there
# or hardcode it with simple values


def material_as_list(materials: str, name): # Done, do not change
    for mat in materials:
        if not mat.startswith('newmtl,' + name):
            continue
        tmp = mat.split(',')
        Ns = float(tmp[3])
        KaX, KaY, KaZ = float(tmp[5]), float(tmp[6]), float(tmp[7])
        KdX, KdY, KdZ = float(tmp[9]), float(tmp[10]), float(tmp[11])
        KsX, KsY, KsZ = float(tmp[13]), float(tmp[14]), float(tmp[15])
        KeX, KeY, KeZ = float(tmp[17]), float(tmp[18]), float(tmp[19])
        Ni = float(tmp[21])
        d = float(tmp[23])

        return [Ns, KaX, KaY, KaZ, KdX, KdY, KdZ, KsX, KsY, KsZ, KeX, KeY, KeZ, Ni, d]
    
    raise ValueError('Name value provided not found in materials string!')


def interleave(vertices, textures, normals, faces, materials):  # Works
    # We want the interleave to be in the following format:
    # v0, t0, n0, Ns0, KaR0, KaG0, KaB0, KdR0, KdG0, KdB0, KsR0, KsG0, KsB0, KeR0, KeG0, KeB0, Ni0, d0, v1, t1...
    # most of this data is not useful at the moment, but we will parse it all so we don't have to come back

    interleaved = []

    for face in faces:
        for i in range(3):
            interleaved.append(vertices[int(face[0][i])])
            interleaved.append(textures[int(face[1][i])])
            interleaved.append(normals[int(face[2][i])])
            interleaved.extend(material_as_list(materials, face[3]))
    
    return interleaved


def load_mat(file_path: Path):                  # This was tested, works beautifully. DO NOT CHANGE WITHOUT TESTING
    materials = []

    mat_string = ""

    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith("illum "):       # starting with the end here
                materials.append(mat_string)    # throw the string we've made into the list
            elif line.startswith("newmtl "):    # this will be the first thing we care about, new material
                mat_string = ""                 # reset the string we will append to the list
                mat_string += "newmtl,"         
                mat_string += line[7:-1]        # adding the name of the new material to the string
                mat_string += ","               
            elif line.startswith(" "):          # null case
                continue
            elif line.startswith("#"):          # comment
                continue
            elif line.startswith('\n'):         # null case
                continue
            else:                               # data that isn't the beginning of a new material
                tmp = line[:-1]
                tmp = tmp.split(" ")            # split the string
                for sub in tmp:                 
                    mat_string += sub           # add it to the string
                    mat_string += ","
    
    return materials


def load_obj(file_path):
    # This function takes a file path to a .obj and does a few things
    # first and foremost, it opens the file and finds any dependencies
    # it then opens those and stores the material data needed

    # Once all that is done, it goes through and parses the following data:
    # Vertex positions (x, y, z)
    # Normals [x, y, z]
    # Texture positions (u, v)
    # Faces
    #   Faces are complicated
    #   Faces may be made of n vertices
    #   We need to do fan triangulaization to turn these "n-gons" into n-2 triangles
    #   Each vertex will have an associated normal and texture position
    #   Each face will also have an associated texture.
    #   We will need to store those in a particular way, as described below.

    vertices = []
    normals = []
    textures = []

    faces = []

    # The "faces" list will be stored as follows:
    #   faces = [
    #   [[v0, v1, v2], [t0, t1, t2], [n0, n1, n2], "material"],     // Face 0
    #   [[v0, v1, v2], [t0, t1, t2], [n0, n1, n2], "material"],     // Face 1
    #   [[v0, v1, v2], [t0, t1, t2], [n0, n1, n2], "material"]      // Face 2
    #   ]
    # The sublists on each line contain integer indecies for the above lists.

    materials = []

    # The "materials" list will be a list of strings, as described above.

    current_mat = None

    with open(file_path, 'r') as f:
        # This beginning part is (mostly) quite simple. Each if / elif just parses a normal line of data from our .obj
        for line in f:
            # This is the part that parses the mtl files,
            # since this is another file, we have another function that does the heavy lifting for us.
            if line.startswith('mtllib '):
                materials.extend(load_mat(Path("models") / f"{line[7:-1]}"))
            elif line.startswith('v '):
                tmp = line[2:]
                tmp = tmp.split(" ")
                for n in tmp:
                    vertices.append(float(n))
            elif line.startswith('vn '):
                tmp = line[3:]
                tmp = tmp.split(" ")
                for n in tmp:
                    normals.append(float(n))
            elif line.startswith('vt '):
                tmp = line[3:]
                tmp = tmp.split(" ")
                for n in tmp:
                    textures.append(float(n))

            # Now here's where things get interesting:
            # We start by finding which texture is current
            elif line.startswith('usemtl '):
                current_mat = line[7:-1]
            # Then we start processing faces
            elif line.startswith('f '):
                tmp = line[2:-1]
                tmp = tmp.split(' ')

                triangle_list = []
                
                first = tmp[0]
                prev = None

                # We cannot pass n-gons to OpenGL so we do fan triangularization to the potential n-gons
                for cur in tmp:
                    if prev == None:
                        prev = cur
                        continue
                    elif first == prev:
                        prev = cur
                        continue
                    triangle_list.append([first, prev, cur])
                    prev = cur
                
                for triangle in triangle_list:
                    tmpvert = []
                    tmpnorm = []
                    tmptex = []
                    for vert in triangle:
                        vert = vert.split('/')
                        tmpvert.append(vert[0])
                        tmptex.append(vert[1])
                        tmpnorm.append(vert[2])
                    faces.append([tmpvert, tmptex, tmpnorm, current_mat])
    return vertices, textures, normals, faces, materials


def load_model(name: str) -> list:   # This function should be the function that is called from outside.
    """This function taken an input of a .obj file name (without the file extension) and returns an interleaved list. \n
    The list contains the ordered data for each vertex of each triangle in the model. \n
    Format: v0, t0, n0, Ns0, KaR0, KaG0, KaB0, KdR0, KdG0, KdB0, KsR0, KsG0, KsB0, KeR0, KeG0, KeB0, Ni0, d0, v1, t1..."""
    a ,b ,c, d, e = load_obj(Path("models") / f"{name}.obj")
    return interleave(a, b, c, d, e)

