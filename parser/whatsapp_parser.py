
def parse_whatsapp_chat(file_path):
    messages = []
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            if '-' in line and ':' in line:
                try:
                    message = line.split('-', 1)[1].split(':', 1)[1].strip()
                    messages.append(message)
                except IndexError:
                    continue
    return messages
