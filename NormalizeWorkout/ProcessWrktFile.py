#!/usr/bin/env python
# coding: utf-8
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

# First party classes
import os,glob,shutil, subprocess
import re
import datetime, time
import configparser
import sys, getopt
import logging
import logging.config

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import dao.files as fao
import util.timeConv as tc
# import parse.rungapParse as rgNorm
import parse.hkParse as hkNorm
import parse.fitParse as fitParse
import parse.rungapMetadata as rungapMeta
import WrktSplits

# tempDir = '/tmp/' #default to /tmp
logging.config.fileConfig('../logging.conf')
logger = logging.getLogger()

def printArgumentsHelp():
    print ('WorkoutAnalyze.py -i <inputfile> -o <outputdir>')
    print ("-i, --ifile arg  : Input filename to process")
    print ("-o, --odir arg   : Output directory for results")
    print ("--splits arg     : Segments to split up file, ")
    print ("                    options are mile, kilometer, segment, pause, custom, all")
    print ("                    all option will generate mile, kilometer, segment, pause")
    print ("                    default is mile, segment, pause")

def getSplitOptions(arg):
    '''
    Parameger arg: comma delimited list of arguments for splitting the workout

    Converts passed in split argument to lower case and splits on comma
    Parses each argument doing needed transformations before adding to a list.
    Prints to the console if any arguments are invalid
    Removes duplicates from list of split arguments

    Returns list of split arguments
    '''
    splitOptions = []
    splitArgs = arg.lower().split(',')
    for split in splitArgs:
        if split == 'all':
            splitOptions.extend(['mile','lap','resume','kilometer'])
        elif split == 'pause':
            splitOptions.append('resume')
        elif split in ('custom','mile','lap','kilometer'):
            splitOptions.append(split)
        else:
            print("Invalid split argument: " + split)
    return(list(dict.fromkeys(splitOptions)))


def main(argv):
    '''
    Steps
    1. Get config details
    2. Extract files
    3. Load files into activities and events data frames
    4. Clean up and merge the activities and events data frames
    5. Group activities by different splits
    6. Export activiies grouped by splits to CSV files
    '''
    config = configparser.ConfigParser()
    # progDir = os.path.dirname(os.path.abspath(__file__)) #might need to use this in actual Python script, but does not work in Jupyter Notebook
    progDir = os.path.abspath('')
    print(progDir)
    config.read(progDir + "/config.txt")

    logger.info('ProcessWrktFile Start')

    tempDir = config['wrkt_analyze_inputs']['temp_dir']
    outDir = config['wrkt_analyze_outputs']['dir']

    customSplit = False
    splitOptions = []
    filename = ''

    fao.clean_dir(tempDir)

    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=", "odir=", "split="])
    except getopt.GetoptError:
        printArgumentsHelp()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printArgumentsHelp()
            sys.exit()
        elif opt in ("-i", "--ifile"):
            filename = arg
        elif opt in ("-o", "--odir"):
            outDir = arg
        elif opt in ('--split'):
            splitOptions = getSplitOptions(arg)
    if splitOptions == []:
        splitOptions = config['wrkt_analyze']['dflt_split_opt'].split(',')

    if filename == '':
        filename = os.path.join(config['rungap']['backup_dir'], fao.getLatestFile(config['rungap']['backup_dir']))
    logger.info('Input file: ' + filename)
    logger.info('Split arguments: ' + str(splitOptions))

    fao.extract_files(filename, tempDir)

    if fao.file_with_ext(tempDir, ext='fit') != '':
        logger.info('fit file exists')
        fitFile = fao.file_with_ext(tempDir, ext='fit')
        lapsDf, pointsDf = fitParse.get_dataframes(tempDir + '/' + fitFile)
        actv_df = fitParse.normalize_laps_points(lapsDf, pointsDf)
    elif fao.file_with_ext(tempDir, ext='rungap.json') != '':
        logger.info('Rungap JSON file')
        data = fao.get_workout_data(tempDir)
        actv_df, pause_times_df = hkNorm.normalize_activity(data)
    else:
        logger.info('No file to process')
        sys.exit(-1)

    dataJson = rungapMeta.get_workout_data(tempDir)
    wrktStrtTmStr = dataJson['startTime']['time']
    wrktType = rungapMeta.get_wrkt_type(dataJson)
    wrktSrc = dataJson['source'].replace(' ','-').lower()
    wrktStrtTm = datetime.datetime.strptime(wrktStrtTmStr, '%Y-%m-%dT%H:%M:%SZ')
    # logger.info('Workout Start Time: {}'.format(wrktStrtTmStr))
    # logger.info('Workout Year: {}'.format(wrktStrtTm.strftime('%Y')))
    # logger.info('Workout Month: {}'.format(wrktStrtTm.strftime('%m')))
    wrktDirNm = wrktStrtTm.strftime('%Y-%m-%d_%H%M%S') + '_' + wrktType + '_' + wrktSrc
    logger.info('Workout folder name: {}'.format(wrktDirNm))

    fao.save_df(actv_df, outDir,'activity', frmt=['csv','pickle'])

    '''
    Group activities by different splits
    '''
    splitDict = {}
    for split in splitOptions:
        splitDict[split] = WrktSplits.group_actv(actv_df, split)

    '''
    Export data frames to files for review
    '''
    for split in splitOptions:
        fao.save_df(splitDict[split], outDir, split + '_split', frmt=['csv','pickle'])

    fao.clean_dir(tempDir)

    logger.info('ProcessWrktFile End')


if __name__ == '__main__':
	main(sys.argv[1:])
