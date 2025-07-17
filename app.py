
from parser.whatsapp_parser import parse_whatsapp_chat
from model.claim_detector import is_potential_fake
from api.fact_check_api import search_fact_check

def process_file(file_path):
    messages = parse_whatsapp_chat(file_path)
    for msg in messages:
        label, score = is_potential_fake(msg)
        print(f"Message: {msg}\nVerdict: {label} (Confidence: {score:.2f})")
        claims = search_fact_check(msg)
        if claims:
            print("Sources:")
            for c in claims[:2]:
                print(f"- {c['claimReview'][0]['publisher']['name']}: {c['claimReview'][0]['textualRating']}")
                print(f"  {c['claimReview'][0]['url']}")
        print("-"*60)

if __name__ == '__main__':
    process_file('sample_chat.txt')  
