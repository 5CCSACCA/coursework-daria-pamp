import json
import os
import time
import pika

from deepsymbol.firebase_store import update_output


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE", "postprocess")


def simple_postprocess(objects: list[str], interpretation: str) -> dict:
    # Very lightweight "post-processing" (no extra LLM, no heavy compute)
    # Enough to demonstrate the pipeline.
    keywords = objects[:]
    summary = interpretation.strip().split(".")[0].strip()
    if summary and not summary.endswith("."):
        summary += "."
    return {"post_summary": summary, "keywords": keywords, "processed_at": time.time()}


def main():
    while True:
        try:
            params = pika.ConnectionParameters(host=RABBITMQ_HOST)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            def callback(ch, method, properties, body):
                msg = json.loads(body.decode("utf-8"))
                record_id = str(msg["id"])
                objects = msg.get("objects", [])
                interpretation = msg.get("interpretation", "")

                patch = simple_postprocess(objects, interpretation)
                update_output(record_id, patch)

                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
            print("[postprocess] waiting for messages...")
            channel.start_consuming()

        except Exception as e:
            print(f"[postprocess] error: {e} — retrying in 3s")
            time.sleep(3)


if __name__ == "__main__":
    main()

