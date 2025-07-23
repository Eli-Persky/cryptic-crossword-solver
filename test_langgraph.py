from config import Config
from app.langgraph_solver import CrypticCrosswordSolver

def parse_given_letters(s):
    """Parse a string like '1:A,3:E' into a dict {1: 'A', 3: 'E'}"""
    result = {}
    for item in s.split(','):
        if ':' in item:
            pos, letter = item.split(':', 1)
            if pos.strip().isdigit() and letter.strip():
                result[int(pos.strip())] = letter.strip().upper()
    return result

def main():
    openai_key = Config.OPENAI_API_KEY

    solver = CrypticCrosswordSolver(openai_key)
    
    if save_image:
        solver.save_graph()
        return
    
    clue = input("Enter cryptic crossword clue: ").strip()
    length = input("Enter solution length (optional): ").strip()
    given = input("Enter given letters (e.g. 1:A,3:E) (optional): ").strip()
    target_length = int(length) if length.isdigit() else None
    given_letters = parse_given_letters(given) if given else {}
    
    print("\nSolving...")
    result = solver.solve(clue, target_length=target_length, given_letters=given_letters)
    
    print("\n--- LangGraph Solution ---")
    print("Clue:", clue)
    if target_length:
        print("Expected length:", target_length)
    if given_letters:
        print("Given letters:", given_letters)
    print("\nStructured Output:")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    save_image = True
    main()
