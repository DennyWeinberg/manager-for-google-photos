from distutils.core import setup

with open('requirements.txt') as f:
    requs = f.read().splitlines()

setup(name='manager-for-google-photos',
      version='0.0.1',
      author='Denny Weinberg',
      author_email='levion.software@gmail.com',
      url='https://github.com/DennyWeinberg/manager-for-google-photos',
      packages=['google_photos_manager'],
      install_requires=requs
      )
