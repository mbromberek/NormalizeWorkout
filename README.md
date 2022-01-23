python3 -m venv $HOME/.virtualenvironments/TestEnv
source $HOME/.virtualenvironments/TestEnv/bin/activate

pip install wheel
pip install .

### Testing
```
import NormalizeWorkout.parse.fitParse as fitParse
dir='/Users/mikeyb/Downloads/2022-01-22_07-04-48_co_441002095250800640_mod'
lapsDf, pointsDf = fitParse.get_dataframes(dir + '/' + '2022-01-22_07-04-48_co_441002095250800640.fit')
actv_df = fitParse.normalize_laps_points(lapsDf, pointsDf)
```
