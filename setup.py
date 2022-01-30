import setuptools

setuptools.setup(name='NormalizeWorkout',
      version='0.1',
      description='Normalize Workout to a Pandas dataframe from .fit or rungap.json file',
      # url='http://github.com/storborg/funniest',
      author='Mike Bromberek',
      # author_email='',
      license='BSD 3-Clause License',
      # packages=setuptools.find_packages(),
      packages=['NormalizeWorkout','NormalizeWorkout.dao','NormalizeWorkout.parse','NormalizeWorkout.util'],
      install_requires=['numpy','pandas','fitdecode']
      # zip_safe=False
)
