from distutils.core import setup

with open('requirements.txt') as f:
    requs = f.read().splitlines()

setup(name='backup-for-google-photos',
      version='0.0.1',
      author='Denny Weinberg',
      author_email='levion.software@gmail.com',
      url='https://github.com/DennyWeinberg/backup-for-google-photos',
      packages=['backup_google_photos'],
      install_requires=requs
      )
