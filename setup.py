from setuptools import setup, Extension

module = Extension('pdfcracker',
                  sources=['pdf_cracker.cpp'],
                  extra_compile_args=['-std=c++11'])

setup(name='pdfcracker',
      version='1.0',
      description='High performance PDF password cracker',
      ext_modules=[module]) 