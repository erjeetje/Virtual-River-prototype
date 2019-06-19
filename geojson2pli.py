import pathlib

import geojson
import click
import mako.template

pli_template_text = '''
%for feature in features:
${feature.id}
${len(feature.geometry)} 2
%for point in feature.geometry.coordinates:
${point[0]} ${point[1]}
%endfor
%endfor
'''

structures_template_text = '''
%for feature in features:

[structure]
type                  = weir                # Type of structure
id                    = ${feature.id}              # Name of the structure
polylinefile          = ${feature.properties.pli_filename}          # *.pli; Polyline geometry definition for 2D structure
crest_level           = ${crest_level}            # Crest height in [m]
lat_contr_coeff       = 1                   # Lateral contraction coefficient in 
%endfor
'''

@click.command()
@click.argument('input', type=click.File('rb'))
def geojson2pli(input):
    """convert geojson input (FeatureCollection of linestring features) to a pli file"""
    path = pathlib.Path(input.name)
    structures_path = path.with_suffix('.ini').relative_to(path.parent)
    pli_path = path.with_suffix('.pli').relative_to(path.parent)
    collection = geojson.load(input)
    pli_template = mako.template.Template(pli_template_text)
    with pli_path.open('w') as f:
        rendered = pli_template.render(features=collection.features)
        f.write(rendered)
    structures_template = mako.template.Template(structures_template_text)
    with structures_path.open('w') as f:
        rendered = structures_template.render(features=collection.features, crest_level=0, pli_filename=pli_path)
        f.write(rendered)
    
    

if __name__ == '__main__':
    geojson2pli()