#!/bin/bash

echo "==============================="
echo "   CLOUD-AI SYSTEM TEST SUITE  "
echo "==============================="

GATEWAY="http://localhost:8080"
YOLO="http://localhost:8000"
BITNET="http://localhost:8001"

TEST_IMAGE="test.jpg"   # положи любой маленький JPEG рядом со скриптом

echo ""
echo "--------------------------------"
echo "1) HEALTH CHECKS"
echo "--------------------------------"

curl -s $GATEWAY/health
echo ""
curl -s $YOLO/health
echo ""
curl -s $BITNET/health
echo ""

echo ""
echo "--------------------------------"
echo "2) YOLO OBJECT DETECTION TEST"
echo "--------------------------------"

time curl -s -X POST \
    -F "file=@$TEST_IMAGE" \
    $YOLO/detect

echo ""
echo "--------------------------------"
echo "3) BITNET TEXT GENERATION TEST"
echo "--------------------------------"

JSON_PAYLOAD='{ "detected_objects": ["cat", "flower"] }'

time curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD" \
    $BITNET/generate

echo ""
echo "--------------------------------"
echo "4) GATEWAY ASYNC PIPELINE TEST"
echo "--------------------------------"

echo "NOTE: This will fail without Firebase token, but shows endpoint works."

time curl -s -X POST \
    -F "file=@$TEST_IMAGE" \
    $GATEWAY/process-art

echo ""
echo "--------------------------------"
echo "5) LOAD TEST — 5 images"
echo "--------------------------------"

START=$(date +%s)

for i in {1..5}
do
    echo "Upload #$i"
    curl -s -X POST -F "file=@$TEST_IMAGE" $YOLO/detect > /dev/null
done

END=$(date +%s)
ELAPSED=$((END - START))

echo "Total time for 5 runs: $ELAPSED seconds"

echo ""
echo "--------------------------------"
echo "TESTS COMPLETE"
echo "--------------------------------"
