import xml.etree.ElementTree as ET
import random
import time

def generate_route_file(filename):
    # random.seed(42)  # make tests reproducible
    N = 1000  # number of time steps
    # demand per second from different directions
    pWE = 1. / 7
    pEW = 1. / 8
    pNS = 1. / 9
    pSN = 1. / 10
    
    pBus = 1. / 250
    
    with open(filename, "w") as routes:
        print("""<routes>
        <vType id="car" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" \
guiShape="passenger"/>
        <vType id="bus" accel="0.8" decel="4.5" sigma="0.5" length="7" minGap="3" maxSpeed="25" guiShape="bus"/>

        <route id="right" edges="-EE -EW" />
        <route id="left" edges="EW EE" />
        <route id="down" edges="-EN -ES" />
        <route id="up" edges="ES EN" />""", file=routes)
        vehNr = 0
        for i in range(N):
            if random.uniform(0, 1) < pWE:
                vehicle_type = "bus" if random.uniform(0, 1) < pBus else "car"
                print('    <vehicle id="right_%i" type="%s" route="right" depart="%i" />' % (
                    vehNr, vehicle_type, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pEW:
                vehicle_type = "bus" if random.uniform(0, 1) < pBus else "car"
                print('    <vehicle id="left_%i" type="%s" route="left" depart="%i" />' % (
                    vehNr, vehicle_type, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pNS:
                vehicle_type = "bus" if random.uniform(0, 1) < pBus else "car"
                print('    <vehicle id="down_%i" type="%s" route="down" depart="%i"/>' % (
                    vehNr, vehicle_type, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pSN:
                vehicle_type = "bus" if random.uniform(0, 1) < pBus else "car"
                print('    <vehicle id="up_%i" type="%s" route="up" depart="%i"/>' % (
                    vehNr, vehicle_type, i), file=routes)
                vehNr += 1
        print("</routes>", file=routes)





