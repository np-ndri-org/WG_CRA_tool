# WG_CRA_tool
Weather Generator and Climate Change Scenario Generator for Climate Risk Assessment
# Requirements for WECCS-Gen tools
Linux Operating system - ubuntu  
# miniconda 
Install minicondo (https://docs.conda.io/projects/miniconda/en/latest)
   # 
   $ mkdir -p ~/miniconda3
   # 
   $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
   # 
   $ bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
   # 
   $ rm -rf ~/miniconda3/miniconda.sh
   # initialize if bash shell
   $ ~/miniconda3/bin/conda init bash
   # initialize if zsh shell
   $ ~/miniconda3/bin/conda init zsh
#
$ conda create -c conda-forge -n spyder-env "python>=3.11,<3.12" spyder numpy scipy pandas matplotlib sympy cython
