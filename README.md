# WG_CRA_tool
Weather Generator and Climate Change Scenario Generator for Climate Risk Assessment
### Requirements for WECCS-Gen tools
Linux Operating system - ubuntu  
### miniconda 
1. Install minicondo (https://docs.conda.io/projects/miniconda/en/latest)
   ### 
   $ mkdir -p ~/miniconda3
   ### 
   $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
   ### 
   $ bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
   ### 
   $ rm -rf ~/miniconda3/miniconda.sh
   ### 
   $ ~/miniconda3/bin/conda init bash
   ### 
   $ ~/miniconda3/bin/conda init zsh
### create new environment and install Spyder (IDE), python version less than 3.12 is required 
$ conda create -c conda-forge -n spyder-env "python>=3.11,<3.12" spyder numpy scipy pandas matplotlib sympy cython
###
2.Install Spyder ( https://docs.spyder-ide.org/current/installation.html)
###
$ conda activate spyder-env
### 
$ conda install -c conda-forge statsmodels 
### 
3.Install xesmf
###
$ conda install -c conda-forge esmpy xarray numpy shapely cf_xarray sparse numba
### 
###
$ conda install -c conda-forge dask netCDF4
###
$ conda install -c conda-forge matplotlib cartopy jupyterlab
###
$ conda install -c conda-forge xesmf
###
4.Install CDO (python version)
###
$ conda install conda-forge::python-cdo
###
5.Install xrft


