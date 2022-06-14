```
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
```
# NormalizeWorkout

Take workout data from RunGap JSON file or .FIT file and create a DataFrame of the data. Can then save the DataFrame as a .pickle or .CSV file.

ProcessWrktFile.py can be used for testing and saving a file.

### Setup Environment
```
python3 -m venv $HOME/.virtualenvironments/TestEnv
source $HOME/.virtualenvironments/TestEnv/bin/activate

pip install wheel
pip install .
pip install git+https://github.com/mbromberek/NormalizeWorkout.git
```

### Testing
```
import NormalizeWorkout.parse.fitParse as fitParse
dir='/Users/mikeyb/Downloads/2022-01-22_07-04-48_co_441002095250800640_mod'
lapsDf, pointsDf = fitParse.get_dataframes(dir + '/' + '2022-01-22_07-04-48_co_441002095250800640.fit')
actv_df = fitParse.normalize_laps_points(lapsDf, pointsDf)

dir='/Users/mikeyb/Library/Mobile Documents/iCloud~com~rungap~RunGap/Documents/Export_test/2019-06-15_07-05-44_hk_1560600344'
lapsDf, pointsDf = fitParse.get_dataframes(dir + '/' + '2019-06-15_07-05-44_hk_1560600344.rungap.json')
```
