from setuptools import setup, find_packages

setup(
   name='rplab_image_analysis',
   version='1.0.0',
   description='Image analysis library of Parthasarathy Lab at University of Oregon',
   author='Jonah Sokoloff',
   author_email='jonahs@uoregon.edu',
   packages=find_packages(),
   install_requires=['wheel', 'numpy', 'scikit-image', 'tifffile', 'psutil', 'natsort']
)