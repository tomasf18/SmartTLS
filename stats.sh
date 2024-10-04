#!/bin/bash

# Assert the number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <model_path> <traffic_scale>"
    exit 1
fi

model_path=$1
traffic_scale=$2

echo "[0/6] - Starting simulation"

## Smart traffic lights
python3 test.py --load_model=$model_path --simulation="aveiro_traffic/osm" --traffic_scale="$traffic_scale" --render_mode="None" > /dev/null
mv data/emissions.xml data/emissions-SmartTLS.xml
mv data/waitingTime.xml data/waitingTime-SmartTLS.xml
mv data/publicTransport.xml data/publicTransport-SmartTLS.xml

echo "[1/6] - SmartTLS traffic lights simulation finished"

## Normal traffic lights
sumo -c sumo_config/aveiro_traffic/osm.sumocfg --tripinfo-output.write-unfinished="true" --duration-log.statistics="true" --device.emissions.probability="0.10" --no-step-log="true" --no-warnings="true" --end="2250" --scale="$traffic_scale" --start="true" >> /dev/null
mv data/emissions.xml data/emissions-Tradicional.xml
mv data/waitingTime.xml data/waitingTime-Tradicional.xml
mv data/publicTransport.xml data/publicTransport-Tradicional.xml

echo "[2/6] - Tradicional traffic lights simulation finished"

## Actuated traffic lights
sumo -c sumo_config/aveiro_traffic/osm.actuated.sumocfg --tripinfo-output.write-unfinished="true" --duration-log.statistics="true" --device.emissions.probability="0.10" --no-step-log="true" --no-warnings="true" --end="2250" --scale="$traffic_scale" --start="true" > /dev/null
mv data/emissions.xml data/emissions-Alemanha.xml
mv data/waitingTime.xml data/waitingTime-Alemanha.xml
mv data/publicTransport.xml data/publicTransport-Alemanha.xml

echo "[3/6] - Alemenha traffic lights simulation finished"

## Get the simulation results
python3 $SUMO_HOME/tools/visualization/plotXMLAttributes.py -x begin -y CO2_abs -i @NONE data/emissions-SmartTLS.xml data/emissions-Tradicional.xml data/emissions-Alemanha.xml -o data/emissions.png --ylabel="Emissões de CO2 (mg)" --xlabel="Instante (s)" --title="Emissões de CO2 nos Semáforos de Aveiro" --legend --barplot --xbin=60
echo "[4/6] - CO2 Emission plot generated"
python3 $SUMO_HOME/tools/visualization/plotXMLAttributes.py -x begin -y waitingTime -i @NONE data/waitingTime-SmartTLS.xml data/waitingTime-Tradicional.xml data/waitingTime-Alemanha.xml -o data/waitingTime.png --ylabel="Tempo de Espera (s)" --xlabel="Instante (s)" --title="Tempo de Espera dos Restantes Veículos nos Semáforos de Aveiro" --legend --barplot --xbin=60
echo "[5/6] - Waiting Time plot generated"
python3 $SUMO_HOME/tools/visualization/plotXMLAttributes.py -x begin -y waitingTime -i @NONE data/publicTransport-SmartTLS.xml data/publicTransport-Tradicional.xml data/publicTransport-Alemanha.xml -o data/publicTransport.png --ylabel="Tempo de Espera (s)" --xlabel="Instante (s)" --title="Tempo de Espera dos Transportes Públicos nos Semáforos de Aveiro" --legend --barplot --xbin=60
echo "[6/6] - Public Transport Waiting Time plot generated"


## Table output with means
echo "----------------------------------------"
echo "--- Average CO2_abs ---"
echo "----------------------------------------"

xml_file="data/emissions-SmartTLS.xml"
average_1=$(xmllint --xpath "//edge/@CO2_abs" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "SmartTLS traffic lights: $average_1"

xml_file="data/emissions-Tradicional.xml"
average_2=$(xmllint --xpath "//edge/@CO2_abs" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "Tradicional traffic lights: $average_2"

xml_file="data/emissions-Alemanha.xml"
average_3=$(xmllint --xpath "//edge/@CO2_abs" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "Alemanha traffic lights: $average_3"

## Gain calculation
echo "$average_1 $average_2 $average_3"
gain_Traditional=$(echo "scale=2; ($average_2-$average_1)/$average_1*100" | bc)
gain_Alemanha=$(echo "scale=2; ($average_3-$average_1)/$average_1*100" | bc)
echo "Gains: Tradicional: $gain_Traditional / vs Alemanha: $gain_Alemanha"


echo "----------------------------------------"
echo "--- Average waitingTime ---"
echo "----------------------------------------"

xml_file="data/waitingTime-SmartTLS.xml"
average_1=$(xmllint --xpath "//edge/@waitingTime" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "SmartTLS traffic lights: $average_1"

xml_file="data/waitingTime-Tradicional.xml"
average_2=$(xmllint --xpath "//edge/@waitingTime" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "Tradicional traffic lights: $average_2"

xml_file="data/waitingTime-Alemanha.xml"
average_3=$(xmllint --xpath "//edge/@waitingTime" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "Alemanha traffic lights: $average_3"


## Gain calculation
gain_Traditional=$(echo "scale=2; ($average_2-$average_1)/$average_1*100" | bc)
gain_Alemanha=$(echo "scale=2; ($average_3-$average_1)/$average_1*100" | bc)
echo "Gains: Tradicional: $gain_Traditional / vs Alemanha: $gain_Alemanha"


echo "----------------------------------------"
echo "--- Average publicTransport waitingTime ---"
echo "----------------------------------------"

xml_file="data/publicTransport-SmartTLS.xml"
average_1=$(xmllint --xpath "//edge/@waitingTime" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "SmartTLS traffic lights: $average_1"

xml_file="data/publicTransport-Tradicional.xml"
average_2=$(xmllint --xpath "//edge/@waitingTime" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "Tradicional traffic lights: $average_2"

xml_file="data/publicTransport-Alemanha.xml"
average_3=$(xmllint --xpath "//edge/@waitingTime" "$xml_file" | 
          grep -o '[0-9.]\+' | 
          awk '{sum+=$1; count+=1} END {if (count>0) print sum/count; else print "No data"}')
echo "Alemanha traffic lights: $average_3"

## Gain calculation
gain_Traditional=$(echo "scale=2; ($average_2-$average_1)/$average_1*100" | bc)
gain_Alemanha=$(echo "scale=2; ($average_3-$average_1)/$average_1*100" | bc)
echo "Gains: Tradicional: $gain_Traditional / vs Alemanha: $gain_Alemanha"

echo "----------------------------------------"


