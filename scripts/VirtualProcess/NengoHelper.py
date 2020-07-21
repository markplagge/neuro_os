import nengo
import nengo_spa as spa
from nengo_spa import Vocabulary
from nengo.dists import Choice
from nengo.utils.ensemble import response_curves, tuning_curves
import random
import numpy as np
import tensorflow as tf

try:
    import nengo_dl
    NENGO_DL = True
except:
    NENGO_DL = False

if NENGO_DL:
    Simulator = nengo_dl.Simulator
else:
    Simulator = nengo.Simulator
