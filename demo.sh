
# Usage: ./demo.sh fan|temp|psu|vm|reset
case "$1" in
  fan)   curl -s -XPOST localhost:8001/sim/fan_fail ;;
  temp)  curl -s -XPOST localhost:8001/sim/temp_spike ;;
  psu)   curl -s -XPOST localhost:8001/sim/psu_fail; curl -s -XPOST localhost:8002/sim/psu_red ;;
  vm)    curl -s -XPOST localhost:8002/sim/start_vm ;;
  reset) curl -s -XPOST localhost:8001/sim/reset; curl -s -XPOST localhost:8002/sim/reset ;;
  *) echo "usage: $0 fan|temp|psu|vm|reset"; exit 1 ;;
esac
echo
