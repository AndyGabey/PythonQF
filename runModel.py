# Wrapper that kicks off the model run and can translate outputs to polygons from shapefile template
import Calcs3
import os
import string
import numpy as np
import pandas as pd
from AllParts import getQFComponents
from Config import Config
from Params import Params

if __name__ == "__main__":
    config = Config()
    config.loadFromNamelist('V32_Input.nml') # Model config
    params = Params('parameters.nml') # Model params (not the same as input data)
    outs = Calcs3.mostcalcs(config, params)
    print outs

