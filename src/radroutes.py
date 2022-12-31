#!/usr/bin/env python 

import sys
import os
from schema import Schema, SchemaError, Optional, And
import yaml
import fit2gpx
import folium
from folium import plugins

class RadRouter():
    def generate_popup_html(self, coordinates):
        html = " ".join(["<h2>", coordinates['title'].iat[0], "</h2><br><p>", coordinates['description'].iat[0], "</p>"])

        if coordinates['image'].iat[0] is not None:
            html = " ".join([html, "<br><img style = \"width: auto; height: 200px\" src = ",  coordinates['image'].iat[0], ">"])

        return html

    def process_activities(self, path_to_config):
        # Consumes a path to a config file and generates a map.
        activities = self.validate_config(path_to_config)

        segments = activities['activities']['segments']
        directory = activities['activities']['directory']

        conv = fit2gpx.Converter()
        all_coordinates_list = []
        map = folium.Map()

        # convert each file to a dataframe and create a list of dataframes
        for segment in segments:
            segment_path = os.path.join(directory, segment['file_name'])
            _, df_coordinates = conv.fit_to_dataframes(segment_path)
            df_coordinates['file_name'] = segment.get('file_name')
            df_coordinates['title'] = segment.get('title', 'Title')
            df_coordinates['description'] = segment.get('description', 'Description goes here!')
            df_coordinates['image'] = segment.get('image')

            all_coordinates_list.append(df_coordinates)

        self.add_geojson_line(all_coordinates_list, map)

        # folium.LayerControl().add_to(map)
        map.save('map.html')
        print('Map saved.')

    def validate_config(self, path_to_config):
        try:
            with open(path_to_config, 'r') as config_file:
                activities = yaml.safe_load(config_file)
            print(f'Successfully opened config file: {path_to_config}')
        except IOError:
            print(f'Could not find file: {path_to_config}')
            sys.exit(1)

        # need to add check that individual files exist
        expected_schema = Schema({
            'activities': {
                'directory': And(os.path.exists, error='Invalid directory'),
                'segments': [{
                    'file_name': str,
                    Optional('title'): str,
                    Optional('description'): str,
                    Optional('image'): str
                }]
            }
        })

        try:
            expected_schema.validate(activities)
            print('Config file is valid.')
        except SchemaError as se:
            print(se)
            sys.exit(1)

        return activities

    def add_geojson_line(self, coordinates_list, map):
        # step 1: convert antpaths to geojson
        # step 2: oreo adds popups to geojson
        # step 3: oreo adds markers
        # step 4: animate / play button

        segment_features = []

        for coordinates in coordinates_list:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coordinates[['longitude', 'latitude']].values.tolist(),
                },
                'properties': {
                    'weight': 5,
                    'html': self.generate_popup_html(coordinates),
                },
            }

            segment_features.append(feature)

        geojson_features = {
            'type': 'FeatureCollection',
            'features': segment_features
        }

        segment_layer = folium.GeoJson(
            geojson_features,
            zoom_on_click=True,
            highlight_function=lambda x: {
                'color': 'green',
                'weight': 10,
            },
            popup=folium.GeoJsonPopup(
                fields=['html'],
                labels=False,
            )
        ).add_to(map)

        map.fit_bounds(segment_layer.get_bounds())

if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     raise ValueError("Expected path to config file as argument")

    rr = RadRouter()
    rr.process_activities('/workspaces/rad-routes/examples/activity_files/activities.yml')