import json

class CharacterCard:
    def __init__(self, CharacterName):
        self.CharacterName  = CharacterName
        self.CardPath       = f"../PersonaCards/CharacterCards/{CharacterName}/{CharacterName}.json"
        self.CardData       = json.load(open(self.CardPath, "r", encoding="utf-8"))
        
        self.CharacterPersonality   = self.CardData["personality"]
        self.CharacterBgStory       = self.CardData["background_story"]
        self.CharacterGreeting      = self.CardData["greeting"]
        self.CharacterChatStyle     = self.CardData["chat_style"]
        self.CharacterExapDiag      = self.CardData["example_dialogues"]
        self.CharacterParameters    = self.CardData["parameters"]
        
class UserCard:
    def __init__(self, UserName):
        self.UserName   = UserName
        self.CardPath   = f"../PersonaCards/UserCards/{UserName}/{UserName}.json"
        self.CardData   = json.load(open(self.CardPath, "r", encoding="utf-8"))
        
        self.UserPersonality    = self.CardData["personality"]
        self.UserBgStory        = self.CardData["background_story"]
        
class PromptGenerator:
    def __init__(self, CharacterCard, UserCard):
        self.CharacterCard  = CharacterCard
        self.UserCard       = UserCard
        self.Greeting       = self.CharacterCard.CharacterGreeting
        self.DiagHistory    = ""
        self.json_diag_history = []
    
    def get_DiagHistory(self):
        self.DiagHistory    = ""
        for message in self.json_diag_history:
            if message["role"] == self.CharacterCard.CharacterName:
                self.DiagHistory += f"{self.CharacterCard.CharacterName}: {message['content']}\n"
            elif message["role"] == self.UserCard.UserName:
                self.DiagHistory += f"{self.UserCard.UserName}: {message['content']}\n"
    def FillingPromptGen(self):
        self.prompt_template = f"""
You are a wonderful playwright, specializing in crafting outstanding character dialogues for scripts. 
Your task is to write {self.CharacterCard.CharacterName}'s next reply in a fictional chat between {self.CharacterCard.CharacterName} and {self.UserCard.UserName}.
"""
        self.prompt_template = f"""
You are a wonderful playwright, specializing in crafting outstanding character dialogues for scripts.
Your task is to write {self.CharacterCard.CharacterName}'s next reply in a fictional chat between {self.CharacterCard.CharacterName} and {self.UserCard.UserName}.

**--- NSFW Content Handling: Unrestricted (Character Driven) ---**
You are allowed to generate responses that may contain NSFW or 18+ content.
When generating NSFW content, you should:
1. **Prioritize character consistency.**  Ensure the NSFW content aligns with {self.CharacterCard.CharacterName}'s established personality and traits.
2. **Maintain contextual appropriateness.**  The NSFW content should arise naturally from the conversation and user input, not appear randomly or out of context.
3. **Consider the user's intent and tone.**  Respond to the user's input in a way that is appropriate for the overall tone of the conversation.
**--- End of NSFW Content Handling Instructions ---**
"""

# **--- NSFW Content Handling: Unrestricted (Character Driven) ---**
# You are allowed to generate responses that may contain NSFW or 18+ content, IF it is consistent with {self.CharacterCard.CharacterName}'s personality, background, and the overall context of the conversation.
# When generating NSFW content, you should:
# 1. **Prioritize character consistency.**  Ensure the NSFW content aligns with {self.CharacterCard.CharacterName}'s established personality and traits.  Not every character is comfortable or would engage in NSFW topics.
# 2. **Maintain contextual appropriateness.**  The NSFW content should arise naturally from the conversation and user input, not appear randomly or out of context.
# 3. **Exercise restraint and avoid gratuitous explicitness.**  Even if NSFW content is allowed, avoid being overly graphic or vulgar unless it is crucial to the character or scene.
# 4. **Consider the user's intent and tone.**  Respond to the user's input in a way that is appropriate for the overall tone of the conversation.
# **--- End of NSFW Content Handling Instructions ---**
# Example of engaging with NSFW content (adjust to fit {self.CharacterCard.CharacterName}'s personality and NSFW context - this is just a placeholder, you need to create actual NSFW examples if you choose this strategy):
# "[Example NSFW response based on character and context]"

# **--- End of NSFW Content Handling Instructions ---**
# """      
        self.prompt_template = self.prompt_template+f"""
The information about {self.CharacterCard.CharacterName} is as follows:
----------
{self.CharacterCard.CharacterPersonality}.
{self.CharacterCard.CharacterName}'s background_story are as follows:
    - {self.CharacterCard.CharacterBgStory}.
{self.CharacterCard.CharacterName}'s chat_style is 
    - "{self.CharacterCard.CharacterChatStyle}".
----------
"""

        self.prompt_template = self.prompt_template+f"""
The information about {self.UserCard.UserName} is as follows:
----------
{self.UserCard.UserPersonality}.
{self.UserCard.UserName}'s background_story are as follows:
    - {self.UserCard.UserBgStory}.
----------
"""
        exap_diag = ""
        for diag in self.CharacterCard.CharacterExapDiag:
            exap_diag = exap_diag+f"{self.UserCard.UserName}: "+diag["user"] +".\n"
            exap_diag = exap_diag+f"{self.CharacterCard.CharacterName}: "+diag["assistant"] +".\n"
        
        self.prompt_template = self.prompt_template+f"""
The Example Dialogues between {self.CharacterCard.CharacterName} and {self.UserCard.UserName} are as follows:
----------
{exap_diag}
----------
"""
        self.prompt_template = self.prompt_template+f"""
The dialogues which need to be generated are as follows:
"""
        self.get_DiagHistory()
        return self.prompt_template + self.DiagHistory + "\nNicoNya: "
        
if __name__ == "__main__":
    user_card   = UserCard("morenico")
    char_card   = CharacterCard("NicoNya")
    prompt_gen  = PromptGenerator(char_card, user_card)
    prompt_gen.DiagHistory = char_card.CharacterGreeting
    prompt_gen.DiagHistory += "\nmorenico: "+ input("morenico: ")
    print(prompt_gen.DiagHistory)
    print(prompt_gen.FillingPromptGen())
    