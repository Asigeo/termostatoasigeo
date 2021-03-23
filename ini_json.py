import json
import numpy as np

#scheduler = np.zeros((2,7,24))
#np.save("json_f/scheduler.npy",scheduler)
#print(scheduler)
#with open("json_f/scheduler.json", "w") as f:
#    json.dump(scheduler, f,indent=4)
estado_sondas = [{"b1":"normal",
                "b2":"down"} for col in range(8)]
estado_curvas = [{"b1":"down",
                "b2":"normal","b3":"normal"} for col in range(2)]
estado_bombas = [{"b1":"down",
                "b2":"normal"} for col in range(2)]

with open("json_f/estado_bombas.json", "w") as f:
    json.dump(estado_bombas, f,indent=4)
