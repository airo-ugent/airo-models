"""Functions to generate URDFs for basic geometric primitives.

This module provides convenient functions to create URDF representations of basic geometric shapes
(box, cylinder, sphere, and mesh). Each shape module exposes four functions:

1. `{shape}_geometry_dict(...)` - Returns a dictionary representation of the geometry element.
   Use this when you need to embed the geometry in a more complex URDF structure.

2. `{shape}_dict(...)` - Returns a dictionary representation of a complete single-link URDF model.
   Use this when you want to manipulate the URDF as a dictionary (e.g., to edit properties).

3. `{shape}_urdf(...)` - Returns the URDF as an XML string.
   Use this when you need the URDF in XML format, for example to write to a file.

4. `{shape}_urdf_path(...)` - Generates a URDF file and returns the path to the temporary file.
   Use this when you need to load the URDF into a simulation or robotics library.

All shape functions accept an `rgba` parameter (a tuple of floats in [0, 1]) to set the visual
color and transparency. The default is white (1.0, 1.0, 1.0, 1.0).

The URDF coordinates follow the modeling convention: X+ forward, Z+ up. The origin of all
generated primitives is at (0, 0, 0) with no rotation.

Examples:

    Generate a box URDF as a string::

        import airo_models

        box_urdf_str = airo_models.box_urdf(size=(0.5, 1.0, 2.0), name="my_box", rgba=(1.0, 0.0, 0.0, 1.0))
        print(box_urdf_str)

    Get a temporary file path to a sphere URDF for use with simulation libraries::

        sphere_path = airo_models.sphere_urdf_path(radius=0.1, name="ball")
        # Use sphere_path with libraries like Drake, CoppeliaSim, etc.

    Create a cylinder URDF as a dictionary for further manipulation::

        cyl_dict = airo_models.cylinder_dict(length=1.0, radius=0.05, name="rod")
        # Modify cyl_dict as needed
        urdf_str = airo_models.urdf.dict_to_xml_str(cyl_dict)
"""
