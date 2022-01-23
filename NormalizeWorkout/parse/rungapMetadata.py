# coding: utf-8
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
"""
Functions for normalizing the workout from RunGap JSON files
Uses pandas and numpy to process and normalize the data.
"""

# First party classes
import os,glob,shutil
import re
import datetime, time
import json

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import util.timeConv as tc

def get_workout_data(curr_dir):
    """
    Parses files and directories in the passed curr_dir till finds a file
    that ends in metadata.json. Then loads that json data to a Dictionary.
    Returns the Dictionary storing the json data.
    """
    data = ''
    jsonFileRegex = re.compile(r'(metadata.json)$')
    jsonExtRegex = re.compile(r'(.json)$')

    for filename in os.listdir(curr_dir):
        if jsonFileRegex.search(filename):
            with open(curr_dir + filename) as data_file:
                data = json.load(data_file)
                break
    return data

# def normalize_workout(dataJson):
#     wrkt_meta_df = pd.DataFrame(dataJson)
#     return wrkt_meta_df

def get_wrkt_type(dataJson):
    return dataJson['activityType']['internalName'].replace(' ','-').lower()
