import sys
from deepsymbol.vision import detect_objects


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_vision_example.py <image_path>")
        raise SystemExit(1)

    image_path = sys.argv[1]
    result = detect_objects(image_path)

    print("Detected objects:", result["objects"])
    print("Confidences:", result["confidences"])
    print("Total objects:", result["num_objects"])


if __name__ == "__main__":
    main()

