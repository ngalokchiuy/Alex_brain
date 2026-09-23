from google import genai

# Initialize the client (uses your GEMINI_API_KEY environment variable)
client = genai.Client()

print("Searching for available Pro models...\n")

# client.models.list() returns all models available to your API key
pro_models = []
all_models = []

for model in client.models.list():
    all_models.append(model.name)
    if "pro" in model.name.lower():
        pro_models.append(model.name)

if pro_models:
    print("✅ Available 'Pro' Models:")
    for pm in pro_models:
        print(f"   - {pm}")
else:
    print("❌ No 'Pro' models found. Here is the full list of what is available:")
    for am in all_models:
         print(f"   - {am}")