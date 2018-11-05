import cStringIO


try:
    import svgwrite
    have_svg_write = True
except ImportError:
    have_svg_write = False


def generate_map_svg(reader):
    ''' Generate SVG xml of map's polygon wireframe '''

    if not have_svg_write:
        raise Exception('svgwrite not installed')

    # Calculate maximums for image width/height
    max_vertex_x = -1
    max_vertex_y = -1

    # Many coordinates are under 0, get distance from 0 for correction so the minimum will always be 0
    min_vertex_x_for_correction = min(vertex.x for poly in reader.polygons for vertex in poly.Vertexes)
    min_vertex_y_for_correction = min(vertex.y for poly in reader.polygons for vertex in poly.Vertexes)

    for poly in reader.polygons:
        for vertex in poly.Vertexes:

            # Take into account corrections
            if min_vertex_x_for_correction < 0:
                vertex.x += -min_vertex_x_for_correction

            if min_vertex_y_for_correction < 0:
                vertex.y += -min_vertex_y_for_correction

            # And determine width/height of image
            if vertex.x > max_vertex_x:
                max_vertex_x = vertex.x

            if vertex.y > max_vertex_y:
                max_vertex_y = vertex.y

    dimensions = (int(max_vertex_x), int(max_vertex_y))

    # Colors to match the bootswatch theme we use
    polygon_fill_color = '#3e444c'
    polygon_stroke_color = '#000'

    dwg = svgwrite.Drawing(
        filename=None,  # Filename is unused as we just grab the generated xml rather than saving the image somewhere
        profile='tiny',
        viewBox='0 0 %d %d' % dimensions,  # Allow us to automatically scale down the huge poly coordinate locations
        preserveAspectRatio='xMidYMid meet')  # Center it uniformly in the browser's viewport

    for poly in reader.polygons:
      dwg.add(dwg.polygon(
          points=[(vertex.x, vertex.y) for vertex in poly.Vertexes],
          fill=polygon_fill_color,
          stroke=polygon_stroke_color))

    handle = cStringIO.StringIO()
    dwg.write(handle, False)
    return handle.getvalue()
