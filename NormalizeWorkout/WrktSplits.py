#!/usr/bin/env python
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

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import util.timeConv as tc # Need to use when running ProcessWrktFile.py
# import NormalizeWorkout.util.timeConv as tc

def group_actv(df, group_by_field):
    '''
    Group activity in the passed df Data Frame. Will perform group by
     on the group_by_field.
    Will calculate the below fields
    '''

    df_edit = df.copy()
    df_edit['ele_up'] = df[df['delta_ele_ft']>0]['delta_ele_ft']
    df_edit['ele_down'] = df[df['delta_ele_ft']<0]['delta_ele_ft']

    grouped_df = (df_edit.groupby([group_by_field])
        .agg(max_time=('dur_sec', 'max')
             , avg_hr = ('hr', 'mean')
             , ele_up = ('ele_up','sum')
             , ele_down = ('ele_down','sum')
             , sum_ele = ('delta_ele_ft','sum')
             , max_dist = ('dist_mi','max')
             , lat = ('latitude', 'last')
             , lon = ('longitude', 'last')
        )
        .reset_index()
    )

    '''
    Set min_time and min_dist to the max of previous split
    '''
    grouped_df_copy = grouped_df.copy()
    grouped_df['prev_val'] = grouped_df.index.values - 1
    # grouped_df_copy.rename(columns={group_by_field: 'group_by_field'}, inplace=True)
    grouped_df_copy['index_orig'] = grouped_df_copy.index.values

    grouped_min_dist_df = pd.merge(grouped_df[[group_by_field,'prev_val']],
                             grouped_df_copy[['max_dist','max_time','index_orig']],
                             how='left',
                             left_on='prev_val', right_on='index_orig')
    grouped_min_dist_df.rename(columns={'max_dist': 'min_dist','max_time':'min_time'}, inplace=True)
    grouped_df = grouped_df.merge(right=grouped_min_dist_df, how='inner', left_on=group_by_field, right_on=group_by_field)
    grouped_df.fillna({'min_dist':0, 'min_time':0}, inplace=True)

    '''
    Calculate the grouped values
    '''
    grouped_df['dur_sec'] = grouped_df['max_time'] - grouped_df['min_time']
    grouped_df['dist_mi'] = grouped_df['max_dist'] - grouped_df['min_dist']

    grouped_df['pace'] = grouped_df['dur_sec'] / grouped_df['dist_mi']
    grouped_df['pace'] = grouped_df['pace'].replace(np.inf, 0).fillna(0)

    grouped_df['dur_str'] = tc.seconds_to_time_str(grouped_df, 'dur_sec', 'hms')
    grouped_df['pace_str'] = tc.seconds_to_time_str(grouped_df, 'pace', 'hms')

    grouped_df['dist_mi'] = grouped_df['dist_mi'].round(2).fillna(0)
    grouped_df['avg_hr'] = grouped_df['avg_hr'].round(2)
    grouped_df['ele_up'] = grouped_df['ele_up'].round(2)
    grouped_df['ele_down'] = grouped_df['ele_down'].round(2)
    grouped_df['sum_ele'] = grouped_df['sum_ele'].round(2)

    return grouped_df[[group_by_field,'dur_sec', 'dur_str', 'dist_mi' \
        , 'pace', 'pace_str' \
        , 'avg_hr' \
        , 'ele_up', 'ele_down', 'sum_ele' \
        , 'min_time','max_time','min_dist', 'max_dist' \
        , 'lat', 'lon' \
        ]]
