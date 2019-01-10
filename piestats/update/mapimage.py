# Colors to match the bootswatch theme we use
polygon_fill_color = '#3e444c'
polygon_stroke_color = '#000'

poly_tmpl = '<polygon fill="{fill}" points="{points}" stroke="{stroke}" />'
svg_tmpl = '''<?xml version="1.0" encoding="utf-8" ?>
<svg baseProfile="tiny" height="100%" preserveAspectRatio="xMidYMid meet" version="1.2" viewBox="{viewbox}"
      width="100%" xmlns="http://www.w3.org/2000/svg" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xlink="http://www.w3.org/1999/xlink">
{polys}
</svg>'''


def get_map_xml(dimensions, reader):
    return svg_tmpl.format(
        viewbox='0 0 %d %d' % dimensions,
        polys=''.join(poly_tmpl.format(
            fill=polygon_fill_color,
            stroke=polygon_stroke_color,
            points=' '.join('{v.x},{v.y}'.format(v=vertex)
                            for vertex in polygon.Vertexes)) for polygon in reader.polygons))


def generate_map_svg(reader):
    ''' Generate SVG xml of map's polygon wireframe '''

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

    return get_map_xml(dimensions, reader)
