from transformers import pipeline


classifier = pipeline("text-classification", model="Pulk17/Fake-News-Detection")




def is_potential_fake(text):
    result = classifier(text)[0]  
    return {
        "label": result["label"],   
        "score": result["score"]    
    }
