from deepsymbol.llm import generate_text


def main():
    prompt = (
        "You are an AI oracle that interprets psychological symbols.\n"
        "Explain what it might mean if someone sees an apple and a mirror in a dream."
    )

    result = generate_text(prompt)

    print("PROMPT:")
    print(result["prompt"])
    print("\nBITNET OUTPUT:")
    print(result["output_text"])


if __name__ == "__main__":
    main()

