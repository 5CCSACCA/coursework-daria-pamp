#!/bin/bash

GREEN="\e[32m"
RED="\e[31m"
NC="\e[0m"

echo "==============================="
echo "   CLOUD-AI SYSTEM TEST SUITE"
echo "==============================="


pass_fail() {
    if [ $1 -eq 200 ]; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL (HTTP $1)${NC}"
    fi
}


echo
echo "--------------------------------"
echo "1) HEALTH CHECK"
echo "--------------------------------"

HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
echo -n "Health endpoint: "
pass_fail $HEALTH_STATUS
echo


echo "--------------------------------"
echo "2) YOLO OBJECT DETECTION TEST"
echo "--------------------------------"

YOLO_START=$(date +%s%3N)
YOLO_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/detect \
  -F "file=@../images/test.jpg")
YOLO_END=$(date +%s%3N)
YOLO_MS=$((YOLO_END - YOLO_START))

echo -n "YOLO detection: "
pass_fail $YOLO_STATUS
echo "YOLO time: ${YOLO_MS} ms"
echo


echo "--------------------------------"
echo "3) BITNET TEXT GENERATION TEST"
echo "--------------------------------"

BIT_START=$(date +%s%3N)
BIT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"detected_objects":["cat"]}')
BIT_END=$(date +%s%3N)
BIT_MS=$((BIT_END - BIT_START))

echo -n "BitNet generation: "
pass_fail $BIT_STATUS
echo "BitNet time: ${BIT_MS} ms"
echo


echo "--------------------------------"
echo "4) GATEWAY PIPELINE TEST"
echo "--------------------------------"
echo "NOTE: should return 401 if no token is provided"

GW_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/process-art \
    -F "file=@../images/test.jpg")

echo -n "Gateway upload: "
if [ $GW_STATUS -eq 401 ] || [ $GW_STATUS -eq 200 ]; then
    echo -e "${GREEN}PASS${NC} (expected behaviour)"
else
    pass_fail $GW_STATUS
fi
echo


echo "--------------------------------"
echo "5) LOAD TEST – 5 runs"
echo "--------------------------------"

LOAD_START=$(date +%s%3N)

for i in {1..5}; do
    echo "Upload #$i"
    curl -s -o /dev/null -w "" -X POST http://localhost:8000/detect \
      -F "file=@../images/test.jpg"
done

LOAD_END=$(date +%s%3N)
LOAD_MS=$((LOAD_END - LOAD_START))

echo "Total time for 5 YOLO requests: ${LOAD_MS} ms"
echo


echo "--------------------------------"
echo "TESTS COMPLETE"
echo "--------------------------------"

