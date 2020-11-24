from distutils.core import setup

with open('requirements.txt') as f:
    requs = f.read().splitlines()

setup(name='aynil-for-google-photos',
      version='0.0.1',
      author='Denny Weinberg',
      author_email='levion.software@gmail.com',
      url='https://github.com/DennyWeinberg/aynil-for-google-photos',
      packages=['aynil_google_photos'],
      install_requires=requs
      )
