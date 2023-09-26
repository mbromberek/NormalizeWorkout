#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import os,glob,shutil
import re
import datetime, time
import math

# 3rd party classes
import numpy as np
import pandas as pd

MILES_IN_KILOMETERS = 0.621371
METERS_IN_KILOMETERS = 1000
METERS_TO_FEET = 3.28084

'''

'''
def normalize_activity(data):
    activityPts = data['laps'][0]['points']
    eventTyps = data['events']
    
    # Initialize Pandas DataFrames
    df_events = pd.DataFrame(eventTyps)
    df_activity = pd.DataFrame(activityPts)
    
    df_events['start_dttm'] = pd.to_datetime(df_events['start'], unit='s')
    df_events['end_dttm'] = pd.to_datetime(df_events['end'], unit='s')
    df_activity['dttm'] = pd.to_datetime(df_activity['time'], unit='s')
    
    activity = cleanup_values(df_activity)
    
    pause_times = get_pause_times(df_events)
    activity = mark_pause_records(activity, pause_times)
    activity = mark_resumes(activity, df_events)
    
    activity = mark_laps(activity, df_events)
    activity = mark_distances(activity)
    
    activity = calc_elevation_changes(activity)
    activity = drop_pause_records(activity)
    activity = calc_record_duration(activity)
    activity = normalize_field_names(activity)
    
    return activity, pause_times
    
    
def cleanup_values(activity_df):
    '''
    - Forward fill distance and elevation
    '''
    activity = activity_df.copy()
    activity['dist'].ffill(inplace=True)
    activity['ele'].ffill(inplace=True)
    
    return activity
    
'''
Combines pause and resume records to have one reow with start and end time of each pause of activity
'''
def get_pause_times(events_df):
    event_pause_resume = events_df.loc[events_df['type'].isin(['pause','resume'])].copy()
    event_pause_resume.drop(['end','end_dttm'], axis=1, inplace=True)
    
    '''
    Merge pause row with resume row below it to get the start to end time of pause
    '''
    event_pause_resume['end'] = event_pause_resume['start'].shift(-1)
    event_pause_resume.dropna(subset=['end'],inplace=True)
    event_pause_resume['end'] = event_pause_resume['end'].astype('int64')
    event_pause_resume['end_dttm'] = pd.to_datetime(event_pause_resume['end'], unit='s')
    event_pause_resume['dur'] = event_pause_resume['end'] - event_pause_resume['start']
    
    event_pause_times = event_pause_resume = event_pause_resume.loc[event_pause_resume['type'].isin(['pause'])].copy()
    event_pause_times = event_pause_times.reset_index(drop=True)
    event_pause_times.index = event_pause_times.index+1
    
    # event_pause_times.to_csv('/Users/mike/Downloads/event_pause_times.csv')
    return event_pause_times
    

'''
- Mark pause sections with pause column
- Mark which resume section each record is in
'''
def mark_pause_records(df_activity, event_pause_times):
    activity = df_activity.copy()

    '''
    Merge pause markers into activity
    '''    
    pause_range = event_pause_times[['start','end']].values.tolist()
    pause_choices = event_pause_times.index.values.tolist()
    activity_pause_conditions = []
    for i in range(len(pause_range)):
        condition = activity['time'].ge(pause_range[i][0]) & activity['time'].le(pause_range[i][1])
        activity_pause_conditions.append(condition)
    activity['pause'] = np.select(activity_pause_conditions, pause_choices)
    
    return activity

def mark_resumes(activity_df, events_df):
    activity = activity_df.copy()
    '''
    Merge Resume Splits into Activity
    '''
    event_pause = events_df.loc[events_df['type'].isin(['pause'])].copy()
    event_pause = event_pause.reset_index(drop=True)
    
    pause_conditions = event_pause['start'].tolist()
    pause_choices = event_pause.index.values.tolist()
    activity_pause_conditions = []
    for i in range(len(pause_conditions)-1):
        condition = activity['time'].ge(pause_conditions[i]) & activity['time'].lt(pause_conditions[i+1])
        activity_pause_conditions.append(condition)
    activity_pause_conditions.append(activity['time'].ge(pause_conditions[-1]))
    activity['resume'] = np.select(activity_pause_conditions, pause_choices)
    
    return activity

def mark_laps(activity_df, events_df):
    '''    
    Merge marker/lap into activity
    '''
    actvity = activity_df.copy()
    
    # Get start time as int and date/time
    # This is needed for setting first marker
    wrkt_start = actvity['time'].min()
    wrkt_start_dttm = actvity['dttm'].min()

    
    df_laps = events_df.loc[events_df['type'] =='marker'].reset_index(drop=True)
    
    df_laps.loc[-1] = ['marker', wrkt_start, wrkt_start, wrkt_start_dttm, wrkt_start_dttm] # add first marker at start of workout
    df_laps.index = df_laps.index +1 #shifting index
    df_laps = df_laps.sort_index() # sorting on index
    

    lap_conditions = df_laps['start'].tolist()
    lap_choices = df_laps.index.values.tolist()
    activity_lap_conditions = []
    for i in range(len(lap_conditions)-1):
        condition = actvity['time'].ge(lap_conditions[i]) & actvity['time'].lt(lap_conditions[i+1])
        activity_lap_conditions.append(condition)
    activity_lap_conditions.append(actvity['time'].ge(lap_conditions[-1]))
    actvity['lap'] = np.select(activity_lap_conditions, lap_choices)
    
    return actvity
    
    
def mark_distances(activity_df):
    
    activity = activity_df.copy()
    activity.rename(columns={'dist':'dist_m'},inplace=True)
    activity['dist_m'].fillna(0, inplace=True)
    activity['dist_km'] = activity['dist_m'] / METERS_IN_KILOMETERS
    activity['dist_mi'] = activity['dist_km'] * MILES_IN_KILOMETERS
    
    activity['delta_dist_mi'] = activity['dist_mi']-activity['dist_mi'].shift(+1)
    activity['delta_dist_km'] = activity['dist_km']-activity['dist_km'].shift(+1)
    activity['delta_dist_mi'].fillna(0, inplace=True)
    activity['delta_dist_km'].fillna(0, inplace=True)
    
    # Get mile number
    i = 1
    conditions = [activity['dist_mi'].lt(i)]
    choices = [i]
    while i <= math.ceil(activity['dist_mi'].max()):
        conditions.append(activity['dist_mi'].ge(i) & activity['dist_mi'].lt(i+1))
        choices.append(i+1)
        i=i+1
    activity['mile'] = np.select(conditions, choices, default=0)
    
    # Get Kilometer number
    i = 1
    conditions = [activity['dist_km'].lt(i)]
    choices = [i]
    while i <= math.ceil(activity['dist_km'].max()):
        conditions.append(activity['dist_km'].ge(i) & activity['dist_km'].lt(i+1))
        choices.append(i+1)
        i=i+1
    activity['kilometer'] = np.select(conditions, choices, default=0)
    
    return activity
    
    
def calc_elevation_changes(activity_df):
    activity = activity_df.copy()
    
    activity.rename(columns={'ele':'altitude_m'},inplace=True)
    activity['altitude_m'].fillna(0, inplace=True)
    activity['altitude_ft'] = activity['altitude_m'] * METERS_TO_FEET
    
    activity['delta_ele_ft'] = activity['altitude_ft']-activity['altitude_ft'].shift(+1)
    activity['delta_ele_ft'].fillna(0, inplace=True)
    
    activity['ele_up'] = activity[activity['delta_ele_ft']>0]['delta_ele_ft']
    activity['ele_down'] = activity[activity['delta_ele_ft']<0]['delta_ele_ft']
    
    return activity
    
    
def drop_pause_records(activity_df):
    '''
    Drop records that are part of pause, then remove pause column
    '''
    activity = activity_df.copy()
    
    remove_rows_index = activity[activity['pause'] != 0].index
    activity.drop(remove_rows_index, inplace=True)
    activity.drop(columns=['pause'], inplace=True)
    
    return activity
    
def calc_record_duration(activity_df):
    '''
    Get duration of each record
    '''
    activity = activity_df.copy()
    
    activity.reset_index(drop=True, inplace=True)
    activity['dur_sec'] = activity.index.values
    
    return activity
    
def normalize_field_names(activity_df):
    # # Normalize field names
    activity = activity_df.copy()
    activity.rename(columns={'lat':'latitude','lon':'longitude','dttm':'timestamp'},inplace=True)
    return activity
    
